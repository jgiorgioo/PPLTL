import os
import sys
import re
import shutil
from pathlib import Path
from pddl.parser.problem import ProblemParser
from pddl.logic.base import And
from .validator import validate_plan
from .solver import verify_feasibility

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
        return False

    try:
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
    except Exception as e:
        print(f"[ERROR util] Failed to patch PDDL problem header: {e}")
        return False

def save_valid_instance(domain_name, candidate_path, local_plan, problems_dir, plans_dir):
    try:
        final_id = get_highest_index(domain_name, problems_dir) + 1
        
        new_prob_filename = f"{domain_name}-{final_id}.pddl"
        dest_prob_path = os.path.join(problems_dir, new_prob_filename)
        
        dest_plan_filename = f"{domain_name}-{final_id}.plan"
        dest_plan_path = os.path.join(plans_dir, dest_plan_filename)
        
        os.makedirs(problems_dir, exist_ok=True)
        os.makedirs(plans_dir, exist_ok=True)
        
        shutil.move(candidate_path, dest_prob_path)
        
        new_prob_name = f"{domain_name}-{final_id}"
        rename_problem(dest_prob_path, new_prob_name)
        
        if os.path.exists(local_plan):
            shutil.move(local_plan, dest_plan_path)
        else:
            print(f"[ERROR util] Base plan solution not found at: {local_plan}")
            return False
            
        return True
        
    except Exception as e:
        print(f"[ERROR util] Failed to save valid instance: {e}")
        return False


def save_constrained_instance(domain_name, temp_domain_path, temp_problem_path, local_plan, base_constrained_dir, temp_rule_path, constraint_name):
    try:
        next_id = get_highest_index(domain_name, base_constrained_dir) + 1
        
        full_instance_name = f"{domain_name}-{next_id}-{constraint_name}"
        target_problem_dir = os.path.join(base_constrained_dir, full_instance_name)
        os.makedirs(target_problem_dir, exist_ok=True)
        
        final_problem_path = os.path.join(target_problem_dir, f"{full_instance_name}.pddl")
        shutil.move(temp_problem_path, final_problem_path)
        
        rename_problem(final_problem_path, full_instance_name)

        final_domain_path = os.path.join(target_problem_dir, f"{domain_name}-{next_id}-{constraint_name}-domain.pddl")
        final_plan_path = os.path.join(target_problem_dir, f"{domain_name}-{next_id}-{constraint_name}.plan")

        if os.path.exists(temp_domain_path):
            shutil.move(temp_domain_path, final_domain_path)
        else:
            print(f"[ERROR util] Compiled domain not found at: {temp_domain_path}")
            return False

        if os.path.exists(local_plan):
            shutil.move(local_plan, final_plan_path)
        else:
            print(f"[ERROR util] Plan solution not found at: {local_plan}")
            return False
        
        if temp_rule_path and os.path.exists(temp_rule_path):
            final_rule_path = os.path.join(target_problem_dir, "rule.txt")
            shutil.move(temp_rule_path, final_rule_path)
            
        return True

    except Exception as e:
        print(f"[ERROR util] Failed to save encapsulated constrained instance: {e}")
        return False
    
def clear_domain_dirs(prob_dir, plan_dir):
    removed = 0
    targets = [prob_dir, plan_dir]
    
    for folder in targets:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                
                if os.path.isdir(file_path) or file == "domain.pddl":
                    continue
                    
                if file.endswith(".pddl") or file.endswith(".plan") or file.startswith("temp_") or file in ["output.sas", "sas_plan"]:
                    try:
                        os.remove(file_path)
                        removed += 1
                    except:
                        pass
                        
    return removed
    
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
    if not domain_path or not os.path.exists(domain_path):
        print(f"[ERROR] Specified domain path not found for: {domain_name}")
        return False

    search_config = get_search_config(domain_name)
    
    # 1. Plan using Fast Downward
    is_solvable, local_plan = verify_feasibility(
        domain_path, 
        problem_path, 
        search_config=search_config, 
        timeout=timeout
    )
    
    if not is_solvable or not local_plan or not os.path.exists(local_plan):
        print(f"[INFO] Planning process failed for {domain_name}.")
        return False

    try:
        # 2. Validate the generated plan using VAL
        if validate_plan(domain_path, problem_path, local_plan):
            # 3. Execute the custom storage callback method
            return save_callback(local_plan)
        else:
            print(f"[WARN] Plan validation failed via VAL for {domain_name}.")
            return False
            
    finally:
        # Centralized cleanup of the temporary local plan file
        if local_plan and os.path.exists(local_plan):
            try:
                os.remove(local_plan)
            except Exception:
                pass

def run_generic_pipeline_loop(target_dir, file_prefix, count, pipeline_func, status_callback=None):
    """
    Universal loop orchestrator for flat generation and LTL constraints.
    Manages target calculation, the while loop, Ctrl+C handling, and logs via callback.
    """
    target_dir = os.path.abspath(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    
    # Count how many valid items already exist based solely on the prefix
    files_saved = len([
        f for f in os.listdir(target_dir) 
        if f.startswith(file_prefix)
    ])
    
    total_target = files_saved + count
    
    if status_callback:
        status_callback("init", {"current": files_saved, "target": total_target})
    
    try:
        while files_saved < total_target:
            if status_callback: 
                status_callback("attempt", None)
            
            success = pipeline_func()
            
            if success:
                # Re-evaluate disk state using only the prefix filter
                files_saved = len([
                    f for f in os.listdir(target_dir) 
                    if f.startswith(file_prefix)
                ])
                if status_callback: 
                    status_callback("success", {"current": files_saved, "target": total_target})
            else:
                if status_callback: 
                    status_callback("failed", None)
                    
        if status_callback: 
            status_callback("finished", {"prefix": file_prefix.rstrip("-")})
            
    except KeyboardInterrupt:
        if os.path.exists(target_dir):
            for f in os.listdir(target_dir):
                if f.startswith("temp_") or f.startswith("tmp_"):
                    try: 
                        os.remove(os.path.join(target_dir, f))
                    except: 
                        pass
        if status_callback: 
            status_callback("interrupted", None)
        sys.exit(0)