class CancelledError(Exception):
    """Raised when a task is cancelled by the user."""

    pass


class CriticalAbortError(Exception):
    """Raised when a task is aborted because the system entered critical state."""

    pass


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass
