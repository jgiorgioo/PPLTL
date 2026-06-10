import os
import subprocess

def _get_default_val_path():
    """Returns the absolute path to the VAL Validate binary in WSL."""
    return os.path.abspath(os.path.join(os.path.expanduser("~"), "VAL", "build", "bin", "Validate"))

def validate_plan(domain_file, problem_file, plan_file, val_path=None):
    """Validates a PDDL plan using the VAL binary."""
    val_binary = os.path.abspath(val_path) if val_path else _get_default_val_path()
    
    # Check if required files exist
    if not os.path.exists(val_binary):
        print(f"[ERROR validator] VAL binary not found at: {val_binary}")
        return False

    if not os.path.exists(plan_file):
        print(f"[ERROR validator] Plan file not found at: {plan_file}")
        return False

    command = [val_binary, domain_file, problem_file, plan_file]
    
    try:
        # Run VAL validation with a 10-second timeout
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        
        # VAL returns 0 and prints 'Plan valid' if the plan is correct
        if result.returncode == 0 and "plan valid" in result.stdout.lower():
            return True
            
        print(f"[DEBUG validator] Validation failed for {plan_file}")
        print(f"[VAL stdout]: {result.stdout}")
        return False

    except subprocess.TimeoutExpired:
        print("[DEBUG validator] VAL validation timeout expired.")
        return False
    except Exception as e:
        print(f"[ERROR validator] Unexpected error during validation: {e}")
        return False