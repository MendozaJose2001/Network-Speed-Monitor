# models/speed_entities.py

from dataclasses import dataclass

@dataclass(frozen=True)
class SpeedRecord:
    timestamp: str
    download_mbps: str
    upload_mbps: str
    ping_ms: str
    server_name: str
    

