# core/speed_test_service.py
"""
Speed Test Service
==================
Orchestrates the full speed test monitoring workflow: executing tests,
normalizing results, persisting records, and resolving server consistency
across multiple samples within a session.

Design
------
SpeedTestService defines the abstract (no more) base for all monitoring services,
accepting a TestRepository at construction time to keep the service
decoupled from any specific storage backend.

LibreSpeedService is the concrete implementation for the LibreSpeed CLI.
Its responsibilities are split across two methods:

_test_network()
    Executes a single test, normalizes the result, and persists it.
    All recoverable errors are caught and logged here, returning None
    on failure so the calling loop can continue without interruption.

monitor_network()
    Drives the sampling loop. On the first successful test, it resolves
    and pins the server ID to ensure all subsequent samples in the same
    session target the same server, preserving statistical consistency.
    Server resolution failure is non-fatal: the next iteration will
    attempt a new test and re-resolve the server.

Error Handling
--------------
All exceptions are handled within the service layer and never propagate
to the caller. Each failure domain is caught and logged independently:

    SpeedTestExecutionError  — CLI process failed or returned bad output.
    NormalizationError       — Raw result could not be mapped to SpeedRecord.
    OSError                  — CSV file operation failed.
    ServerResolutionError    — Server ID could not be resolved after a test.
    Exception                — Unexpected error, logged as a safety net.

Usage
-----
    from core.speed_test_service import LibreSpeedService
    from infrastructure.database.csv_session import get_session
    from infrastructure.repository.csv_repository import TestRepository

    service = LibreSpeedService(TestRepository(get_session()))
    service.monitor_network(num_samples=5)
"""
from infrastructure.adapters.libre_speed_adapter import TestSpeedAdapter
from schemas.is_speed_test import ISpeedTest
from utils.normalize_results import SpeedTestManager
from models.speed_entities import SpeedRecord
from infrastructure.repository.csv_repository import TestRepository
from utils.exceptions import SpeedTestExecutionError, ServerResolutionError, NormalizationError
from typing import Optional
from dataclasses import asdict
from typing import TypeVar, Generic, Type

T = TypeVar('T', bound=ISpeedTest) # Look if this passway with factory

class NetworkSpeedService(Generic[T]):
    
    def __init__(self, repo: TestRepository, adapter: Type[TestSpeedAdapter[T]]) -> None:
        self._repo = repo
        self._adapter = adapter
        self._server_id: Optional[int] = None

    def _test_network(self) -> Optional[T]:
        
        results = None
        
        try:
            
            results = self._adapter.run_a_test(
                server_id = self._server_id
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
        
        for _ in range(num_samples):
            
            result = self._test_network()
            
            if result is None:
                
                continue
            
            if not self._server_id:
                
                try:
                    self._server_id = self._adapter.find_server_id(result)
                    
                except ServerResolutionError as e:
                    print(f"[ERROR] Server resolution failed: {e}")

    def access_records(self):
        
        records = self._repo.get_all_records()
        
        return [asdict(r) for r in records]