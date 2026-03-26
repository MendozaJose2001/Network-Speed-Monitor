# utils/normlaize_results.py

from models.speed_entities import SpeedRecord
from utils.mapp_headers import HeaderManager
from schemas.is_speed_test import ISpeedTest
from utils.types import StrFloat
from typing import Dict
from utils.exceptions import NormalizationError

class SpeedTestManager:
    
    _SCALE_UP_DOWN = 10**6
    _SCALE_TIME = 10**-3
    _ROUNDS_DIGITS = 4
    _REFERENCE_HEADER = HeaderManager.get_header_dataclass(SpeedRecord)
    
    @classmethod
    def normalize_record(cls, record: ISpeedTest) -> Dict[str, str]:
        
        try:
            record_header = HeaderManager.get_header_dataclass(record)
        
            mapper = HeaderManager.map_best_unique_matches(
                reference_header=cls._REFERENCE_HEADER,
                input_header=record_header
                )
            
        except (ValueError, TypeError) as e:
            raise NormalizationError(f"Header mapping failed: {e}")
        
        normalized_data = {}
        
        for attribute in mapper.keys():
            
            value = getattr(record, mapper[attribute])
            
            if 'bps' in attribute:
                
                try:
                    value = round(
                        float(value)*(record.get_up_down_unit()/cls._SCALE_UP_DOWN), 
                        cls._ROUNDS_DIGITS
                        )
                except (ValueError, AttributeError) as e:
                    raise NormalizationError(f"Failed to normalize field '{attribute}': {e}")
                
            if 'ms' in attribute: 
                
                try:
                    value = round(
                        float(value)*(record.get_time_unit()/cls._SCALE_TIME), 
                        cls._ROUNDS_DIGITS
                        )
                except (ValueError, AttributeError) as e:
                    raise NormalizationError(f"Failed to normalize field '{attribute}': {e}")
                
            if 'server' in attribute and isinstance(value, Dict):
                value = value.get('name')
                    
            normalized_data[attribute] = str(value)
            
        return normalized_data
                
    

    