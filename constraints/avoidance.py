import os
from abc import ABC, abstractmethod
from pathlib import Path
from pddl.formatter import domain_to_string, problem_to_string
from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser
from pylogics.parsers import parse_pltl
from plan4past.compiler import Compiler
from util import join_goal_and_rule

class BaseAvoidance(ABC):
    """
    Classe astratta che gestisce l'infrastruttura di compilazione di Plan4Past.
    Le sottoclassi devono solo implementare la generazione della regola LTL specifica.
    """
    
    @abstractmethod
    def generate_avoid_rule(self, target_object) -> str:
        """Ritorna la stringa della regola LTL (es: 'H(~at-robot(place_1_1))')"""
        pass

    def apply_avoidance(self, unconstrained_domain, unconstrained_problem, target_object, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
        regola_avoid = self.generate_avoid_rule(target_object)
        
        formula_str = join_goal_and_rule(unconstrained_problem, regola_avoid)
        
        compiled_domain_path = os.path.join(output_dir, "test_avoid_domain.pddl")
        compiled_problem_path = os.path.join(output_dir, "test_avoid_prob.pddl")
        
        try:
            domain_parser = DomainParser()
            problem_parser = ProblemParser()
            
            domain_obj = domain_parser(Path(unconstrained_domain).read_text(encoding="utf-8"))
            problem_obj = problem_parser(Path(unconstrained_problem).read_text(encoding="utf-8"))
            
            goal_formula = parse_pltl(formula_str)
            compiler = Compiler(domain_obj, problem_obj, goal_formula)
            compiler.compile()
            compiled_domain, compiled_problem = compiler.result
            
            with open(compiled_domain_path, "w", encoding="utf-8") as d:
                d.write(domain_to_string(compiled_domain))
            with open(compiled_problem_path, "w", encoding="utf-8") as p:
                f_p = problem_to_string(compiled_problem)
                p.write(f_p)
                
            return True
            
        except Exception as e:
            print(f"[ERROR avoidance] Plan4Past compilation failed: {e}")
            return False


class AvoidanceGridworld(BaseAvoidance):
    
    def generate_avoid_rule(self, avoid_cell) -> str:
        return f"H(~at-robot({avoid_cell}))"
    
