import re

def extract_gridworld_avoidance(plan_path: str) -> list:
    """
    Parses a GridWorld .plan file matching the '(move from to)' syntax.
    Extracts the destination of each move action, excluding the final goal destination
    to provide a clean pool of unique intermediate cell candidates.
    """
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        visited_cells = []
        
        for line in lines:
            line = line.strip().lower()
            match = re.match(r"\(move\s+(\w+)\s+(\w+)\)", line)
            if match:
                destination_cell = match.group(2)
                visited_cells.append(destination_cell)
                
        if not visited_cells:
            print(f"[WARN] No move actions detected in plan: {plan_path}")
            return []
            
        goal_cell = visited_cells[-1]

        candidate_cells = [cell for cell in visited_cells if cell != goal_cell]
        
        return list(set(candidate_cells))

    except Exception as e:
        print(f"[ERROR] Failed to extract avoidance targets from plan {plan_path}: {e}")
        return []

EXTRACTOR_REGISTRY = {
    ("gridworld", "avoidance"): extract_gridworld_avoidance,
    # ("gridworld", "precedence"): extract_gridworld_precedence,
    # ("goldminer", "avoidance"): extract_goldminer_avoidance,
    # ...
}

def get_domain_targets(domain: str, constraint: str, plan_path: str) -> list:
    """
    Dispatches the target extraction request to the specific domain-constraint function.
    Returns a list of all identified string tokens.
    """
    extractor_func = EXTRACTOR_REGISTRY.get((domain, constraint))
    if not extractor_func:
        print(f"[WARN] No specific extractor registered for configuration: ({domain}, {constraint})")
        return []
    return extractor_func(plan_path)