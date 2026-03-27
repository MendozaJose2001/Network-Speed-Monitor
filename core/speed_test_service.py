# core/speed_test_service.py
"""
Speed Test Service
==================
Orchestrates the full speed test monitoring workflow: executing tests,
normalizing results, persisting records, and resolving server consistency
across multiple samples within a session.

Design
------
SpeedTestService defines the abstract base for all monitoring services,
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
from infrastructure.adapters.libre_speed_adapter import LibreSpeedAdapter
from schemas.is_speed_test import LibreSpeedTest, ISpeedTest
from utils.normalize_results import SpeedTestManager
from models.speed_entities import SpeedRecord
from infrastructure.repository.csv_repository import TestRepository
from utils.exceptions import SpeedTestExecutionError, ServerResolutionError, NormalizationError
from abc import ABC, abstractmethod
from typing import Optional


class SpeedTestService(ABC):
    """
    Abstract base class for speed test monitoring services.

    Defines the shared constructor and the interface that all concrete
    service implementations must fulfill. The repository is injected at
    construction time to decouple the service from any specific storage
    backend.

    Parameters
    ----------
    repo : TestRepository
        The repository instance used to persist speed test records.
    """

    def __init__(self, repo: TestRepository) -> None:
        self._repo = repo
        self._server_id = None

    @abstractmethod
    def _test_network(self) -> Optional[ISpeedTest]:
        """
        Execute a single speed test, normalize, and persist the result.

        Returns
        -------
        Optional[ISpeedTest]
            The raw test result on success, or None if any step failed.
        """
        pass


class LibreSpeedService(SpeedTestService):
    """
    Concrete monitoring service for the LibreSpeed CLI.

    Implements _test_network() and monitor_network() to drive the full
    sampling workflow using LibreSpeedAdapter as the test executor.
    """

    def _test_network(self) -> Optional[LibreSpeedTest]:
        """
        Execute a single LibreSpeed test, normalize, and persist the result.

        Runs the test against the pinned server ID if one has been resolved,
        otherwise lets the CLI select the best server automatically.

        All exceptions are caught and logged independently. The method
        returns None on any failure, allowing the sampling loop in
        monitor_network() to continue with the next iteration.

        Returns
        -------
        Optional[LibreSpeedTest]
            The raw LibreSpeedTest result on success, or None on failure.
        """
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
        """
        Execute a series of speed tests and persist each result.

        On the first successful test, resolves the server ID used by the
        CLI and pins it for all subsequent samples in the session. This
        ensures statistical consistency across measurements by always
        targeting the same server.

        If a test fails, the iteration is skipped via continue. If server
        resolution fails, the error is logged and the next iteration will
        attempt to re-resolve the server from a fresh test result.

        Parameters
        ----------
        num_samples : int, optional
            Number of speed test samples to collect. Defaults to 1.
        """
        for i in range(num_samples):

            result = self._test_network()

            # Skip server resolution if the test failed.
            if result is None:
                continue

            # Resolve and pin the server ID on the first successful test.
            if not self._server_id:
                try:
                    self._server_id = LibreSpeedAdapter.find_server_id(result)
                except ServerResolutionError as e:
                    print(f"[ERROR] Server resolution failed: {e}")