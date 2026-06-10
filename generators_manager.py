import os
import sys
import random
import subprocess
import shutil
from generators import PDDLGenerator
from util import rename_problem, save_valid_instance
from solver import verify_feasibility
from validator import validate_plan 

# Centralized configuration pools owned globally by the module
MINIGRID_POOL = {
    "floorplans": [
        ("9room3.fpl", 35),
        ("9room2.fpl", 35),
        ("4room3.fpl", 10),
        ("3Vroom3.fpl", 10),
        ("3Hroom3.fpl", 10)
    ],
    "nshapes_range": (2, 6)
}

CITYCAR_POOL = {
    "rows_range": (4, 10),
    "cols_range": (4, 10),
    "cars_range": (1, 2),
    "garages_range": (1, 4)
}

GOLDMINER_POOL = {
    "rows_range": (5, 10),
    "cols_range": (5, 10)
}

SOKOBAN_POOL = {
    "grid_size_range": (5, 10),
    "boxes_range": (1, 5)
} 


def _verify_and_save(domain_name, candidate_path, problems_dir, plans_dir):
    domain_mapping = {
        "citycar": os.path.abspath(os.path.join("plans", "uncostrained", "citycar", "domain.pddl")),
        "gridworld": os.path.abspath(os.path.join("plans", "uncostrained", "gridworld", "domain.pddl")),
        "goldminer": os.path.abspath(os.path.join("plans", "uncostrained", "goldminer", "domain.pddl")),
        "sokoban": os.path.abspath(os.path.join("plans", "uncostrained", "sokoban", "domain.pddl"))
    }
    
    domain_file = domain_mapping.get(domain_name)
    if not domain_file or not os.path.exists(domain_file):
        return False

    search = "eager_greedy([ff()], preferred=[ff()])" if domain_name in ["citycar", "sokoban", "goldminer"] else "astar(blind())"
    
    # 1. Solve instance with Fast Downward
    is_solvable, local_plan = verify_feasibility(domain_file, candidate_path, search_config=search, timeout=10)
    
    try:
        if is_solvable and local_plan and os.path.exists(local_plan):
            # 2. Validate standard plan with VAL
            if validate_plan(domain_file, candidate_path, local_plan):
                return save_valid_instance(domain_name, candidate_path, local_plan, problems_dir, plans_dir)
            else:
                print(f"[WARN] Generated plan for {domain_name} is INVALID according to VAL.")
        return False
    finally:
        if local_plan and os.path.exists(local_plan):
            try: os.remove(local_plan)
            except: pass


def _get_random_params(domain_name):
    """Generates the mandatory parameter map from global pools randomly."""
    params = {}
    if domain_name == "gridworld":
        floorplan_options = [item[0] for item in MINIGRID_POOL["floorplans"]]
        floorplan_weights = [item[1] for item in MINIGRID_POOL["floorplans"]]
        params["floorplan"] = random.choices(floorplan_options, weights=floorplan_weights, k=1)[0]
        params["nshapes"] = random.randint(*MINIGRID_POOL["nshapes_range"])
        params["seed"] = random.randint(0, 10**9)
    elif domain_name == "citycar":
        params["rows"] = random.randint(*CITYCAR_POOL["rows_range"])
        params["columns"] = random.randint(*CITYCAR_POOL["cols_range"])
        params["cars"] = random.randint(*CITYCAR_POOL["cars_range"])
        params["garages"] = random.randint(*CITYCAR_POOL["garages_range"])
        params["seed"] = random.randint(0, 10**9)
    elif domain_name == "goldminer":
        params["rows"] = random.randint(*GOLDMINER_POOL["rows_range"])
        params["columns"] = random.randint(*GOLDMINER_POOL["cols_range"])
        params["seed"] = random.randint(0, 10**9)
    elif domain_name == "sokoban":
        params["grid_size"] = random.randint(*SOKOBAN_POOL["grid_size_range"])
        params["boxes"] = random.randint(*SOKOBAN_POOL["boxes_range"])
        params["seed"] = random.randint(0, 10**9)
        params["instance_id"] = 0  
    return params


