import os
import re
import random
from abc import ABC, abstractmethod
from pathlib import Path
from pddl.parser.problem import ProblemParser
from pddl.logic.base import And

# =============================================================================
# MAIN MOTOR ENGINE (SHARED AGNOSTIC LOGIC)
# =============================================================================
class BaseExtractor(ABC):
    def __init__(self, plan_path: str, problem_path: str, blacklist: set):
        self.plan_path = plan_path
        self.problem_path = problem_path
        self.blacklist = blacklist if blacklist is not None else set()

    @abstractmethod
    def _get_problem_regex(self) -> str:
        """Returns the regex pattern to scan the PDDL problem file."""
        pass

    @abstractmethod
    def _get_plan_regex(self) -> str:
        """Returns the regex pattern to extract tokens from the plan file."""
        pass

    @abstractmethod
    def _get_goal_regex(self) -> str | None:
        """Returns the regex pattern to filter goal terms, or None if unused."""
        pass

    # -------------------------------------------------------------------------
    # CORE EXTRACTION UTILITIES
    # -------------------------------------------------------------------------
    def _extract_objects_from_problem(self) -> list:
        if not os.path.exists(self.problem_path): 
            return []
        content = Path(self.problem_path).read_text(encoding="utf-8").lower()
        found = re.findall(self._get_problem_regex(), content)
        # Unpack match groups if the regex returns tuples
        cleaned = [obj[0] if isinstance(obj, tuple) else obj for obj in found]
        return list(set(cleaned))

    def _extract_objects_from_plan(self) -> list:
        if not os.path.exists(self.plan_path): 
            return []
            
        content = Path(self.plan_path).read_text(encoding="utf-8").lower()
        regex_pattern = self._get_plan_regex()
        
        tracked = []
        # Process line by line to ignore plan comments and preserve temporal order
        for line in content.splitlines():
            line = line.strip()
            if line.startswith(";") or not line:
                continue
                
            found = re.findall(regex_pattern, line)
            for item in found:
                token = item[0] if isinstance(item, tuple) else item
                # Deduplicate consecutive identical actions
                if not tracked or tracked[-1] != token: 
                    tracked.append(token)
        return tracked

    def _extract_goals_from_problem(self) -> set:
        goal_regex = self._get_goal_regex()
        if not os.path.exists(self.problem_path) or not goal_regex: 
            return set()
        try:
            problem_obj = ProblemParser()(Path(self.problem_path).read_text(encoding="utf-8"))
            goal_expr = problem_obj.goal
            atoms = list(goal_expr.operands) if isinstance(goal_expr, And) else [goal_expr]
            
            goal_objects = set()
            for atom in atoms:
                for term in atom.terms:
                    if re.match(goal_regex, term.name, re.IGNORECASE):
                        goal_objects.add(term.name.lower())
            return goal_objects
        except Exception:
            return set()

    # -------------------------------------------------------------------------
    # CONSTRAINT SAMPLING STRATEGIES
    # -------------------------------------------------------------------------
    def extract_avoidance(self) -> any:
        """Picks a random object from the plan that is not part of the goal or blacklist."""
        plan_objects = self._extract_objects_from_plan()
        goal_objects = self._extract_goals_from_problem()
        full_blacklist = self.blacklist.union(goal_objects)
        
        candidates = [o for o in plan_objects if o not in full_blacklist]
        return random.choice(candidates) if candidates else None

    def extract_obligation(self) -> any:
        """Picks a random world object that was completely ignored in the plan."""
        prob_objects = self._extract_objects_from_problem()
        plan_objects = self._extract_objects_from_plan()
        candidates = list(set(prob_objects) - set(plan_objects) - self.blacklist)
        return random.choice(candidates) if candidates else None

    def extract_ordering(self) -> tuple[str, str] | None:
        """Picks two distinct sequential objects from the plan and reverses their order."""
        plan_objects = self._extract_objects_from_plan()
        if len(plan_objects) < 2: 
            return None
        for _ in range(200):
            i, j = random.randint(0, len(plan_objects)-2), random.randint(1, len(plan_objects)-1)
            if i < j and plan_objects[i] != plan_objects[j]:
                pair = (plan_objects[j], plan_objects[i])
                if pair not in self.blacklist: 
                    return pair
        return None

# =============================================================================
# DOMAIN EXTRACTOR IMPLEMENTATIONS
# =============================================================================

