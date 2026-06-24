import os
import subprocess
import shutil

def _get_default_fd_path():
    return os.path.abspath(os.path.join(os.path.expanduser("~"), "downward", "fast-downward.py"))

def _run_planner(domain_file, problem_file, search_config, timeout, fd_path):
    fd_script = os.path.abspath(fd_path) if fd_path else _get_default_fd_path()
    
    if not os.path.exists(fd_script):
        print(f"[ERROR solver] Fast Downward not found at: {fd_script}")
        return False

    local_plan = "sas_plan"
    output_sas = "output.sas"
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
        print(f"[DEBUG solver] Planner timeout of {timeout}s expired.")
        return False
        
    finally:
        if os.path.exists(output_sas):
            try: os.remove(output_sas)
            except: pass


def verify_feasibility(domain_file, problem_file, search_config, timeout=10, fd_path=None):
    local_plan = "sas_plan"
    success = _run_planner(domain_file, problem_file, search_config, timeout, fd_path)
    
    if success and os.path.exists(local_plan):
        return True, local_plan
        
    return False, None


def solve(domain_file, problem_file, search_config, output_plan_path, timeout=30, fd_path=None):
    local_plan = "sas_plan"
    success = _run_planner(domain_file, problem_file, search_config, timeout, fd_path)
    
    try:
        if success and os.path.exists(local_plan):
            os.makedirs(os.path.dirname(os.path.abspath(output_plan_path)), exist_ok=True)
            shutil.move(local_plan, output_plan_path)
            return True
        return False
    finally:
        if os.path.exists(local_plan):
            try: os.remove(local_plan)
            except: pass