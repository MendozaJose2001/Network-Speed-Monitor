# utils/time_manager.py

from datetime import datetime, timezone

class TimeManager:
    
    @staticmethod
    def timestamp_now() -> datetime:
        return datetime.now(timezone.utc)
    
    @classmethod
    def get_str_now(cls) -> str:
        now = cls.timestamp_now()
        return now.strftime("%Y-%m-%dT%H-%M-%S") + "Z"
        