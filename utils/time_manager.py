# utils/time_manager.py
"""
Time Management Utilities
=========================
Provides UTC timestamp generation used across the project for
record timestamping and session file naming.

Design
------
All functionality is encapsulated in the TimeManager class, which is
never instantiated. Its methods operate at the class level, keeping
the interface explicit and readable at the call site:
TimeManager.timestamp_now(), TimeManager.get_str_now().

All timestamps are UTC-aware to ensure consistency regardless of the
host machine's local timezone.

Usage
-----
    from utils.time_manager import TimeManager

    TimeManager.timestamp_now()  # datetime object, UTC-aware
    TimeManager.get_str_now()    # '2024-01-15T10-30-45Z'
"""
from datetime import datetime, timezone


class TimeManager:
    """
    Namespace for UTC timestamp utilities.
    Never instantiate this class. All members are class-level.
    """

    @staticmethod
    def timestamp_now() -> datetime:
        """
        Return the current UTC time as a timezone-aware datetime object.

        Returns
        -------
        datetime
            Current UTC timestamp with timezone info attached.
        """
        return datetime.now(timezone.utc)

    @classmethod
    def get_str_now(cls) -> str:
        """
        Return the current UTC time as a formatted string.

        Uses hyphens instead of colons in the time portion to ensure
        compatibility with file system naming conventions across all
        operating systems.

        Returns
        -------
        str
            UTC timestamp in the format 'YYYY-MM-DDTHH-MM-SSZ'.

        Example
        -------
            >>> TimeManager.get_str_now()
            '2024-01-15T10-30-45Z'
        """
        now = cls.timestamp_now()
        return now.strftime("%Y-%m-%dT%H-%M-%S") + "Z"