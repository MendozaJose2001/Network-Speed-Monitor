# utils/mapp_headers.py

from difflib import SequenceMatcher
from dataclasses import fields, is_dataclass
from typing import List, Dict
from utils.types import DataClassProtocol

class HeaderManager:
    
    _THRESHOLD_UQ_MATCH = 0.6 # Should be select by try and error for now.
        
    @classmethod
    def map_best_unique_matches(
        cls,
        reference_header: List[str],
        input_header: List[str] 
    ) -> Dict[str,str]:
        
        """
        Maps input headers to reference headers based on sequence similarity.

        This method identifies the best one-to-one matches between a list of 
        expected field names (reference) and a list of provided column names 
        (input) using a greedy matching algorithm.

        Args:
            reference_header: Expected field names from the data model.
            input_header: Actual column names received from the external source.

        Returns:
            A dictionary mapping reference field names to input column names.

        Raises:
            ValueError: If no matches are found above the specified threshold.

        Note:
            Current implementation uses 'difflib.SequenceMatcher', which calculates 
            similarity based on the longest common substrings (Ratcliff/Obershelp). 
            
            Future Improvements:
            - Consider 'Levenshtein Distance' for better handling of character 
              insertions/deletions if external dependencies are allowed.
            - Implement a 'Containment Check' (e.g., if ref in inp) to boost scores 
              for nested naming conventions (e.g., 'date' vs 'order_date').
            - Integrate Jaro-Winkler similarity to prioritize prefix matching, 
              which is common in structured data schemas.
        """
        
        score = [
            (ref, inp, SequenceMatcher(a = ref, b= inp).ratio()) 
            for inp in input_header
            for ref in reference_header
        ]
        
        score.sort(key=lambda x: x[2],
                   reverse=True)
        
        mapping = {}
        used_candidates = set()
        
        for ref, inp, ratio in score:
            
            if ratio < cls._THRESHOLD_UQ_MATCH: 
                continue
            
            if ref not in mapping and inp not in used_candidates:
                mapping[ref] = inp
                used_candidates.add(inp)
                
        if not mapping:
            raise ValueError(
                f"No matches found (reference macth rate {cls._THRESHOLD_UQ_MATCH})"
            )
                
        return mapping

    @staticmethod
    def get_header_dataclass(
        cls_schema: DataClassProtocol
        ) -> list[str]:
        
        if not is_dataclass(cls_schema):
            
            name = getattr(cls_schema, "__name__", str(cls_schema))
            
            raise TypeError(
                f"The evaluated model/schema {name} must be a dataclass schema"
                )
        
        return [
            field.name for field in fields(cls_schema)
            ]
    
