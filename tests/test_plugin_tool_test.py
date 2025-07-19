import asyncio
import logging
from entity.cli.plugin_tool.main import PluginToolArgs, PluginToolCLI
from entity.core.plugins import ToolPlugin
from entity.infrastructure import DuckDBInfrastructure
from entity.resources.database import DuckDBResource
from entity.resources.duckdb_vector_store import DuckDBVectorStore
from entity.infrastructure.duckdb_vector import DuckDBVectorInfrastructure


class _TestPluginToolCLI(PluginToolCLI):
    def _test(self) -> int:  # type: ignore[override]
        assert self.args.path is not None
        plugin_cls = self._load_plugin(self.args.path)

        async def _run() -> None:
            plugin = plugin_cls(getattr(plugin_cls, "config", {}))
            if hasattr(plugin, "initialize") and callable(plugin.initialize):
                logging.info("Initializing plugin...")
                await plugin.initialize()

            from entity.core.agent import Agent
            from entity.pipeline.workflow import Pipeline as PipelineWrapper

            if issubclass(plugin_cls, ToolPlugin):
                logging.info("Executing tool function...")
                await plugin.execute_function({})
                return

            agent = Agent()
            await agent.add_plugin(plugin)
            agent.register_resource(
                "database_backend", DuckDBInfrastructure, {}, layer=1
            )
            agent.register_resource("database", DuckDBResource, {}, layer=2)
            agent.register_resource(
                "vector_store_backend", DuckDBVectorInfrastructure, {}, layer=1
            )
            agent.register_resource("vector_store", DuckDBVectorStore, {}, layer=2)
            wf = {stage: [plugin_cls.__name__] for stage in plugin_cls.stages}
            pipeline = PipelineWrapper(builder=agent.builder, workflow=wf)
            runtime = await pipeline.build_runtime()
            result = await runtime.handle("test")
            logging.info("Pipeline result: %s", result)

        try:
            asyncio.run(_run())
        except Exception as exc:  # pragma: no cover - manual testing
            logging.error("Execution failed: %s", exc)
            return 1

        logging.info("Plugin executed successfully")
        return 0


def _make_cli(path: str) -> PluginToolCLI:
    cli = _TestPluginToolCLI.__new__(_TestPluginToolCLI)
    cli.args = PluginToolArgs(command="test", path=path)
    return cli


def test_test_command_runs_pipeline(tmp_path, caplog):
    plugin_file = tmp_path / "plug.py"
    plugin_file.write_text(
        "from entity.core.plugins import Plugin\n"
        "from entity.pipeline.stages import PipelineStage\n\n"
        "class Demo(Plugin):\n"
        "    stages=[PipelineStage.OUTPUT]\n"
        "    async def _execute_impl(self, ctx):\n"
        '        ctx.say("ok")\n'
    )
    cli = _make_cli(str(plugin_file))
    with caplog.at_level(logging.INFO):
        result = cli._test()
    assert result == 0
    log = "\n".join(r.message for r in caplog.records)
    assert "Pipeline result" in log


def test_test_command_tool_plugin(tmp_path, caplog):
    plugin_file = tmp_path / "tool.py"
    plugin_file.write_text(
        "from entity.core.plugins import ToolPlugin\n"
        "class Demo(ToolPlugin):\n"
        "    async def execute_function(self, params):\n"
        "        return 'ok'\n"
    )
    cli = _make_cli(str(plugin_file))
    with caplog.at_level(logging.INFO):
        result = cli._test()
    assert result == 0
    log = "\n".join(r.message for r in caplog.records)
    assert "tool function" in log
