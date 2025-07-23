from importlib import import_module

__all__ = ["Workflow", "WorkflowExecutor"]


def __getattr__(name: str):
    if name == "WorkflowExecutor":
        return import_module(".executor", __name__).WorkflowExecutor
    if name == "Workflow":
        return import_module(".workflow", __name__).Workflow
    raise AttributeError(name)
