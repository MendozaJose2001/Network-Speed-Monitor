# infrastructure/database/csv_session.py
"""
CSV Session Management
======================
Handles low-level read and write operations against CSV files used as
the storage backend for speed test records.

Design
------
Each call to get_session() produces a new CSVSession bound to a uniquely
timestamped file. This is intentional: every monitoring run generates its
own isolated CSV, providing a clear and differentiated record per session.
If a unified dataset is needed across sessions, files can be merged by a
separate service.

CSVSession is instantiated with a file path and delimiter. On construction,
it ensures the target directory and file exist, creating them if necessary.
The header row is written lazily on the first write_row() call, only if
the file is empty, avoiding duplicate headers on subsequent writes.

The module-level _get_csv_path() and get_session() are kept private and
public respectively, following the same encapsulation pattern used across
the infrastructure layer. External callers always use get_session() and
never construct CSVSession directly with a raw path.

Usage
-----
    from infrastructure.database.csv_session import get_session

    session = get_session()
    session.write_row({'timestamp': '...', 'download_mbps': '95.4'})
    records = session.read_all()

Raises
------
OSError
    If the data directory or file cannot be created, or if a read or
    write operation fails due to permission or filesystem errors.
"""
import csv
from pathlib import Path
from utils.time_manager import TimeManager


def _get_csv_path() -> Path:
    """
    Generate a timestamped file path for a new CSV session.

    Combines a fixed data directory with the current UTC timestamp to
    produce a unique, human-readable filename for each monitoring run.

    Returns
    -------
    Path
        A Path object pointing to the target CSV file, e.g.:
        'data/speed_register_2024-01-15T10-30-45Z.csv'
    """
    DATA_DIR = Path("data")
    timestamp = TimeManager.get_str_now()

    return DATA_DIR / f"speed_register_{timestamp}.csv"


class CSVSession:
    """
    Low-level CSV file handler for reading and writing speed test records.

    Each instance is bound to a single file for the duration of a
    monitoring session. The file and its parent directory are created
    on instantiation if they do not already exist.

    Parameters
    ----------
    path : Path
        The file path to bind this session to.
    delimiter : str, optional
        The CSV delimiter character. Defaults to ','.
    """

    def __init__(self, path: Path, delimiter: str = ",") -> None:
        self._path = path
        self._delimiter = delimiter

        # Ensure the data directory and file exist before any operations.
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch()

    def read_all(self) -> list[dict]:
        """
        Read all records from the CSV file.

        Returns
        -------
        list[dict]
            A list of dictionaries where each dict represents one row,
            keyed by the CSV header fields.
        """
        with self._path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(f=file, delimiter=self._delimiter)
            return list(reader)

    def write_row(self, row: dict) -> None:
        """
        Append a single row to the CSV file.

        Writes the header automatically on the first call if the file
        is empty, ensuring the CSV is always valid without requiring
        the caller to manage header state.

        Parameters
        ----------
        row : dict
            A dictionary representing the row to write. Keys are used
            as column names if the header has not been written yet.
        """
        is_empty = self._path.stat().st_size == 0

        with self._path.open("a", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                f=file,
                fieldnames=row.keys(),
                delimiter=self._delimiter
            )

            # Write header only on the first row to avoid duplicates.
            if is_empty:
                writer.writeheader()

            writer.writerow(row)


def get_session() -> CSVSession:
    """
    Instantiate and return a new CSVSession for the current monitoring run.

    Generates a unique timestamped file path and binds a fresh CSVSession
    to it. This is the intended entry point for all external callers.

    Returns
    -------
    CSVSession
        A new session instance bound to a uniquely named CSV file.

    Example
    -------
        >>> from infrastructure.database.csv_session import get_session
        >>> session = get_session()
        >>> session.write_row({'timestamp': '...', 'download_mbps': '95.4'})
    """
    return CSVSession(path=_get_csv_path())