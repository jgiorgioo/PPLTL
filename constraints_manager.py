# constraints/base_constraint_manager.py
import os
import random
from abc import ABC, abstractmethod
from util import run_generic_pipeline_loop

# Centralized path mappings owned directly by the constraints module
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

class BaseConstraintManager(ABC):
    def __init__(self, domain: str, constraint: str):
        self.domain = domain
        self.constraint = constraint
        # Read paths dynamically from the centralized module maps
        self.unconstrained_dir = UNCONSTRAINED_MAP.get(domain)
        self.constrained_dir = CONSTRAINED_MAP.get(domain)

    @abstractmethod
    def execute_pipeline(self, problem_file_name: str) -> bool:
        """To be implemented by specific constraint sub-classes."""
        pass

    def run_loop(self, count: int, status_callback=None):
        """Orchestrates LTL compilation batch loop without duplicating cycle logic."""
        destination_dir = os.path.join(self.constrained_dir, self.constraint)
        
        def atomic_pipeline():
            # Scan the unconstrained folder for source flat problems
            all_problems = [
                f for f in os.listdir(self.unconstrained_dir) 
                if f.startswith(f"{self.domain}-") and f.endswith(".pddl")
            ]
            if not all_problems:
                print(f"[ERROR] No unconstrained problems found in {self.unconstrained_dir}")
                return False
            
            # Select an instance randomly at each iteration step
            chosen_problem_file = random.choice(all_problems)
            return self.execute_pipeline(chosen_problem_file)

        # Fire the universal engine
        run_generic_pipeline_loop(
            target_dir=destination_dir,
            file_prefix=f"{self.domain}-",
            count=count,
            pipeline_func=atomic_pipeline,
            status_callback=status_callback
        )