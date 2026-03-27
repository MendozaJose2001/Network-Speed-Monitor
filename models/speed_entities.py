# models/speed_entities.py
"""
Domain Models
=============
Defines the canonical data models used internally across the system.
These models represent the normalized, provider-agnostic form of a
speed test result, decoupled from any external CLI output format.

Design
------
Models in this layer are the single source of truth for data structure
within the application. Raw provider data (see schemas/is_speed_test.py)
is always normalized into these models before being stored or consumed
by any other layer.

SpeedRecord is defined as a frozen dataclass to enforce immutability —
once a test result is captured and normalized, it must not be modified.

Models
------
SpeedRecord
    The canonical representation of a single speed test measurement.
    All fields are strings to ensure consistent CSV serialization.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SpeedRecord:
    """
    Canonical, immutable representation of a single speed test result.

    All fields are stored as strings to ensure consistent serialization
    across storage backends (e.g., CSV). Numeric precision is preserved
    in the string representation as produced by SpeedTestManager.

    Attributes
    ----------
    timestamp : str
        UTC timestamp of when the test was run, in ISO 8601 format.
    download_mbps : str
        Download speed in Megabits per second, rounded to 4 decimal places.
    upload_mbps : str
        Upload speed in Megabits per second, rounded to 4 decimal places.
    ping_ms : str
        Latency to the test server in milliseconds, rounded to 4 decimal places.
    server_name : str
        Human-readable name of the server used for the test.
    """
    timestamp: str
    download_mbps: str
    upload_mbps: str
    ping_ms: str
    server_name: str