
class IgnorableException(Exception):
    """Dont mind restarting the worker."""
    pass


class ProcessingException(Exception):
    """Recoverable exception, should be reported to the
    ErrorHandler."""
    pass

        