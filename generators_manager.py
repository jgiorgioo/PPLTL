import os
import subprocess
from generators import PDDLGenerator
from utils import verify_validate_and_save, save_valid_instance, run_generic_pipeline_loop, validate_plan 

class GeneratorsManager:
    """Orchestratore ad oggetti puro per la generazione e validazione di istanze base."""
    def __init__(self, domain_mapping: dict):
        self.domain_mapping = domain_mapping

    def execute_generator(self, generator: PDDLGenerator) -> bool:
        raw_capture_path = None
        target_file = None
        target_plan = None
        
        p_dir = generator.problems_dir
        path_seed = None
        
        try:
            files_before = set(os.listdir(p_dir))
            
            # Polimorfismo puro: il manager delega interamente la configurazione
            command, is_stdout_mode, seed = generator.prepare_execution()
            raw_capture_path = os.path.join(p_dir, f"temp_{generator.domain_name}_{seed}.pddl")

            if is_stdout_mode:
                with open(raw_capture_path, "w", encoding="utf-8") as out_f:
                    subprocess.run(command, check=True, stdout=out_f, stderr=subprocess.PIPE, text=True)
            else:
                subprocess.run(command, check=True, capture_output=True, text=True, cwd=p_dir)
                
                new_files = set(os.listdir(p_dir)) - files_before
                for filename in new_files:
                    if filename.endswith(".pddl") and filename != "domain.pddl" and not filename.startswith("temp_") and not filename.startswith(f"{generator.domain_name}-"):
                        target_file = os.path.join(p_dir, filename)
                    elif filename.endswith(".plan") and generator.domain_name == "sokoban":
                        target_plan = os.path.join(p_dir, filename)
                
                # Ramo Sokoban protetto
                if generator.domain_name == "sokoban":
                    if target_file and target_plan and os.path.exists(target_file) and os.path.exists(target_plan):
                        sokoban_domain = self.domain_mapping.get("sokoban")
                        if validate_plan(sokoban_domain, target_file, target_plan):
                            return save_valid_instance("sokoban", target_file, target_plan, p_dir, generator.plans_dir)
                    
                    for f in [target_file, target_plan]:
                        if f and os.path.exists(f):
                            try: os.remove(f)
                            except: pass
                    return False
                
            actual_problem_path = raw_capture_path if is_stdout_mode else target_file

            if not actual_problem_path or not os.path.exists(actual_problem_path):
                return False

            save_strategy = lambda plan_path: save_valid_instance(
                domain_name=generator.domain_name,
                candidate_path=actual_problem_path,
                local_plan=plan_path,
                problems_dir=p_dir,
                plans_dir=generator.plans_dir
            )

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
        atomic_pipeline = lambda: self.execute_generator(generator)
        run_generic_pipeline_loop(
            target_dir=generator.problems_dir,
            file_prefix=f"{generator.domain_name}-",
            count=count,
            pipeline_func=atomic_pipeline,
            status_callback=status_callback
        )