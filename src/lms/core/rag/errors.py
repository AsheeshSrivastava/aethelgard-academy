"""RAG error definitions, matching rag-core."""

class RegisterError(ValueError):
    """A register or licence-rules file that cannot be loaded."""


class TransitionError(ValueError):
    """A status change the register refuses."""


class LoadRefused(ValueError):
    """A record the loader will not read."""


class SkipShareExceeded(RuntimeError):
    """Too many files in a snapshot could not be loaded."""

    def __init__(self, message: str, result=None) -> None:
        super().__init__(message)
        self.result = result


class LoadError(Exception):
    """A reader that refuses a file; the message is the reason code (e.g. 'stub')."""
