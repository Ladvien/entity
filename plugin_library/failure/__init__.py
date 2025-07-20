def __getattr__(name: str):
    if name == "BasicLogger":
        from .basic_logger import BasicLogger

        return BasicLogger
    if name == "ErrorFormatter":
        from .error_formatter import ErrorFormatter

        return ErrorFormatter
    if name == "DefaultResponder":
        from .default_responder import DefaultResponder

        return DefaultResponder
    raise AttributeError(name)


__all__ = ["BasicLogger", "ErrorFormatter", "DefaultResponder"]
