from entity.setup.vllm_installer import VLLMInstaller


def test_auto_install_enabled(monkeypatch):
    calls = []

    monkeypatch.setenv("ENTITY_AUTO_INSTALL_VLLM", "true")
    monkeypatch.setattr(VLLMInstaller, "_vllm_installed", lambda: False)
    monkeypatch.setattr(VLLMInstaller, "_detect_backend", lambda: "cpu")
    monkeypatch.setattr(
        VLLMInstaller, "_install_vllm", lambda backend: calls.append(backend)
    )
    monkeypatch.setattr(
        VLLMInstaller, "_download_model", lambda model: calls.append(model)
    )

    VLLMInstaller.ensure_vllm_available("test/model")

    assert calls == ["cpu", "test/model"]


def test_auto_install_disabled(monkeypatch):
    called = False

    def fake_install(_):
        nonlocal called
        called = True

    monkeypatch.setenv("ENTITY_AUTO_INSTALL_VLLM", "false")
    monkeypatch.setattr(VLLMInstaller, "_install_vllm", fake_install)
    monkeypatch.setattr(VLLMInstaller, "_download_model", fake_install)

    VLLMInstaller.ensure_vllm_available("test/model")

    assert not called
