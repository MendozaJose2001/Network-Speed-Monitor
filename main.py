# main.py
"""
Network Speed Monitor
=====================
Entry point for the network speed monitoring application. Composes the
full dependency graph, runs the monitoring session, and reports the
total execution time.

Composition
-----------
Dependencies are assembled here at the top level, following the
Dependency Injection pattern used across the project:

    get_session()        — creates a new timestamped CSVSession.
    TestRepository       — binds the session to the data access layer.
    LibreSpeedService    — binds the repository to the service layer.

The app instance is module-level so the full composition is resolved
once at import time, before main() is called.

Usage
-----
    python main.py

Output
------
    ========================================
    Monitoring...
    Network Monitoring Time: 0:05:23.412310 s
    ========================================

Notes
-----
num_samples controls how many speed test measurements are collected
in a single run. Each run produces one uniquely timestamped CSV file
in the data/ directory. See infrastructure/database/csv_session.py
for details on session file naming.
"""
from core.speed_test_service import NetworkSpeedService
from infrastructure.adapters.libre_speed_adapter import LibreSpeedAdapter, SpeedTestGoAdapter
from infrastructure.database.csv_session import get_session
from infrastructure.repository.csv_repository import TestRepository
from utils.time_manager import TimeManager


# Compose the full dependency graph once at import time.
app = NetworkSpeedService(
    TestRepository(get_session(file_name='speed_register_2026-03-29T02-17-53Z.csv')),
    SpeedTestGoAdapter
)


def main() -> None:
    """
    Run a network speed monitoring session and report execution time.

    Collects the configured number of speed test samples, persisting
    each result to a timestamped CSV file. Prints the total wall-clock
    duration of the session on completion.
    """
    print("=" * 40)
    print("Monitoring...")
    start = TimeManager.timestamp_now()

    app.monitor_network(num_samples=100)

    end = TimeManager.timestamp_now()
    print(f"Network Monitoring Time: {end - start}")
    print("=" * 40)


if __name__ == "__main__":
    main()