# utils/exceptions.py
"""
Custom Exceptions
=================
Defines domain-specific exceptions for the speed test monitoring system.
Centralizing exceptions here keeps error semantics explicit and ensures
that callers can import and handle them from a single, predictable location.

Design
------
Each exception maps to a distinct failure domain within the system,
allowing the service layer (core/speed_test_service.py) to handle each
case independently and meaningfully without relying on generic built-ins
like ValueError or RuntimeError.

Exceptions
----------
SpeedTestExecutionError
    CLI execution failures. Raised by SubProcessManager and
    LibreSpeedAdapter when the underlying process exits with an error.

ServerResolutionError
    Server identification failures. Raised by LibreSpeedAdapter when
    the server used in a test cannot be matched to a known server ID
    or when the server URL is missing.

NormalizationError
    Data normalization failures. Raised by SpeedTestManager when raw
    test output cannot be mapped or converted to a canonical SpeedRecord.

Usage
-----
    from utils.exceptions import (
        SpeedTestExecutionError,
        ServerResolutionError,
        NormalizationError
    )
"""


class SpeedTestExecutionError(Exception):
    """
    Raised when the speed test CLI fails to execute.

    Wraps the stderr output from SubProcessManager when the LibreSpeed
    CLI exits with a non-zero return code.
    """
    pass


class ServerResolutionError(Exception):
    """
    Raised when the server used in the test cannot be identified.

    Covers two cases: the server URL is null or empty, or no matching
    server ID can be found in the available server list.
    """
    pass


class NormalizationError(Exception):
    """
    Raised when raw test results cannot be normalized to SpeedRecord.

    Covers header mapping failures and field-level conversion errors
    during the normalization process in SpeedTestManager.
    """
    pass