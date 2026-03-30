# schemas/is_speed_test.py
"""
Speed Test Schemas
==================
Defines the abstract interface and concrete implementations for raw
speed test results. Each schema represents the data contract of a
specific speed test provider's CLI output.

Design
------
ISpeedTest establishes the interface that all provider schemas must
implement. This allows the normalization layer (SpeedTestManager) and
the service layer (LibreSpeedService) to operate against the interface
rather than any concrete implementation, making it straightforward to
add new providers without modifying existing code.

Each concrete implementation is responsible for declaring its own unit
factors via get_up_down_unit() and get_time_unit(), so the normalization
layer never hardcodes provider-specific scaling logic.

Providers
---------
LibreSpeedTest
    Schema for the LibreSpeed CLI JSON output. Speeds arrive in bytes/s
    and time values in milliseconds.

Adding a New Provider
---------------------
    1. Create a dataclass that inherits from ISpeedTest.
    2. Implement all four abstract methods.
    3. Declare _UNIT_MBPS and _UNIT_MS as ClassVar with the appropriate
       scaling factors for that provider's output format.

Usage
-----
    from schemas.is_speed_test import LibreSpeedTest

    record = LibreSpeedTest(**cli_json_output)
    record.get_server()         # {'name': '...', 'url': '...'}
    record.get_up_down_unit()   # 1000000.0
"""
from typing import ClassVar, Dict
from abc import ABC, abstractmethod
from dataclasses import dataclass
from utils.types import StrFloat


class ISpeedTest(ABC):
    """
    Abstract interface for raw speed test result schemas.

    All concrete provider schemas must inherit from this class and
    implement its four abstract methods. This ensures the normalization
    and service layers remain provider-agnostic.
    """

    @abstractmethod
    def get_server(self) -> dict[str, str]:
        """
        Return a normalized summary of the server used in the test.

        Returns
        -------
        dict[str, str]
            A dictionary containing at least 'name' and 'url' keys.
        """
        pass

    @abstractmethod
    def get_client(self) -> dict[str, str]:
        """
        Return a normalized summary of the client that ran the test.

        Returns
        -------
        dict[str, str]
            A dictionary containing at least 'ip', 'hostname',
            and 'timezone' keys.
        """
        pass

    @classmethod
    @abstractmethod
    def get_up_down_unit(cls) -> float:
        """
        Return the unit factor for upload and download speed fields.

        Used by SpeedTestManager to scale raw speed values to Mbps.

        Returns
        -------
        float
            The unit factor (e.g., 10**6 if speeds are in bytes/s).
        """
        pass

    @classmethod
    @abstractmethod
    def get_time_unit(cls) -> float:
        """
        Return the unit factor for time-based fields (ping, jitter).

        Used by SpeedTestManager to scale raw time values to milliseconds.

        Returns
        -------
        float
            The unit factor (e.g., 10**-3 if times are in milliseconds).
        """
        pass

@dataclass
class SpeedTestGoTest(ISpeedTest):
    
    _UNIT_BYTES_S: ClassVar[float] = 8  # bytes/s → bps
    _UNIT_NS: ClassVar[float] = 10**-9
    
    timestamp: str
    download: float
    upload: float
    jitter: float
    ping: float
    max_latency: float
    min_latency: float
    client: Dict[str, str]
    server: Dict[str, StrFloat]
    test_duration: Dict[str, float]
    packet_loss: Dict[str, float]
    
    def __init__(self, timestamp: str, servers: list, **kwargs) -> None:
        
        server_data: Dict = servers[0]
        
        self.timestamp = timestamp    
        self.client = kwargs['user_info']      
        
        self.download = float(server_data.pop('dl_speed'))
        self.upload = float(server_data.pop('ul_speed'))
        self.jitter = float(server_data.pop('jitter'))
        self.ping = float(server_data.pop('latency'))
        self.max_latency = float(server_data.pop('max_latency'))
        self.min_latency = float(server_data.pop('min_latency'))
        self.test_duration = server_data.pop('test_duration')
        self.packet_loss = server_data.pop('packet_loss')
        
        self.server = server_data
            
    def get_server(self) -> dict[str, str]:

        return {
            'id' : str(self.server.get('id')),
            'name': str(self.server.get('name')),
            'url': str(self.server.get('url')),
            'country' : str(self.server.get('country')),
            'sponsor' : str(self.server.get('sponsor')),
            'host' : str(self.server.get('host'))
        }
        
    def get_client(self) -> dict[str, str]:
        
        return {
            'ip': str(self.client.get('IP')),
            'isp': str(self.client.get('Isp'))
        }
        
    @classmethod
    def get_up_down_unit(cls) -> float:
        
        return cls._UNIT_BYTES_S
    
    @classmethod
    def get_time_unit(cls) -> float:

        return cls._UNIT_NS
        
@dataclass
class LibreSpeedTest(ISpeedTest):
    """
    Raw speed test result schema for the LibreSpeed CLI.

    Maps directly to the JSON object returned by 'librespeed-cli --json'.
    Speed fields (upload, download) are in bytes/s. Time fields (ping,
    jitter) are in milliseconds.

    Attributes
    ----------
    timestamp : str
        ISO 8601 timestamp of when the test was run.
    server : dict[str, StrFloat]
        Server metadata as returned by the CLI (name, url, etc.).
    client : dict[str, StrFloat]
        Client metadata as returned by the CLI (ip, hostname, timezone).
    bytes_sent : int
        Total bytes sent during the upload test.
    bytes_received : int
        Total bytes received during the download test.
    ping : float
        Latency to the test server in milliseconds.
    jitter : float
        Jitter measurement in milliseconds.
    upload : float
        Upload speed in bytes/s.
    download : float
        Download speed in bytes/s.
    share : str
        URL to the shareable result page, if available.
    """

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
        """
        Return a normalized summary of the test server.

        Returns
        -------
        dict[str, str]
            Dictionary with 'name' and 'url' extracted from the
            raw server field.
        """
        return {
            'name': str(self.server.get('name')),
            'url': str(self.server.get('url'))
        }

    def get_client(self) -> dict[str, str]:
        """
        Return a normalized summary of the test client.

        Returns
        -------
        dict[str, str]
            Dictionary with 'ip', 'hostname', and 'timezone' extracted
            from the raw client field.
        """
        return {
            'ip': str(self.client.get('ip')),
            'hostname': str(self.client.get('hostname')),
            'timezone': str(self.client.get('timezone'))
        }

    @classmethod
    def get_up_down_unit(cls) -> float:
        """
        Return the unit factor for upload and download speed fields.

        LibreSpeed CLI reports speeds in bytes/s, so the factor is 10**6
        to scale toward Mbps during normalization.

        Returns
        -------
        float
            1000000.0 (bytes/s unit factor).
        """
        return cls._UNIT_MBPS

    @classmethod
    def get_time_unit(cls) -> float:
        """
        Return the unit factor for time-based fields.

        LibreSpeed CLI reports ping and jitter already in milliseconds,
        so the factor is 10**-3, resulting in no effective scaling during
        normalization (ms / ms = 1.0).

        Returns
        -------
        float
            0.001 (milliseconds unit factor).
        """
        return cls._UNIT_MS