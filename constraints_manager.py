import os
import re
import random
import shutil
from utils import TargetSampler
from utils import run_generic_pipeline_loop, verify_validate_and_save, save_constrained_instance

UNCONSTRAINED_MAP = {
    "gridworld": os.path.abspath(os.path.join("plans", "uncostrained", "gridworld")),
    "goldminer": os.path.abspath(os.path.join("plans", "uncostrained", "goldminer")),
    "sokoban": os.path.abspath(os.path.join("plans", "uncostrained", "sokoban"))
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
        self.constraint_processor = self._get_constraint(domain, constraint)

    def _get_constraint(self, domain: str, constraint: str):
        if domain == "gridworld":
            from constraints import get_gridworld_constraint
            return get_gridworld_constraint(constraint)
        elif domain == "sokoban":
            pass
        elif domain == "goldminer":
            from constraints import get_goldminer_constraint
            return get_goldminer_constraint(constraint)
        else:
            raise NotImplementedError(f"Domain '{domain}' is not supported.")

    def execute_pipeline(self, problem_file_name: str) -> bool:
        unconstrained_domain_path = os.path.join(self.unconstrained_dir, "domain.pddl")
        unconstrained_problem_path = os.path.join(self.unconstrained_dir, problem_file_name)
        
        idx_match = re.search(r'-([0-9]+)\.pddl$', problem_file_name)
        instance_idx = idx_match.group(1) if idx_match else "0"

        flat_plan_path = os.path.join(self.unconstrained_dir, "solutions", f"{self.domain}-{instance_idx}.plan")
        
        if not os.path.exists(flat_plan_path):
            print(f"[WARN] Baseline plan missing for {problem_file_name}. Skipping.")
            return False
            
        # 1. Istanziamo il Sampler (che internamente gestirà la sua blacklist)
        sampler = TargetSampler(
            domain=self.domain,
            constraint_name=self.constraint_name,
            plan_path=flat_plan_path,
            problem_path=unconstrained_problem_path
        )

        # 2. Passiamo il sampler al gestore dell'esplorazione
        return self._explore_candidates_until_solvable(
            sampler=sampler,
            instance_idx=instance_idx,
            unconstrained_domain_path=unconstrained_domain_path,
            unconstrained_problem_path=unconstrained_problem_path,
            problem_file_name=problem_file_name
        )

    def _explore_candidates_until_solvable(self, sampler: TargetSampler, instance_idx: str, unconstrained_domain_path: str, unconstrained_problem_path: str, problem_file_name: str) -> bool:
        attempts_count = 0
        max_attempts = 20
        
        while sampler.has_candidates() and attempts_count < max_attempts:
            attempts_count += 1
            
            target_object = sampler.sample_next_target()
            
            print(f"[INFO] [Attempt {attempts_count}/{max_attempts}] Testing target '{target_object}' on instance {self.domain}-{instance_idx}...")

            temp_out_dir = os.path.join(self.constrained_dir, self.constraint_name, f"temp_run_{instance_idx}")
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
                    print(f"[WARN] Target '{target_object}' led to an unsolvable problem. Blacklisting and trying next...")
                    # Aggiorniamo la blacklist del sampler così il prossimo giro sa cosa evitare
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
        
        def atomic_pipeline():
            all_problems = [
                f for f in os.listdir(self.unconstrained_dir) 
                if f.startswith(f"{self.domain}-") and f.endswith(".pddl")
            ]
            if not all_problems:
                print(f"[ERROR] No unconstrained problems found in {self.unconstrained_dir}")
                return False
            
            chosen_problem_file = random.choice(all_problems)
            return self.execute_pipeline(chosen_problem_file)

        run_generic_pipeline_loop(
            target_dir=destination_dir,
            file_prefix=f"{self.domain}-",
            count=count,
            pipeline_func=atomic_pipeline,
            status_callback=status_callback
        )