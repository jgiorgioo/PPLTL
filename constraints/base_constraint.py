import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from pddl.formatter import domain_to_string, problem_to_string
from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser
from pddl.logic.base import And
from pylogics.parsers import parse_pltl
from plan4past.compiler import Compiler

class BaseConstraint(ABC):

    @abstractmethod
    def generate_ltl_rule(self, target_objects: list[str] | str) -> str:
        pass

    @property
    @abstractmethod
    def _target_token_regex(self) -> str:
        pass

    def apply_constraint(self, unconstrained_domain: str, unconstrained_problem: str,output_dir: str, target_objects: list[str] | str) -> bool:
        os.makedirs(output_dir, exist_ok=True)

        if isinstance(target_objects, str):
            target_objects_list = [target_objects]
        else:
            target_objects_list = list(target_objects)
        
        ltl_rule = self.generate_ltl_rule(target_objects_list)

        with open(os.path.join(output_dir, "rule.txt"), "w", encoding="utf-8") as r_file:
            r_file.write(ltl_rule + "\n")
        
        formula_str, constant_list = self._join_goal_and_rule(unconstrained_problem, ltl_rule, target_objects_list)
        
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
            
            domain_str, problem_str = self._execute_cleanup(domain_str, problem_str, constant_list)
            
            with open(os.path.join(output_dir, "domain.pddl"), "w", encoding="utf-8") as d:
                d.write(domain_str)
            with open(os.path.join(output_dir, "problem.pddl"), "w", encoding="utf-8") as p:
                p.write(problem_str)
                
            return True
        except Exception as e:
            print(f"[ERROR {self.__class__.__name__}] Constraint application failed: {e}")
            return False
        
    def _join_goal_and_rule(self, problem_pddl_path: str, ltl_rule_str: str, target_objects: list[str]) -> tuple[str, list[str]]:
        try:
            problem_parser = ProblemParser()
            problem_obj = problem_parser(Path(problem_pddl_path).read_text(encoding="utf-8"))
            
            goal_expr = problem_obj.goal
            atoms = []
            
            if isinstance(goal_expr, And):
                atoms = list(goal_expr.operands)
            else:
                atoms = [goal_expr]
                
            pltl_parts = []
            
            all_constants_to_promote = list(target_objects)
            
            for atom in atoms:
                pred_name = atom.name
                args = [term.name for term in atom.terms]
                
                for arg in args:
                    if arg not in all_constants_to_promote:
                        all_constants_to_promote.append(arg)
                
                if args:
                    formatted_atom = f"{pred_name}_{'_'.join(args)}"
                    pltl_parts.append(formatted_atom)
                else:
                    pltl_parts.append(f"{pred_name}")
                    
            pylogics_goal = " & ".join(pltl_parts)
            combined_formula = f"({pylogics_goal}) & {ltl_rule_str}"
            
            return combined_formula, all_constants_to_promote
            
        except Exception as e:
            print(f"[ERROR {self.__class__.__name__}] AST extraction failed for {problem_pddl_path}: {e}")
            return ltl_rule_str, list(target_objects)
        
    def _execute_cleanup(self, domain_str: str, problem_str: str, constant_list:list) -> tuple[str, str]:

        if not constant_list:
            return domain_str, problem_str
        
        if ":disjunctive-preconditions" not in domain_str:
            domain_str = domain_str.replace(
                ":requirements :conditional-effects :derived-predicates :negative-preconditions :strips",
                ":requirements :conditional-effects :derived-predicates :negative-preconditions :strips :disjunctive-preconditions"
            )
        
        if "(:constants" not in domain_str:
            constants_pddl = f"\n    (:constants {' '.join(constant_list)})"
            req_match = re.search(r'\(:requirements.*?\)', domain_str)
            if req_match:
                end_req_idx = req_match.end()
                domain_str = domain_str[:end_req_idx] + constants_pddl + domain_str[end_req_idx:]
        
        def clean_objects_block(match):
            objects_text = match.group(1)
            for token in constant_list:
                objects_text = re.sub(r'\b' + token + r'\b', '', objects_text)
            return f"(:objects {re.sub(r'\s+', ' ', objects_text).strip()})"
        
        problem_str = re.sub(r'\(:objects\s+(.*?)\)', clean_objects_block, problem_str)
        return domain_str, problem_str