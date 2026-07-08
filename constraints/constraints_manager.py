import os
import tempfile
import shutil
from .domain_constraints import get_domain_constraint
from .target_sampler import TargetSampler
from .problem_sampler import ProblemSampler
from utils import run_generic_pipeline_loop, verify_validate_and_save, save_constrained_instance

class ConstraintManager:
    """Coordinates the selection of unconstrained instances and applies LTL constraints to them."""
    def __init__(self, domain: str, constraint: str, unconstrained_mapping: dict, constrained_mapping: dict):
        self.domain = domain
        self.constraint_name = constraint
        # Injected mappings dynamically from the main interface
        self.unconstrained_dir = unconstrained_mapping.get(domain)
        self.constrained_dir = constrained_mapping.get(domain)
        self.constraint_processor = get_domain_constraint(domain, constraint)

    def execute_pipeline(self, problem_file_name: str) -> bool:
        """Runs the compile-validate-save sequence on a selected unconstrained PDDL problem."""
        try:
            unconstrained_problem_path = os.path.join(self.unconstrained_dir, problem_file_name)
            stratum_folder = os.path.dirname(problem_file_name)  
            pure_file_name = os.path.basename(problem_file_name)  
            unconstrained_domain_path = os.path.join(self.unconstrained_dir, "domain.pddl")
            
            # Locate the baseline plan file companion
            plan_file_name = pure_file_name.replace(".pddl", ".plan")
            flat_plan_path = os.path.join(self.unconstrained_dir, stratum_folder, "solutions", plan_file_name)
            
            if not os.path.exists(flat_plan_path):
                return False
                
            # Instantiate the stateful sampler for target objects/tuples
            sampler = TargetSampler(
                domain=self.domain,
                constraint_name=self.constraint_name,
                plan_path=flat_plan_path,
                problem_path=unconstrained_problem_path
            )

            return self._explore_candidates_until_solvable(
                sampler=sampler,
                unconstrained_domain_path=unconstrained_domain_path,
                unconstrained_problem_path=unconstrained_problem_path
            )
        except Exception:
            return False

    def _explore_candidates_until_solvable(self, sampler: TargetSampler, unconstrained_domain_path: str, unconstrained_problem_path: str) -> bool:
        """Iterates through LTL target candidates until a solvable compiled domain-problem pair is found."""
        attempts_count = 0
        max_attempts = 20
        
        while sampler.has_candidates() and attempts_count < max_attempts:
            attempts_count += 1
            target_object = sampler.sample_next_target()

            # Create an isolated, secure temporary directory that auto-deletes on exit
            with tempfile.TemporaryDirectory(prefix=f"pddl_constraint_{self.domain}_") as temp_out_dir:
                
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

                # Validate using the external automated planner pipeline
                success = verify_validate_and_save(
                    domain_name=self.domain,
                    domain_mapping={self.domain: compiled_domain},
                    problem_path=compiled_problem,
                    save_callback=save_strategy,
                    timeout=20
                )
                
                if success:
                    return True
                
                sampler.mark_as_failed(target_object)
                    
        return False

    def run_loop(self, count: int, status_callback=None):
        """Launches the shared pipeline loop with an atomic execution function wrapper."""
        destination_dir = os.path.join(self.constrained_dir, self.constraint_name)

        problem_sampler = ProblemSampler(
            unconstrained_base_dir=self.unconstrained_dir,
            domain_name=self.domain
        )
        
        def atomic_pipeline():
            if not problem_sampler.has_problems():
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