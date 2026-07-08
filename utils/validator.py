import os
import subprocess
from .exceptions import MissingBinaryError, PipelineTimeoutError

VAL_TIMEOUT = 10

def _get_default_val_path():
    return os.path.abspath(os.path.join(os.path.expanduser("~"), "VAL", "build", "bin", "Validate"))

def validate_plan(domain_file, problem_file, plan_file, val_path=None):
    val_binary = os.path.abspath(val_path) if val_path else _get_default_val_path()
    
    if not os.path.exists(val_binary):
        raise MissingBinaryError(f"VAL validation binary missing at: {val_binary}")

    if not os.path.exists(plan_file):
        raise FileNotFoundError(f"Plan file missing for validation: {plan_file}")

    command = [val_binary, domain_file, problem_file, plan_file]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=VAL_TIMEOUT)
        
        if result.returncode == 0 and "plan valid" in result.stdout.lower():
            return True
            
        return False

    except subprocess.TimeoutExpired:
        raise PipelineTimeoutError(f"VAL validation timed out after {VAL_TIMEOUT}s.")