import os
import sys
import random
import subprocess
import shutil
from generators import PDDLGenerator
from utils import verify_validate_and_save, save_valid_instance, run_generic_pipeline_loop
from utils import validate_plan 

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

GOLDMINER_POOL = {
    "rows_range": (5, 10),
    "cols_range": (5, 10)
}

SOKOBAN_POOL = {
    "grid_size_range": (5, 10),
    "boxes_range": (2, 5)
} 

domain_mapping = {
        "gridworld": os.path.abspath(os.path.join("plans", "uncostrained", "gridworld", "domain.pddl")),
        "goldminer": os.path.abspath(os.path.join("plans", "uncostrained", "goldminer", "domain.pddl")),
        "sokoban": os.path.abspath(os.path.join("plans", "uncostrained", "sokoban", "domain.pddl"))
    }
    

def _get_random_params(domain_name):
    """Generates the mandatory parameter map from global pools randomly."""
    params = {}
    if domain_name == "gridworld":
        floorplan_options = [item[0] for item in MINIGRID_POOL["floorplans"]]
        floorplan_weights = [item[1] for item in MINIGRID_POOL["floorplans"]]
        params["floorplan"] = random.choices(floorplan_options, weights=floorplan_weights, k=1)[0]
        params["nshapes"] = random.randint(*MINIGRID_POOL["nshapes_range"])
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


def _execute_generator(generator: PDDLGenerator, domain_mapping, problems_dir, plans_dir):
    raw_capture_path = None
    target_file = None
    
    try:
        files_before = set(os.listdir(problems_dir))
        generation_params = _get_random_params(generator.domain_name)
        command, is_stdout_mode = generator.get_command_and_mode(generation_params)
        
        seed = generation_params["seed"]
        raw_capture_path = os.path.join(problems_dir, f"temp_{generator.domain_name}_{seed}.pddl")

        # Execute the binary using either stdout redirection or working directory generation
        if is_stdout_mode:
            with open(raw_capture_path, "w", encoding="utf-8") as out_f:
                subprocess.run(command, check=True, stdout=out_f, stderr=subprocess.PIPE, text=True)
        else:
            subprocess.run(command, check=True, capture_output=True, text=True, cwd=problems_dir)
            
            # Detect the newly created files written directly to disk by the generator binary
            files_after = set(os.listdir(problems_dir))
            new_files = files_after - files_before
            
            for filename in new_files:
                if filename.endswith(".pddl") and filename != "domain.pddl" and not filename.startswith("temp_") and not filename.startswith(f"{generator.domain_name}-"):
                    target_file = os.path.join(problems_dir, filename)
                elif filename.endswith(".plan") and generator.domain_name == "sokoban":
                    target_plan = os.path.join(problems_dir, filename)
            
            # --- Dedicated Sokoban validation branch ---
            if generator.domain_name == "sokoban":
                if target_file and target_plan and os.path.exists(target_file) and os.path.exists(target_plan):
                    sokoban_domain = domain_mapping.get("sokoban")
                    print("[*] Validating native Sokoban plan using VAL...")
                    
                    if validate_plan(sokoban_domain, target_file, target_plan):
                        success_save = save_valid_instance(
                            domain_name="sokoban",
                            candidate_path=target_file,
                            local_plan=target_plan,
                            problems_dir=problems_dir,
                            plans_dir=plans_dir
                        )
                        return success_save
                    else:
                        print("[WARN] Native Sokoban plan failed VAL verification. Discarding.")
                
                # Immediate localized cleanup for Sokoban files if validation fails
                if target_file and os.path.exists(target_file): 
                    try: os.remove(target_file)
                    except: pass
                if target_plan and os.path.exists(target_plan): 
                    try: os.remove(target_plan)
                    except: pass
                return False
            
        # Determine the definitive location of the generated raw problem file
        actual_problem_path = raw_capture_path if is_stdout_mode else target_file

        # Centralized guard clause verifying the existence of the generated file
        if not actual_problem_path or not os.path.exists(actual_problem_path):
            print(f"[ERROR] PDDL instance file not found at: {actual_problem_path}")
            return False

        # Package local storage parameters into a single-argument callback strategy via lambda
        save_strategy = lambda plan_path: save_valid_instance(
            domain_name=generator.domain_name,
            candidate_path=actual_problem_path,
            local_plan=plan_path,
            problems_dir=problems_dir,
            plans_dir=plans_dir
        )

        # Delegate planning, plan verification, and persistent saving to the unified engine
        success = verify_validate_and_save(
            domain_name=generator.domain_name,
            domain_mapping=domain_mapping,
            problem_path=actual_problem_path,
            save_callback=save_strategy,
            timeout=15
        )

        # Wipe the unvalidated problem file from disk if the centralized planning process fails
        if not success:
            try: os.remove(actual_problem_path)
            except Exception: pass

        return success
 
    except subprocess.CalledProcessError:
        # Centralized fallback cleanup if the external generator binary crashes before actual_problem_path is set
        if raw_capture_path and os.path.exists(raw_capture_path): 
            try: os.remove(raw_capture_path)
            except: pass
        if target_file and os.path.exists(target_file):
            try: os.remove(target_file)
            except: pass
        return False

def run_generation_loop(generator: PDDLGenerator, problems_dir, plans_dir, count, status_callback=None):
    """Main standalone orchestrator batch function."""
    atomic_pipeline = lambda: _execute_generator(generator, domain_mapping, problems_dir, plans_dir)
    
    run_generic_pipeline_loop(
        target_dir=problems_dir,
        file_prefix=f"{generator.domain_name}-",
        count=count,
        pipeline_func=atomic_pipeline,
        status_callback=status_callback
    )