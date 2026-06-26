import os
import subprocess
from generation.generators import PDDLGenerator
from utils import verify_validate_and_save, save_valid_instance, run_generic_pipeline_loop, validate_plan 

class GeneratorsManager:
    """
    Pure Controller (MVC): coordinates CLI generator execution and base instance validation,
    completely decoupling core logic from view printing or log messages.
    """
    def __init__(self, domain_mapping: dict):
        self.domain_mapping = domain_mapping

    def execute_generator(self, generator: PDDLGenerator) -> bool:
        raw_capture_path = None
        target_file = None
        target_plan = None
        p_dir = generator.problems_dir
        
        try:
            # Track existing files before execution to catch new asynchronous outputs
            files_before = set(os.listdir(p_dir))
            command, is_stdout_mode, seed = generator.prepare_execution()
            raw_capture_path = os.path.join(p_dir, f"temp_{generator.domain_name}_{seed}.pddl")

            if is_stdout_mode:
                # Subprocess execution for stdout-based generators (e.g., Goldminer)
                with open(raw_capture_path, "w", encoding="utf-8") as out_f:
                    subprocess.run(command, check=True, stdout=out_f, stderr=subprocess.PIPE, text=True)
            else:
                # Subprocess execution for file-writing generators (e.g., MiniGrid, Sokoban)
                subprocess.run(command, check=True, capture_output=True, text=True, cwd=p_dir)
                
                # Identify newly created files on the disk
                new_files = set(os.listdir(p_dir)) - files_before
                for filename in new_files:
                    if filename.endswith(".pddl") and filename != "domain.pddl" and not filename.startswith("temp_") and not filename.startswith(f"{generator.domain_name}-"):
                        target_file = os.path.join(p_dir, filename)
                    elif filename.endswith(".plan") and generator.domain_name == "sokoban":
                        target_plan = os.path.join(p_dir, filename)
                
                # SOKOBAN BRANCH: The generator natively outputs a valid plan.
                # We skip the external planner invocation and validate the native plan directly.
                if generator.domain_name == "sokoban":
                    if target_file and target_plan and os.path.exists(target_file) and os.path.exists(target_plan):
                        sokoban_domain = self.domain_mapping.get("sokoban")
                        if validate_plan(sokoban_domain, target_file, target_plan):
                            return save_valid_instance("sokoban", target_file, target_plan, p_dir, generator.plans_dir)
                    
                    # Immediate physical cleanup on validation failure
                    for f in [target_file, target_plan]:
                        if f and os.path.exists(f):
                            try: os.remove(f)
                            except: pass
                    return False
                
            actual_problem_path = raw_capture_path if is_stdout_mode else target_file
            if not actual_problem_path or not os.path.exists(actual_problem_path):
                return False

            # Strategy callback to delegate the final renaming and saving workflow
            save_strategy = lambda plan_path: save_valid_instance(
                domain_name=generator.domain_name,
                candidate_path=actual_problem_path,
                local_plan=plan_path,
                problems_dir=p_dir,
                plans_dir=generator.plans_dir
            )

            # Standard external planner validation loop (used for Gridworld and Goldminer)
            success = verify_validate_and_save(
                domain_name=generator.domain_name,
                domain_mapping=self.domain_mapping,
                problem_path=actual_problem_path,
                save_callback=save_strategy,
                timeout=15
            )

            if not success and os.path.exists(actual_problem_path):
                try: os.remove(actual_problem_path)
                except Exception: pass

            return success
     
        except subprocess.CalledProcessError:
            for f in [raw_capture_path, target_file]:
                if f and os.path.exists(f):
                    try: os.remove(f)
                    except: pass
            return False

    def run_loop(self, generator: PDDLGenerator, count: int, status_callback=None):
        """Runs the generation loop by delegating execution flow control to the generic utility function."""
        atomic_pipeline = lambda: self.execute_generator(generator)
        run_generic_pipeline_loop(
            target_dir=generator.problems_dir,
            file_prefix=f"{generator.domain_name}-",
            count=count,
            pipeline_func=atomic_pipeline,
            status_callback=status_callback
        )