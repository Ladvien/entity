import pytest

from entity.infrastructure.vllm_infra import VLLMInfrastructure


class DummyProcess:
    def __init__(self) -> None:
        self.terminated = False
        self.killed = False

    def poll(self):  # pragma: no cover - simple stub
        return None

    def terminate(self):  # pragma: no cover - simple stub
        self.terminated = True

    def wait(self, timeout: float | None = None):  # pragma: no cover - simple stub
        return 0

    def kill(self):  # pragma: no cover - simple stub
        self.killed = True


@pytest.mark.asyncio
async def test_startup_starts_server(monkeypatch):
    proc = DummyProcess()

    async def fake_start(self):
        self._server_process = proc

    monkeypatch.setattr(VLLMInfrastructure, "_start_vllm_server", fake_start)
    infra = VLLMInfrastructure(model="m", auto_detect_model=False)

    await infra.startup()

    assert infra._server_process is proc


def test_detect_optimal_model(monkeypatch):
    infra = VLLMInfrastructure(model="m", auto_detect_model=False)
    monkeypatch.setattr(infra, "_detect_hardware_tier", lambda: "cpu_only")
    assert (
        infra._detect_optimal_model()
        == VLLMInfrastructure.MODEL_SELECTION_MATRIX["cpu_only"]["models"][0]
    )


@pytest.mark.asyncio
async def test_shutdown_terminates(monkeypatch):
    proc = DummyProcess()
    infra = VLLMInfrastructure(model="m", auto_detect_model=False)
    infra._server_process = proc
    await infra.shutdown()
    assert proc.terminated


def test_health_check(monkeypatch):
    class Resp:
        status_code = 200

    infra = VLLMInfrastructure(model="m", auto_detect_model=False)
    monkeypatch.setattr(
        "entity.infrastructure.vllm_infra.httpx.get", lambda *a, **k: Resp()
    )
    infra._server_process = DummyProcess()
    assert infra.health_check()
