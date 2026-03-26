# infrastructure/adapters/libre_speed_adapater

import re
from schemas.is_speed_test import LibreSpeedTest, ISpeedTest
from utils.subproccess_manager import SubProcessManager
from typing import List, Dict, Optional, Tuple
from utils.types import ServerData
from abc import ABC, abstractmethod
from utils.exceptions import SpeedTestExecutionError, ServerResolutionError

class TestSpeedAdapter(ABC):
    
    @classmethod
    @abstractmethod
    def run_a_test(cls) -> ISpeedTest:
        pass
    
class LibreSpeedAdapter (TestSpeedAdapter):
    
    _SUBPROCCESS_ARGS_CONFIG : Dict[str, Tuple] = {
        'speed_test_best_server' : ('librespeed-cli', '--json'),
        'speed_test_by_server_id': ('librespeed-cli', '--server', None, '--json'),
        'list_server' : ('librespeed-cli', '--list')
    }
    
    _GET_SERVER_PATTER = r"(\d+):.*?\((https?://.*?)\)"

    @classmethod
    def run_a_test(
        cls, server_id: Optional[int] = None
        ) -> LibreSpeedTest:
        
        if server_id:
            process_args = list(
                cls._SUBPROCCESS_ARGS_CONFIG['speed_test_by_server_id']
                )
            
            process_args[2] = str(server_id)
            process_args = tuple(process_args)
            
        else:
            process_args = cls._SUBPROCCESS_ARGS_CONFIG[
            'speed_test_best_server'
            ]
                    
        process: List[Dict] = SubProcessManager.run_subproccess(process_args)
        
        if not isinstance(process, List):
            raise SpeedTestExecutionError("The test did not return a list")
        
        if not all(isinstance(result, Dict) for result in process):
            raise SpeedTestExecutionError("The test did not return the result JSON")

        return LibreSpeedTest(**process[0])
    
    @classmethod
    def get_servers(cls) -> List[ServerData]:
        result: str = SubProcessManager.run_subproccess(
            cls._SUBPROCCESS_ARGS_CONFIG['list_server']
        )
        
        if not result:
            raise ServerResolutionError("No servers found")
        
        # Explicación del Regex:
        # (\d+)          -> Grupo 1: Captura el ID numérico.
        # :              -> Busca los dos puntos literales.
        # .*?            -> Salta todo el nombre del servidor de forma "perezosa".
        # \(             -> Busca el paréntesis de apertura literal.
        # (https?://.*?) -> Grupo 2: Captura la URL (acepta http o https).
        # \)             -> Busca el paréntesis de cierre literal.

        matches = re.findall(
            cls._GET_SERVER_PATTER, result, re.IGNORECASE
            )
    
        return [{"id": id, "url": url} for id, url in matches]

    @classmethod
    def find_server_id(cls, record_test: LibreSpeedTest):
        
        url_target = record_test.get_server()['url']
        
        if not url_target:
            raise ServerResolutionError("The server's URL must not be NULL")

        server_map = cls.get_servers()
        
        for server_data in server_map:
            
            if server_data['url'] == url_target:
                return int(server_data['id'])
            
        raise ServerResolutionError(f"Could not find server ID for URL: {url_target}")
          


