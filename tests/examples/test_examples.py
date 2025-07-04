from importlib import import_module

from pipeline import SystemRegistries


def test_pipeline_example_setup_registries() -> None:
    mod = import_module("examples.pipelines.pipeline_example")
    regs = mod.setup_registries()
    assert isinstance(regs, SystemRegistries)


def test_example_modules_importable() -> None:
    modules = [
        "examples.advanced_llm",
        "examples.bedrock_deploy",
        "examples.servers.http_server",
        "examples.utilities.plugin_loader",
        "examples.pipelines.memory_composition_pipeline",
        "examples.pipelines.vector_memory_pipeline",
    ]
    for name in modules:
        import_module(name)