def _execute_generator(generator: PDDLGenerator, problems_dir, plans_dir):
    try:
        files_before = set(os.listdir(problems_dir))
        generation_params = _get_random_params(generator.domain_name)
        command, is_stdout_mode = generator.get_command_and_mode(generation_params)
        
        seed = generation_params["seed"]
        raw_capture_path = os.path.join(problems_dir, f"temp_{generator.domain_name}_{seed}.pddl")

        if is_stdout_mode:
            with open(raw_capture_path, "w", encoding="utf-8") as out_f:
                subprocess.run(command, check=True, stdout=out_f, stderr=subprocess.PIPE, text=True)
        else:
            subprocess.run(command, check=True, capture_output=True, text=True, cwd=problems_dir)
            
            files_after = set(os.listdir(problems_dir))
            new_files = files_after - files_before
            
            target_file = None
            target_plan = None
            
            for filename in new_files:
                if filename.endswith(".pddl") and filename != "domain.pddl" and not filename.startswith("temp_") and not filename.startswith(f"{generator.domain_name}-"):
                    target_file = os.path.join(problems_dir, filename)
                elif filename.endswith(".plan") and generator.domain_name == "sokoban":
                    target_plan = os.path.join(problems_dir, filename)
            
            # --- Dedicated Sokoban validation branch ---
            if generator.domain_name == "sokoban":
                if target_file and target_plan and os.path.exists(target_file) and os.path.exists(target_plan):
                    
                    # Target domain for Sokoban
                    sokoban_domain = os.path.abspath(os.path.join("plans", "uncostrained", "sokoban", "domain.pddl"))
                    
                    # Validate native Sokoban plan with VAL before proceeding
                    print("[*] Validating native Sokoban plan using VAL...")
                    if validate_plan(sokoban_domain, target_file, target_plan):
                        final_id = rename_problem(generator.domain_name, problems_dir, target_file_path=target_file)
                        
                        if final_id is not None:
                            os.makedirs(plans_dir, exist_ok=True)
                            dest_plan_path = os.path.join(plans_dir, f"{generator.domain_name}-{final_id}.plan")
                            shutil.move(target_plan, dest_plan_path)
                            return True
                    else:
                        print("[WARN] Native Sokoban plan failed VAL verification. Discarding.")
                
                # Cleanup if validation failed or files are missing
                if target_file and os.path.exists(target_file): 
                    try: os.remove(target_file)
                    except: pass
                if target_plan and os.path.exists(target_plan): 
                    try: os.remove(target_plan)
                    except: pass
                return False

        if _verify_and_save(generator.domain_name, raw_capture_path, problems_dir, plans_dir):
            return True
        else:
            if os.path.exists(raw_capture_path): 
                os.remove(raw_capture_path)
            return False

    except subprocess.CalledProcessError:
        if 'raw_capture_path' in locals() and os.path.exists(raw_capture_path): 
            try: os.remove(raw_capture_path)
            except: pass
        return False

def run_generation_loop(generator: PDDLGenerator, problems_dir, plans_dir, count, status_callback=None):
    """Main standalone orchestrator batch function."""
    problems_dir = os.path.abspath(problems_dir)
    plans_dir = os.path.abspath(plans_dir)
    os.makedirs(problems_dir, exist_ok=True)
    
    prefix = f"{generator.domain_name}-"
    files_saved = len([f for f in os.listdir(problems_dir) if f.startswith(prefix) and f.endswith(".pddl")])
    total_target = files_saved + count
    
    if status_callback:
        status_callback("init", {"current": files_saved, "target": total_target})
    
    try:
        while files_saved < total_target:
            if status_callback: status_callback("attempt", None)
            
            success = _execute_generator(generator, problems_dir, plans_dir)
            
            if success:
                files_saved = len([f for f in os.listdir(problems_dir) if f.startswith(prefix) and f.endswith(".pddl")])
                if status_callback: 
                    status_callback("success", {"current": files_saved, "target": total_target})
            else:
                if status_callback: status_callback("failed", None)
                
        if status_callback: status_callback("finished", {"domain": generator.domain_name})
        
    except KeyboardInterrupt:
        if os.path.exists(problems_dir):
            for f in os.listdir(problems_dir):
                if f.startswith("temp_") and f.endswith(".pddl"):
                    try: os.remove(os.path.join(problems_dir, f))
                    except: pass
        if status_callback: status_callback("interrupted", None)
        sys.exit(0)