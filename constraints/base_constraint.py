import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from pddl.formatter import domain_to_string, problem_to_string
from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser
from pddl.logic.base import And
from plan4past.compiler import Compiler
from pylogics.parsers import parse_pltl

class BaseConstraint(ABC):

    @abstractmethod
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        """Generates the domain-specific LTL rule based on target objects."""
        pass

    def apply_constraint(self, unconstrained_domain: str, unconstrained_problem: str, output_dir: str, target_objects: any) -> bool:
        """Compiles the LTL constraint into the PDDL domain and problem files."""
        os.makedirs(output_dir, exist_ok=True)

        # Standardize input targets into a flat list of strings (handles str, list, and tuples)
        if isinstance(target_objects, str):
            target_objects_list = [target_objects]
        else:
            target_objects_list = list(target_objects)
        
        ltl_rule = self.generate_ltl_rule(target_objects_list)

        # Save the raw LTL rule for debugging purposes
        with open(os.path.join(output_dir, "rule.txt"), "w", encoding="utf-8") as r_file:
            r_file.write(ltl_rule + "\n")
        
        # Merge the original PDDL goal with the new LTL constraint rule
        formula_str, constant_list = self._join_goal_and_rule(unconstrained_problem, ltl_rule, target_objects_list)
        
        try:
            domain_parser = DomainParser()
            problem_parser = ProblemParser()
            
            domain_obj = domain_parser(Path(unconstrained_domain).read_text(encoding="utf-8"))
            problem_obj = problem_parser(Path(unconstrained_problem).read_text(encoding="utf-8"))
            
            # Invoke the Plan4Past compiler engine
            goal_formula = parse_pltl(formula_str)
            compiler = Compiler(domain_obj, problem_obj, goal_formula)
            compiler.compile()
            compiled_domain, compiled_problem = compiler.result
            
            # Convert the compiled AST back into standard PDDL strings
            domain_str = domain_to_string(compiled_domain)
            problem_str = problem_to_string(compiled_problem)
            
            # Clean up constraints and object promotion blocks
            domain_str, problem_str = self._execute_cleanup(domain_str, problem_str, constant_list)
            
            with open(os.path.join(output_dir, "domain.pddl"), "w", encoding="utf-8") as d:
                d.write(domain_str)
            with open(os.path.join(output_dir, "problem.pddl"), "w", encoding="utf-8") as p:
                p.write(problem_str)
                
            return True
        except Exception as e:
            return False
        
    def _join_goal_and_rule(self, problem_pddl_path: str, ltl_rule_str: str, target_objects: list[str]) -> tuple[str, list[str]]:
        """Combines the current problem goals with the LTL rule using PLTL syntax."""
        try:
            problem_parser = ProblemParser()
            problem_obj = problem_parser(Path(problem_pddl_path).read_text(encoding="utf-8"))
            
            goal_expr = problem_obj.goal
            atoms = list(goal_expr.operands) if isinstance(goal_expr, And) else [goal_expr]
                
            pltl_parts = []
            all_constants_to_promote = list(target_objects)
            
            # Convert standard PDDL goals into PPLTL atoms (e.g., (at robot cell) -> at_robot_cell)
            for atom in atoms:
                if hasattr(atom, "name") and hasattr(atom, "terms"):
                    pred_name = atom.name
                    args = [getattr(term, "name", str(term)) for term in atom.terms]
                else:
                    atom_str = str(atom).strip("() ")
                    parts = atom_str.split()
                    pred_name = parts[0]
                    args = parts[1:]
                
                # Register constants that need to be promoted to the domain level
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
            return ltl_rule_str, list(target_objects)
        
    def _execute_cleanup(self, domain_str: str, problem_str: str, constant_list: list) -> tuple[str, str]:
        """Fixes requirement blocks and syncs promoted constants between domain and problem strings."""
        if not constant_list:
            return domain_str, problem_str
        
        # 1. Map each token with its PDDL type found in the problem string
        typed_constants = []
        for token in constant_list:
            type_match = re.search(r'\b' + re.escape(token) + r'\s+-\s+([a-zA-Z0-9_-]+)', problem_str, re.IGNORECASE)
            if type_match:
                obj_type = type_match.group(1)
                typed_constants.append(f"{token} - {obj_type}")
            else:
                typed_constants.append(token)

        # 2. Inject :disjunctive-preconditions requirement if missing
        req_match = re.search(r'\(:requirements\s+([^)]*)\)', domain_str, re.DOTALL | re.IGNORECASE)
        if req_match:
            current_requirements = req_match.group(1)
            if ":disjunctive-preconditions" not in current_requirements:
                new_requirements = f"(:requirements {current_requirements.strip()} :disjunctive-preconditions)"
                domain_str = domain_str.replace(req_match.group(0), new_requirements)
        else:
            domain_str = re.sub(r'\(define\s+\(domain\s+[a-zA-Z0-9_-]+\)', r'\g<0>\n    (:requirements :disjunctive-preconditions)', domain_str, flags=re.IGNORECASE)

        constants_text = " ".join(typed_constants)
        const_match = re.search(r'\(:constants\s+([^)]*)\)', domain_str, re.DOTALL | re.IGNORECASE)
        
        # 3. Update or inject the (:constants ) block into the domain string
        if const_match:
            existing_content = const_match.group(1).strip()
            
            # CRITICAL PATCH: Fixes Plan4Past bug that breaks direction typing in Sokoban/Gridworld
            if "down" in existing_content and "-" not in existing_content:
                clean_content = existing_content.replace("down", "").replace("up", "").replace("left", "").replace("right", "").strip()
                updated_block = f"(:constants down up left right - direction {clean_content} {constants_text})"
            else:
                updated_block = f"(:constants {existing_content} {constants_text})"
                
            domain_str = domain_str.replace(const_match.group(0), updated_block)
        else:
            updated_req_match = re.search(r'\(:requirements\s+.*?\)', domain_str, re.DOTALL | re.IGNORECASE)
            if updated_req_match:
                end_idx = updated_req_match.end()
                domain_str = domain_str[:end_idx] + f"\n    (:constants {constants_text})" + domain_str[end_idx:]
        
        # 4. Remove constants from the standard (:objects ) block using a robust regex callback
        def clean_objects_block(match):
            objects_text = match.group(1)
            for token in constant_list:
                objects_text = re.sub(r'\b' + re.escape(token) + r'\s+-\s+[a-zA-Z0-9_-]+\b', '', objects_text, flags=re.IGNORECASE)
                objects_text = re.sub(r'\b' + re.escape(token) + r'\b', '', objects_text)
            
            # Clean up residual hyphens, types, and double spaces
            objects_text = re.sub(r'-\s+[a-zA-Z0-9_-]+\s+(?=-\s+[a-zA-Z0-9_-]+)', '', objects_text)
            objects_text = re.sub(r'-\s+[a-zA-Z0-9_-]+\s*\)$', '', objects_text.strip())
            return f"(:objects {re.sub(r'\s+', ' ', objects_text).strip()})"
        
        # Safe inline substitution via regex engine for complex problem blocks
        problem_str = re.sub(r'\(:objects\s+(.*?)\)', clean_objects_block, problem_str, flags=re.DOTALL)

        return domain_str, problem_str