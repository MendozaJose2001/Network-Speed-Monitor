# infrastruture/database/csv_session.py

import csv
from pathlib import Path
from utils.time_manager import TimeManager

def _get_csv_path() -> Path:
    
    DATA_DIR = Path("data")
    timestamp = TimeManager.get_str_now()
    
    return DATA_DIR / f"speed_register_{timestamp}.csv"
    
class CSVSession:
    
    def __init__(self, path: Path, delimiter: str = ",") -> None:
        self._path = path
        self._delimiter = delimiter
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch()
        
    def read_all(self) -> list[dict]:
        with self._path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(f=file, 
                                    delimiter=self._delimiter
                                    )
            return list(reader)
    
    def write_row(self, row: dict) -> None:
        
        is_empty = self._path.stat().st_size == 0
        
        with  self._path.open("a", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(f=file, 
                                    fieldnames=row.keys(), 
                                    delimiter=self._delimiter
                                    )
            
            if is_empty:
                writer.writeheader()
                
            writer.writerow(row)
            
def get_session() -> CSVSession:
    return CSVSession(
        path=_get_csv_path()
        )