import os
import subprocess
from .exceptions import MissingBinaryError, PipelineTimeoutError
def _get_default_fd_path():
    """
    NOTE: Override this return statement with your custom path if 
    Fast Downward is installed in a different location.
    
    You can use an absolute string path or dynamic resolution via os.path.expanduser.
    """
    # Dynamic approach (Recommended for default home installations)
    return os.path.abspath(os.path.join(os.path.expanduser("~"), "downward", "fast-downward.py"))
    
    # Alternative approach (Hardcoded absolute path if needed)
    # return "/opt/downward/fast-downward.py"

def _run_planner(domain_file, problem_file, search_config, timeout, fd_path):
    fd_script = os.path.abspath(fd_path) if fd_path else _get_default_fd_path()

    if not os.path.exists(fd_script):
        raise MissingBinaryError(f"Fast Downward executable missing at: {fd_script}")

    local_plan = "sas_plan"
    command = ["python3", fd_script, domain_file, problem_file, "--search", search_config]
    
    try:
        if os.path.exists(local_plan): 
            os.remove(local_plan)
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)

        if result.returncode == 0 and "Solution found!" in result.stdout:
            if os.path.exists(local_plan):
                return True
        return False

    except subprocess.TimeoutExpired:
        raise PipelineTimeoutError(f"Planner execution timed out after {timeout}s.")

def verify_feasibility(domain_file, problem_file, search_config, timeout=10, fd_path=None):
    local_plan = "sas_plan"
    success = _run_planner(domain_file, problem_file, search_config, timeout, fd_path)
    
    if success and os.path.exists(local_plan):
        return True, local_plan
        
    return False, None