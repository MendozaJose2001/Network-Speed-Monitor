# utils/exceptions.py

class SpeedTestExecutionError(Exception):
    """
    Raised when the speed test CLI fails to execute.
    Wraps RuntimeError from SubProcessManager.
    """
    pass


class ServerResolutionError(Exception):
    """
    Raised when the server used in the test cannot be identified.
    """
    pass


class NormalizationError(Exception):
    """
    Raised when raw test results cannot be normalized to SpeedRecord.
    """
    pass