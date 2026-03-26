# infrastruture/repository/csv_repository.py

from infrastructure.database.csv_session import CSVSession
from models.speed_entities import SpeedRecord
from dataclasses import asdict

class TestRepository:
    
    def __init__(self, session: CSVSession) -> None:
        self._session = session
        
    def get_all_records(self) -> list[SpeedRecord]:
        
        raw_records = self._session.read_all()
        
        return [
            SpeedRecord(**record) for record in raw_records
            ]
        
    def store_record(self, record: SpeedRecord) -> None:
        
        self._session.write_row(asdict(record))
