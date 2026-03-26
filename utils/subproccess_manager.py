# utils/subproccess_manager.py

import subprocess
import json
from typing import Tuple, Any
from utils.exceptions import SpeedTestExecutionError

class SubProcessManager:
    
    _CAPTURE_OUTPUT = True
    _TEXT_ = True
    
    @classmethod
    def run_subproccess(cls, arg: Tuple[str]) -> Any:
        process = subprocess.run(
            args = arg, 
            capture_output = True, 
            text = True)
        
        if process.returncode != 0:
            raise SpeedTestExecutionError(f"CLI execution failed: {process.stderr}")
        
        result = process.stdout if process.stdout.strip() else process.stderr
        
        try:
            return json.loads(result)
        
        except (json.JSONDecodeError, TypeError):
            return result