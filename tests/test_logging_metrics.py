import json
import shutil
import subprocess
from pathlib import Path

import pytest

from entity.workflow import Workflow, WorkflowExecutor
from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure


class LogPlugin(Plugin):
    stage = WorkflowExecutor.THINK

    async def _execute_impl(self, context: PluginContext) -> str:
        return context.message or ""


class OutputPlugin(Plugin):
    stage = WorkflowExecutor.OUTPUT

    async def _execute_impl(self, context: PluginContext) -> str:
        context.say("done")
        return "done"


@pytest.mark.asyncio
async def test_logging_and_metrics_per_stage():
    wf = Workflow(
        steps={
            WorkflowExecutor.THINK: [LogPlugin],
            WorkflowExecutor.OUTPUT: [OutputPlugin],
        }
    )
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    executor = WorkflowExecutor({"memory": memory}, wf.steps)
    result = await executor.run("hi")

    assert result == "done"

    logs = executor.resources["logging"].records
    metrics = executor.resources["metrics_collector"].records

    assert [r["fields"]["stage"] for r in logs] == [
        WorkflowExecutor.THINK,
        WorkflowExecutor.THINK,
        WorkflowExecutor.OUTPUT,
        WorkflowExecutor.OUTPUT,
    ]
    assert [m["stage"] for m in metrics] == [
        WorkflowExecutor.THINK,
        WorkflowExecutor.OUTPUT,
    ]


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not installed")
def test_docker_logging_metrics(tmp_path):
    script = (
        "import json, asyncio;"
        "from entity.resources.logging import LoggingResource;"
        "from entity.resources.metrics import MetricsCollectorResource;"
        "async def main():\n"
        "    logger = LoggingResource();\n"
        "    metrics = MetricsCollectorResource();\n"
        "    await logger.log('info', 'hello', container='id');\n"
        "    await metrics.record_plugin_execution('p','stage',0.1,True);\n"
        "    print(json.dumps({'logs': logger.records, 'metrics': metrics.records}))\n"
        "asyncio.run(main())"
    )
    result1 = subprocess.check_output(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{Path.cwd()}:/src",
            "python:3.11-slim",
            "python",
            "-c",
            script.replace("id", "one"),
        ],
        text=True,
    )
    result2 = subprocess.check_output(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{Path.cwd()}:/src",
            "python:3.11-slim",
            "python",
            "-c",
            script.replace("id", "two"),
        ],
        text=True,
    )
    data1 = json.loads(result1)
    data2 = json.loads(result2)
    assert len(data1["logs"]) == len(data1["metrics"]) == 1
    assert len(data2["logs"]) == len(data2["metrics"]) == 1