class GridworldExtractor(BaseExtractor):
    def _get_problem_regex(self) -> str:
        return r'\bp[0-9]+\b'

    def _get_plan_regex(self) -> str:
        # Capture the destination cell (second argument) of a move action
        return r"\(move\s+\S+\s+(\S+)\)"

    def _get_goal_regex(self) -> str | None:
        return r'^p[0-9]+$'


class GoldminerExtractor(BaseExtractor):
    def _get_problem_regex(self) -> str:
        return r"\(soft-rock-at\s+([^\s\)]+)\)"

    def _get_plan_regex(self) -> str:
        # Capture the rock name target during a detonate bomb action
        return r"\(detonate[-_]?bomb\s+\S+\s+([^\s\)]+)\)"

    def _get_goal_regex(self) -> str | None:
        return None


class SokobanExtractor(BaseExtractor):
    def _get_problem_regex(self) -> str:
        return r'\bloc-[0-9]+-[0-9]+\b'

    def _get_plan_regex(self) -> str:
        return r'\bloc-[0-9]+-[0-9]+\b'

    def _get_goal_regex(self) -> str | None:
        return None

    def _get_sokoban_goal_regex(self) -> str:
        return r'at\s+(box[0-9]+)\s+(loc-[0-9]+-[0-9]+)'

    def _extract_boxes_from_plan_backwards(self, sokoban_goals_map: dict) -> list[str]:
        """Reads the plan backward to find the final delivery order of the boxes."""
        box_reverse_order = []
        with open(self.plan_path, "r", encoding="utf-8") as f:
            plan_lines = list(reversed(f.readlines()))
            
        for line in plan_lines:
            line = line.strip().lower()
            if "push" in line:
                found_boxes = re.findall(r'\bbox[0-9]+\b', line)
                for b in found_boxes:
                    if b in sokoban_goals_map and b not in box_reverse_order:
                        box_reverse_order.append(b)
                        
        return list(reversed(box_reverse_order))
    
    def extract_ordering(self) -> tuple[str, str, str, str] | None:
        """Finds a box pair and forces them to be delivered in inverse chronological order."""
        if not os.path.exists(self.problem_path) or not os.path.exists(self.plan_path):
            return None
            
        try:
            # Map each Box to its target Goal Location
            with open(self.problem_path, "r", encoding="utf-8") as f:
                prob_content = f.read().lower()
            
            goal_block = re.search(r'\(:goal\s+(.*?)\)\s*\)\s*$', prob_content, re.DOTALL)
            if not goal_block: 
                return None
                
            sokoban_goals_map = dict(re.findall(self._get_sokoban_goal_regex(), goal_block.group(1)))
            
            #  Get the real box delivery sequence from the plan
            box_chronological_order = self._extract_boxes_from_plan_backwards(sokoban_goals_map)
            if len(box_chronological_order) < 2: 
                return None

            # Generate all valid sequence combinations (i < j) as immutable tuples
            possible_candidates = []
            for i in range(len(box_chronological_order) - 1):
                for j in range(i + 1, len(box_chronological_order)):
                    box_A = box_chronological_order[i]
                    loc_A = sokoban_goals_map[box_A]
                    box_B = box_chronological_order[j]
                    loc_B = sokoban_goals_map[box_B]
                    
                    possible_candidates.append((box_A, loc_A, box_B, loc_B))

            #Pick a candidate randomly and filter out blacklisted items
            while possible_candidates:
                candidate = random.choice(possible_candidates)
                possible_candidates.remove(candidate)
                
                if candidate not in self.blacklist:
                    return candidate
                    
            return None
        except Exception:
            return None

# =============================================================================
# FACTORY INTERFACE ROUTER
# =============================================================================
def get_random_target(domain: str, constraint: str, plan_path: str, problem_path: str, blacklist: set = None) -> any:
    if blacklist is None: 
        blacklist = set()

    extractor_mapping = {
        "gridworld": GridworldExtractor,
        "goldminer": GoldminerExtractor,
        "sokoban": SokobanExtractor
    }

    extractor_cls = extractor_mapping.get(domain.lower())
    if not extractor_cls: 
        return None

    extractor_instance = extractor_cls(plan_path, problem_path, blacklist)

    strategies = {
        "avoidance": extractor_instance.extract_avoidance,
        "obligation": extractor_instance.extract_obligation,
        "ordering": extractor_instance.extract_ordering
    }
    
    strategy_func = strategies.get(constraint.lower())
    return strategy_func() if strategy_func else None