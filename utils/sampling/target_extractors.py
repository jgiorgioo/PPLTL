import os
import re
import random

def _extract_objects_from_problem(domain: str, problem_path: str) -> list:
    """Parses problem.pddl to identify all available domain objects."""
    objects = []
    if not problem_path or not os.path.exists(problem_path):
        return objects
        
    with open(problem_path, "r", encoding="utf-8") as f:
        content = f.read().lower()
        
    if domain == "gridworld":
        found_cells = re.findall(r'\bp[0-9]+\b', content)
        objects = list(set(found_cells))

    elif domain == "goldminer":
        soft_rocks = re.findall(r"\(soft-rock-at\s+([^\s\)]+)\)", content)
        objects = list(set(soft_rocks))
        
    return objects

def _extract_objects_from_plan(domain: str, plan_path: str) -> list:
    """Parses the .plan file to extract chronological tracking of actions."""
    tracked_elements = []
    if not os.path.exists(plan_path):
        return tracked_elements

    with open(plan_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().lower()
            if line.startswith(";") or not line:
                continue
            
            if domain == "gridworld":
                match = re.match(r"\(move\s+(\S+)\s+(\S+)\)", line)
                if match:
                    if not tracked_elements:
                        tracked_elements.append(match.group(1)) # Start cell
                    destination_cell = match.group(2)
                    
                    if tracked_elements[-1] != destination_cell:
                        tracked_elements.append(destination_cell)

            elif domain == "goldminer":
                match_detonate = re.search(r"\(detonate[-_]?bomb\s+\S+\s+([^\s\)]+)\)", line)
                if match_detonate:
                    soft_rock = match_detonate.group(1)
                    if not tracked_elements or tracked_elements[-1] != soft_rock:
                        tracked_elements.append(soft_rock)

    if domain == "gridworld" and tracked_elements:
        tracked_elements = tracked_elements[:-1]

    return tracked_elements

def extract_avoidance(domain: str, plan_path: str, problem_path: str, blacklist: set) -> any:
    plan_objects = _extract_objects_from_plan(domain, plan_path)
    if not plan_objects:
        return None
    candidates = [o for o in plan_objects if o not in blacklist]
    return random.choice(candidates) if candidates else None


def extract_obligation(domain: str, plan_path: str, problem_path: str, blacklist: set) -> any:
    problem_objects = _extract_objects_from_problem(domain, problem_path)
    plan_objects = _extract_objects_from_plan(domain, plan_path)
    
    candidates = list(set(problem_objects) - set(plan_objects) - blacklist)
    return random.choice(candidates) if candidates else None


def extract_ordering(domain: str, plan_path: str, problem_path: str, blacklist: set) -> tuple | None:
    plan_objects = _extract_objects_from_plan(domain, plan_path)
    if len(plan_objects) < 2:
        return None
        
    max_sampling_attempts = 200
    attempts = 0
    
    while attempts < max_sampling_attempts:
        attempts += 1
        i = random.randint(0, len(plan_objects) - 2)
        j = random.randint(i + 1, len(plan_objects) - 1)
        obj_a, obj_b = plan_objects[i], plan_objects[j]
        
        if obj_a != obj_b:
            candidate_pair = (obj_b, obj_a)
            if candidate_pair not in blacklist:
                return candidate_pair
                
    return None

def get_random_target(domain: str, constraint: str, plan_path: str, problem_path: str, blacklist: set = None) -> any:
    if blacklist is None:
        blacklist = set()

    strategies = {
        "avoidance": extract_avoidance,
        "obligation": extract_obligation,
        "ordering": extract_ordering
    }
    
    strategy_func = strategies.get(constraint)
    if not strategy_func:
        print(f"[WARN] Unknown constraint type: {constraint}")
        return None
    
    return strategy_func(domain, plan_path, problem_path, blacklist)