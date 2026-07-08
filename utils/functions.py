import os
import sys
import re
import shutil
from .validator import validate_plan
from .solver import verify_feasibility
from .exceptions import handle_pipeline_exception

def get_highest_index(domain_name, target_dir):
    if not os.path.exists(target_dir):
        return 0

    highest_index = 0
    prefix = f"{domain_name}-"

    for entry in os.listdir(target_dir):
        if entry.startswith(prefix):
            base_name = entry.split('.')[0] if '.' in entry else entry
            try:
                parts = base_name.split("-")
                index = int(parts[-1])
                if index > highest_index:
                    highest_index = index
            except (ValueError, IndexError):
                continue
                
    return highest_index

def rename_problem(target_file_path, new_prob_name):
    if not target_file_path or not os.path.exists(target_file_path):
        raise FileNotFoundError(f"Target problem file missing: {target_file_path}")

    with open(target_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    match = re.search(r"\(define\s*\(\s*problem\s+([^\s\)]+)", content, re.IGNORECASE)
    if match:
        native_prob_name = match.group(1)
        
        pattern = r"(\(define\s*\(\s*problem\s+)" + re.escape(native_prob_name) + r"(\s*\))"
        if re.search(pattern, content, re.IGNORECASE):
            content = re.sub(pattern, r"\1" + new_prob_name + r"\2", content, flags=re.IGNORECASE)
        else:
            content = content.replace(f"problem {native_prob_name}", f"problem {new_prob_name}")
    
    with open(target_file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return True

def save_valid_instance(domain_name, candidate_path, local_plan, problems_dir, plans_dir, stratum):
    final_id = get_highest_index(domain_name, problems_dir) + 1
    
    new_prob_filename = f"{domain_name}-{stratum}-{final_id}.pddl"
    dest_prob_path = os.path.join(problems_dir, new_prob_filename)
    
    dest_plan_filename = f"{domain_name}-{stratum}-{final_id}.plan"
    dest_plan_path = os.path.join(plans_dir, dest_plan_filename)
    
    os.makedirs(problems_dir, exist_ok=True)
    os.makedirs(plans_dir, exist_ok=True)
    
    shutil.move(candidate_path, dest_prob_path)
    rename_problem(dest_prob_path, f"{domain_name}-{final_id}")
    
    if os.path.exists(local_plan):
        shutil.move(local_plan, dest_plan_path)
    else:
        raise FileNotFoundError(f"Generated plan solution file vanished: {local_plan}")
        
    return True

def count_unconstrained_instances(domain_name, base_unconstrained_dir):
    if not os.path.exists(base_unconstrained_dir):
        return 0
    total_count = 0
    for entry in os.listdir(base_unconstrained_dir):
        stratum_path = os.path.join(base_unconstrained_dir, entry)
        if os.path.isdir(stratum_path):
            total_count += get_highest_index(domain_name, stratum_path)
    return total_count

def save_constrained_instance(domain_name, temp_domain_path, temp_problem_path, local_plan, base_constrained_dir, temp_rule_path, constraint_name):
    next_id = get_highest_index(domain_name, base_constrained_dir) + 1
    
    full_instance_name = f"{domain_name}-{constraint_name}-{next_id}"
    target_problem_dir = os.path.join(base_constrained_dir, full_instance_name)
    os.makedirs(target_problem_dir, exist_ok=True)
    
    final_problem_path = os.path.join(target_problem_dir, f"{full_instance_name}.pddl")
    shutil.move(temp_problem_path, final_problem_path)
    
    rename_problem(final_problem_path, full_instance_name)

    shutil.move(temp_domain_path, os.path.join(target_problem_dir, f"{domain_name}-{constraint_name}-{next_id}-domain.pddl"))
    shutil.move(local_plan, os.path.join(target_problem_dir, f"{domain_name}-{constraint_name}-{next_id}.plan"))
    
    if temp_rule_path and os.path.exists(temp_rule_path):
        shutil.move(temp_rule_path, os.path.join(target_problem_dir, "rule.txt"))
        
    return True
    
def count_constrained_instances(domain_name, constraint_folder_path):
    return get_highest_index(domain_name, constraint_folder_path)
    
def get_search_config(domain_name: str) -> str:
    if domain_name in ["sokoban", "goldminer","gridworld"]:
        return "lazy_greedy([ff()], preferred=[ff()])"
    return "astar(blind())"


def verify_validate_and_save(domain_name, domain_mapping, problem_path, save_callback, timeout):
    """
    Unified function that handles planning with Fast Downward and validation with VAL.
    Accepts domain_mapping configuration and a specific save_callback function
    to decouple the raw planning execution from the different dataset storage logic.
    """
    domain_path = domain_mapping.get(domain_name)
    search_config = get_search_config(domain_name)
    
    # 1. Plan using Fast Downward
    is_solvable, local_plan = verify_feasibility(
        domain_path, 
        problem_path, 
        search_config=search_config, 
        timeout=timeout
    )
    
    if not is_solvable or not local_plan or not os.path.exists(local_plan):
        return False

        # 2. Validate the generated plan using VAL
    if validate_plan(domain_path, problem_path, local_plan):
            # 3. Execute the custom storage callback method
        return save_callback(local_plan)
    else:
        return False
            

def run_generic_pipeline_loop(target_dir, file_prefix, count, pipeline_func, status_callback=None):
    """
    Universal loop orchestrator for flat generation and LTL constraints.
    Manages session progress counters, Ctrl+C handling, and logs via callback.
    """
    target_dir = os.path.abspath(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    
    successful_generations = 0
    
    if status_callback:
        status_callback("init", {"current": 0, "target": count})
    
    try:
        while successful_generations < count:
            if status_callback: 
                status_callback("attempt", None)
            
            try:
                success = pipeline_func()
                
                if success:
                    successful_generations = successful_generations + 1
                    if status_callback: 
                        status_callback("success", {"current": successful_generations, "target": count})
                else:
                    if status_callback: 
                        status_callback("failed", None)
            
            except Exception as e:
                should_abort = handle_pipeline_exception(e, status_callback)
                if should_abort:
                    break
    
        if status_callback: 
            status_callback("finished", {"prefix": file_prefix.rstrip("-")})

            
    except KeyboardInterrupt:
        if status_callback: 
            status_callback("interrupted", None)
        sys.exit(0)