import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from pddl.formatter import domain_to_string, problem_to_string
from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser
from pylogics.parsers import parse_pltl
from plan4past.compiler import Compiler
from util import join_goal_and_rule

class BaseAvoidance(ABC):
    
    @abstractmethod
    def generate_avoid_rule(self, target_object) -> str:
        pass

    @abstractmethod
    def _normalize_formula_for_pylogics(self, formula_str: str) -> str:
        pass

    def apply_avoidance(self, unconstrained_domain, unconstrained_problem, target_object, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
        avoid_rule = self.generate_avoid_rule(target_object)
        formula_str = join_goal_and_rule(unconstrained_problem, avoid_rule)
        
        formula_str = self._normalize_formula_for_pylogics(formula_str)
        print(f"[DEBUG NORMALIZZATO] Formula pulita per pylogics: {formula_str}")
        
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
            
            domain_str = domain_to_string(compiled_domain)
            problem_str = problem_to_string(compiled_problem)
            
            if hasattr(self, "_cleanup_compiled_pddl"):
                domain_str, problem_str = self._cleanup_compiled_pddl(domain_str, problem_str, target_object, formula_str)
            
            with open(compiled_domain_path, "w", encoding="utf-8") as d:
                d.write(domain_str)
            with open(compiled_problem_path, "w", encoding="utf-8") as p:
                p.write(problem_str)
                
            return True
            
        except Exception as e:
            print(f"[ERROR avoidance] Plan4Past compilation failed: {e}")
            return False


class AvoidanceGridworld(BaseAvoidance):
    
    def generate_avoid_rule(self, avoid_cell) -> str:
        return f"!O(at-robot_{avoid_cell})"
    
    def _normalize_formula_for_pylogics(self, formula_str: str) -> str:
        # Trasforma at-robot(p67) in at-robot_p67 specifico per le celle di Gridworld
        return re.sub(r'([a-zA-Z0-9_-]+)\((p[0-9]+)\)', r'\1_\2', formula_str)
    
    def _cleanup_compiled_pddl(self, domain_str: str, problem_str: str, target_object: str, formula_str: str) -> tuple[str, str]:
        # Estrae dinamicamente tutte le celle (es: p46, p67) dalla formula per isolarle
        cells_to_isolate = list(set(re.findall(r'p[0-9]+', formula_str)))
        print(f"[CLEANUP] Celle rilevate da convertire in costanti: {cells_to_isolate}")
        
        # 1. Iniezione dei requisiti mancanti nel dominio
        if ":disjunctive-preconditions" not in domain_str:
            domain_str = domain_str.replace(
                ":requirements :conditional-effects :derived-predicates :negative-preconditions :strips",
                ":requirements :conditional-effects :derived-predicates :negative-preconditions :strips :disjunctive-preconditions"
            )
        
        # 2. Iniezione del blocco (:constants ...) nel dominio subito dopo i requisiti
        if cells_to_isolate and "(:constants" not in domain_str:
            constants_pddl = f"\n    (:constants {' '.join(cells_to_isolate)})"
            req_match = re.search(r'\(:requirements.*?\)', domain_str)
            if req_match:
                end_req_idx = req_match.end()
                domain_str = domain_str[:end_req_idx] + constants_pddl + domain_str[end_req_idx:]
        
        # 3. Rimozione sicura dei duplicati dal blocco (:objects ...) del problema
        def clean_objects_block(match):
            objects_text = match.group(1)
            for cell in cells_to_isolate:
                objects_text = re.sub(r'\b' + cell + r'\b', '', objects_text)
            objects_text = re.sub(r'\s+', ' ', objects_text).strip()
            return f"(:objects {objects_text})"
        
        problem_str = re.sub(r'\(:objects\s+(.*?)\)', clean_objects_block, problem_str)
        
        return domain_str, problem_str
    