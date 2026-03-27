# infrastructure/repository/csv_repository.py
"""
Speed Test Repository
=====================
Provides the data access layer for persisting and retrieving canonical
SpeedRecord instances. Abstracts all storage details from the service
layer, which interacts exclusively with SpeedRecord objects and never
with raw CSV data.

Design
------
TestRepository follows the Repository pattern: it mediates between the
domain model (SpeedRecord) and the storage backend (CSVSession), handling
serialization and deserialization transparently.

The session is injected at construction time, keeping the repository
decoupled from any specific storage backend. Swapping CSVSession for a
different backend (e.g., a database session) requires no changes to the
repository interface or the service layer.

Serialization
-------------
SpeedRecord instances are serialized to dict via dataclasses.asdict()
before being handed to the session. On read, raw dicts from the session
are deserialized back into SpeedRecord instances via unpacking.

Usage
-----
    from infrastructure.database.csv_session import get_session
    from infrastructure.repository.csv_repository import TestRepository

    repo = TestRepository(get_session())
    repo.store_record(record)
    records = repo.get_all_records()

Raises
------
OSError
    Propagated from CSVSession if the underlying file operation fails.
TypeError
    If the CSV data does not match the expected SpeedRecord field names.
"""
from infrastructure.database.csv_session import CSVSession
from models.speed_entities import SpeedRecord
from dataclasses import asdict


class TestRepository:
    """
    Data access layer for SpeedRecord persistence.

    Mediates between the SpeedRecord domain model and the CSVSession
    storage backend. The session is injected at construction time to
    keep the repository decoupled from any specific storage implementation.

    Parameters
    ----------
    session : CSVSession
        The storage session to read from and write to.
    """

    def __init__(self, session: CSVSession) -> None:
        self._session = session

    def get_all_records(self) -> list[SpeedRecord]:
        """
        Retrieve all stored speed test records.

        Reads all rows from the session and deserializes each into a
        SpeedRecord instance.

        Returns
        -------
        list[SpeedRecord]
            A list of all SpeedRecord instances stored in the current
            session's CSV file. Returns an empty list if no records exist.

        Raises
        ------
        TypeError
            If any row in the CSV does not match the SpeedRecord field names.
        """
        raw_records = self._session.read_all()

        return [
            SpeedRecord(**record) for record in raw_records
        ]

    def store_record(self, record: SpeedRecord) -> None:
        """
        Persist a single SpeedRecord to storage.

        Serializes the SpeedRecord to a dictionary via asdict() and
        delegates the write operation to the session.

        Parameters
        ----------
        record : SpeedRecord
            The normalized speed test result to persist.

        Raises
        ------
        OSError
            If the underlying CSV write operation fails.
        """
        self._session.write_row(asdict(record))