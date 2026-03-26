# schemas/is_speed_test.py

from typing import Any, Union, ClassVar
from abc import ABC, abstractmethod
from dataclasses import dataclass
from utils.types import StrFloat

class ISpeedTest(ABC):
    @abstractmethod
    def get_server(self) -> dict[str, str]:
        pass
    
    @abstractmethod
    def get_client(self) -> dict[str, str]:
        pass
    
    @classmethod
    @abstractmethod
    def get_up_down_unit(cls) -> float:
        pass
    
    @classmethod
    @abstractmethod
    def get_time_unit(cls) -> float:
        pass
    
@dataclass
class LibreSpeedTest(ISpeedTest):
    
    _UNIT_MBPS: ClassVar[float] = 10**6
    _UNIT_MS: ClassVar[float] = 10**-3
    
    timestamp: str
    server: dict[str, StrFloat]
    client: dict[str, StrFloat]
    bytes_sent: int
    bytes_received: int
    ping: float
    jitter: float
    upload: float
    download: float
    share: str
    
    def get_server(self) -> dict[str, str]:
        return {
            'name': str(self.server.get('name')),
            'url': str(self.server.get('url'))
        }
        
    def get_client(self) -> dict[str, str]:
        return {
            'ip' : str(self.client.get('ip')),
            'hostname' : str(self.client.get('hostname')),
            'timezone' : str(self.client.get('timezone'))
        }
        
    @classmethod
    def get_up_down_unit(cls) -> float:
        return cls._UNIT_MBPS
    
    @classmethod
    def get_time_unit(cls) -> float:
        return cls._UNIT_MS
