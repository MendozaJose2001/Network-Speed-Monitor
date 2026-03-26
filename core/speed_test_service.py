# core/speed_test_service.py

from infrastructure.adapters.libre_speed_adapter import LibreSpeedAdapter
from schemas.is_speed_test import LibreSpeedTest, ISpeedTest
from utils.normalize_results import SpeedTestManager
from models.speed_entities import SpeedRecord
from infrastructure.repository.csv_repository import TestRepository
from utils.exceptions import SpeedTestExecutionError, ServerResolutionError, NormalizationError
from abc import ABC, abstractmethod
from typing import Optional

class SpeedTestService(ABC):
    
    def __init__(self, repo: TestRepository) -> None:
        self._repo = repo
        self._server_id = None
    
    @abstractmethod
    def _test_network(self) -> Optional[ISpeedTest]:
        pass
     
class LibreSpeedService (SpeedTestService):
        
    def _test_network(self) -> Optional[LibreSpeedTest]:
        
        results = None
        
        try:
            results = LibreSpeedAdapter.run_a_test(
                server_id=self._server_id
                )
                    
            record = SpeedRecord(
                **SpeedTestManager.normalize_record(results)
            )
                
            self._repo.store_record(record)
            
        except SpeedTestExecutionError as e:
            print(f"[ERROR] Test execution failed: {e}")
            
        except NormalizationError as e:
            print(f"[ERROR] Normalization failed: {e}")
            
        except OSError as e:
            print(f"[ERROR] Storage error: {e}")
            
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            
        else:
            return results
        
        
    def monitor_network(self, num_samples: int = 1) -> None:
        
        for i in range(num_samples):
            
            result = self._test_network()
            
            if result is None:
                continue
            
            try:
                self._server_id = LibreSpeedAdapter.find_server_id(result)
            except ServerResolutionError as e:
                print(f"[ERROR] Server resolution failed: {e}")
            
