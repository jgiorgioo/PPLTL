import os
import subprocess
import tempfile
from generation.generators import PDDLGenerator
from utils import verify_validate_and_save, save_valid_instance, run_generic_pipeline_loop, validate_plan 

class GeneratorsManager:
    """
    Controller class that coordinates execution and validation of PDDL generators.
    Built for secure, isolated temporary workspace execution using external domain mapping.
    """
    def __init__(self, domain_mapping: dict):
        self.domain_mapping = domain_mapping

    def execute_generator(self, generator: PDDLGenerator) -> bool:
        try:
            command, is_stdout_mode, seed = generator.prepare_execution()
            
            p_dir = generator.get_problems_dir()
            plans_dir = generator.get_plans_dir()
            sampled_stratum = generator.get_current_stratum()
            current_domain_path = self.domain_mapping.get(generator.domain_name)

            # Create an isolated temporary directory inside the system's /tmp
            with tempfile.TemporaryDirectory(prefix=f"pddl_gen_{generator.domain_name}_") as temp_workspace:
                
                # Path where the temporary problem file will be
                temp_target_file = os.path.join(temp_workspace, f"problem_{seed}.pddl")

                if is_stdout_mode:
                    # Direct stream capturing (Goldminer) directly into the secure temp file
                    with open(temp_target_file, "w", encoding="utf-8") as out_f:
                        subprocess.run(command, check=True, stdout=out_f, stderr=subprocess.PIPE, text=True)
                else:
                    # Local workspace capturing (MiniGrid, Sokoban)
                    # We make the generator write INSIDE the isolated temp directory
                    subprocess.run(command, check=True, capture_output=True, text=True, cwd=temp_workspace)
                    
                    # Scan the isolated temp directory to find what it generated
                    generated_files = os.listdir(temp_workspace)
                    
                    pddl_candidates = [f for f in generated_files if f.endswith(".pddl") and f != "domain.pddl"]
                    if not pddl_candidates:
                        return False
                    
                    # Remap the target file inside our secure temp workspace
                    temp_target_file = os.path.join(temp_workspace, pddl_candidates[0])

                    # Specialized path for Sokoban natively embedded plans
                    if generator.domain_name == "sokoban":
                        plan_candidates = [f for f in generated_files if f.endswith(".plan")]
                        if plan_candidates:
                            temp_target_plan = os.path.join(temp_workspace, plan_candidates[0])
                            
                            # Validate the plan while it is still inside the temp folder
                            if validate_plan(current_domain_path, temp_target_file, temp_target_plan):
                                # Ensure the target stratum directories exist right before moving the file
                                os.makedirs(plans_dir, exist_ok=True)
                                return save_valid_instance("sokoban", temp_target_file, temp_target_plan, p_dir, plans_dir, stratum=sampled_stratum)
                        return False
                
                # Absolute safety check: if the generator didn't produce the file, stop immediately
                if not os.path.exists(temp_target_file):
                    return False

                def save_strategy(plan_path):
                    return save_valid_instance(
                        domain_name=generator.domain_name,
                        candidate_path=temp_target_file,
                        local_plan=plan_path,
                        problems_dir=p_dir,
                        plans_dir=plans_dir,
                        stratum=sampled_stratum
                    )

                os.makedirs(plans_dir, exist_ok=True)

                # Standard external planner verification loop
                success = verify_validate_and_save(
                    domain_name=generator.domain_name,
                    domain_mapping=self.domain_mapping, # Pass your original mapping object cleanly
                    problem_path=temp_target_file,
                    save_callback=save_strategy,
                    timeout=15
                )

                return success
     
        except (subprocess.CalledProcessError, Exception):
            # Safe and automatic cleanup of the /tmp workspace via tempfile context manager
            return False

    def run_loop(self, generator: PDDLGenerator, count: int, status_callback=None):
        """Runs the generation loop via the generic utility function."""
        domain_base_dir = os.path.join(generator.base_dir, generator.domain_name)
        atomic_pipeline = lambda: self.execute_generator(generator)
        
        run_generic_pipeline_loop(
            target_dir=domain_base_dir,
            file_prefix=f"{generator.domain_name}-",
            count=count,
            pipeline_func=atomic_pipeline,
            status_callback=status_callback
        )