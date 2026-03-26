# main.py

from core.speed_test_service import LibreSpeedService
from infrastructure.database.csv_session import get_session
from infrastructure.repository.csv_repository import TestRepository
from utils.time_manager import TimeManager

app = LibreSpeedService(
    TestRepository(get_session())
    )
        
def main() -> None:
    
    print("="*40)
    print("Monitoring...")
    start = TimeManager.timestamp_now()
    
    app.monitor_network(num_samples=100)
    
    end = TimeManager.timestamp_now()
    print(f"Network Monitoring Time: {end - start} s")
    print("="*40)
    
    
if __name__ == "__main__": 
    main()
    