import os
import shutil
from .domain_constraints import get_domain_constraint
from .target_sampler import TargetSampler
from .problem_sampler import ProblemSampler
from utils import run_generic_pipeline_loop, verify_validate_and_save, save_constrained_instance

UNCONSTRAINED_MAP = {
    "gridworld": os.path.abspath(os.path.join("plans", "unconstrained", "gridworld")),
    "goldminer": os.path.abspath(os.path.join("plans", "unconstrained", "goldminer")),
    "sokoban": os.path.abspath(os.path.join("plans", "unconstrained", "sokoban"))
}

CONSTRAINED_MAP = {
    "gridworld": os.path.abspath(os.path.join("plans", "constrained", "gridworld")),
    "goldminer": os.path.abspath(os.path.join("plans", "constrained", "goldminer")),
    "sokoban": os.path.abspath(os.path.join("plans", "constrained", "sokoban"))
}

class ConstraintManager:

    def __init__(self, domain: str, constraint: str):
        self.domain = domain
        self.constraint_name = constraint
        self.unconstrained_dir = UNCONSTRAINED_MAP.get(domain)
        self.constrained_dir = CONSTRAINED_MAP.get(domain)
        self.constraint_processor = get_domain_constraint(domain, constraint)

    def execute_pipeline(self, problem_file_name: str) -> bool:
        unconstrained_problem_path = os.path.join(self.unconstrained_dir, problem_file_name)
        stratum_folder = os.path.dirname(problem_file_name)  
        pure_file_name = os.path.basename(problem_file_name)  
        unconstrained_domain_path = os.path.join(self.unconstrained_dir, "domain.pddl")
        
        # Dead simple extension swap to find the plan file
        plan_file_name = pure_file_name.replace(".pddl", ".plan")
        flat_plan_path = os.path.join(self.unconstrained_dir, stratum_folder, "solutions", plan_file_name)
        
        if not os.path.exists(flat_plan_path):
            print(f"[WARN] Baseline plan missing for {pure_file_name} at {flat_plan_path}. Skipping.")
            return False
            
        # 1. Instantiate the TargetSampler
        sampler = TargetSampler(
            domain=self.domain,
            constraint_name=self.constraint_name,
            plan_path=flat_plan_path,
            problem_path=unconstrained_problem_path
        )

        # 2. Hand over to exploration directly passing pure_file_name
        return self._explore_candidates_until_solvable(
            sampler=sampler,
            unconstrained_domain_path=unconstrained_domain_path,
            unconstrained_problem_path=unconstrained_problem_path,
            problem_file_name=pure_file_name
        )


    def _explore_candidates_until_solvable(self, sampler: TargetSampler, unconstrained_domain_path: str, unconstrained_problem_path: str, problem_file_name: str) -> bool:
        attempts_count = 0
        max_attempts = 20
        
        while sampler.has_candidates() and attempts_count < max_attempts:
            attempts_count += 1
            
            target_object = sampler.sample_next_target()
            print(f"[INFO] [Attempt {attempts_count}/{max_attempts}] Testing target '{target_object}' on {problem_file_name}...")

            # Clean and static temporary folder name
            temp_out_dir = os.path.join(self.constrained_dir, self.constraint_name, "temp_run")
            os.makedirs(temp_out_dir, exist_ok=True)
            
            try:
                compilation_success = self.constraint_processor.apply_constraint(
                    unconstrained_domain_path,
                    unconstrained_problem_path,
                    temp_out_dir,
                    target_object
                )
                
                if not compilation_success:
                    sampler.mark_as_failed(target_object)
                    continue

                compiled_domain = os.path.join(temp_out_dir, "domain.pddl")
                compiled_problem = os.path.join(temp_out_dir, "problem.pddl")
                compiled_rule = os.path.join(temp_out_dir, "rule.txt")
                base_constrained_dir = os.path.join(self.constrained_dir, self.constraint_name)

                def save_strategy(final_plan_path: str):
                    return save_constrained_instance(
                        domain_name=self.domain,
                        temp_domain_path=compiled_domain,
                        temp_problem_path=compiled_problem,
                        local_plan=final_plan_path,
                        base_constrained_dir=base_constrained_dir,
                        temp_rule_path=compiled_rule,
                        constraint_name=self.constraint_name
                    )

                success = verify_validate_and_save(
                    domain_name=self.domain,
                    domain_mapping={self.domain: compiled_domain},
                    problem_path=compiled_problem,
                    save_callback=save_strategy,
                    timeout=20
                )
                
                if success:
                    print(f"[SUCCESS] Solvable target found: '{target_object}' for {problem_file_name}!")
                    return True
                else:
                    print(f"[WARN] Target '{target_object}' led to an unsolvable problem. Blacklisting...")
                    sampler.mark_as_failed(target_object)

            finally:
                if os.path.exists(temp_out_dir):
                    shutil.rmtree(temp_out_dir, ignore_errors=True)

        if attempts_count >= max_attempts:
            print(f"[INFO] Reached maximum limit of {max_attempts} attempts for {problem_file_name}.")
        else:
            print(f"[INFO] All available candidates exhausted for {problem_file_name} without any valid solution.")
            
        return False

    def run_loop(self, count: int, status_callback=None):
        destination_dir = os.path.join(self.constrained_dir, self.constraint_name)

        problem_sampler = ProblemSampler(
            unconstrained_base_dir=self.unconstrained_dir,
            domain_name=self.domain
        )
        
        def atomic_pipeline():
            if not problem_sampler.has_problems():
                print(f"[ERROR] No valid problems or stratums found on disk for {self.unconstrained_dir}")
                return False
            
            problem_path = problem_sampler.sample_next_problem()
            full_problem_path = os.path.relpath(problem_path, self.unconstrained_dir)
            
            return self.execute_pipeline(full_problem_path)
        
        run_generic_pipeline_loop(
            target_dir=destination_dir,
            file_prefix=f"{self.domain}-",
            count=count,
            pipeline_func=atomic_pipeline,
            status_callback=status_callback
        )