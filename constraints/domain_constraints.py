from abc import ABC
from constraints.base_constraint import BaseConstraint

# =============================================================================
# VINCOLI DOMINIO: GRIDWORLD
# =============================================================================
class AvoidanceGridworld(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        avoid_cell = target_objects[0]
        return f"!O(at-robot_{avoid_cell})"

class ObligationGridworld(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        obligation_cell = target_objects[0]
        return f"O(at-robot_{obligation_cell})"
    
class OrderingGridworld(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell_a = target_objects[0]
        cell_b = target_objects[1]
        return f"O(at-robot_{cell_b} & O(at-robot_{cell_a}))"


# =============================================================================
# VINCOLI DOMINIO: GOLDMINER
# =============================================================================
class AvoidanceGoldminer(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell = target_objects[0]
        return f"!O(clear_{cell})"

class ObligationGoldminer(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell = target_objects[0]
        return f"O(clear_{cell})"
    
class OrderingGoldminer(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell_a = target_objects[0]
        cell_b = target_objects[1]
        return f"O(clear_{cell_b} & O(clear_{cell_a}))"


# =============================================================================
# VINCOLI DOMINIO: SOKOBAN
# =============================================================================
class AvoidanceSokoban(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        avoid_cell = target_objects[0]
        return f"!O(at-robot_{avoid_cell})"

class ObligationSokoban(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        obligation_cell = target_objects[0]
        return f"O(at-robot_{obligation_cell})"
    
class OrderingSokoban(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell_a = target_objects[0]
        cell_b = target_objects[1]
        return f"O(at-robot_{cell_b} & O(at-robot_{cell_a}))"


# =============================================================================
# FACTORY DI DISPATCH GENERALE
# =============================================================================
ALL_CONSTRAINTS_MAP = {
    "gridworld": {
        "avoidance": AvoidanceGridworld,
        "obligation": ObligationGridworld,
        "ordering": OrderingGridworld
    },
    "goldminer": {
        "avoidance": AvoidanceGoldminer,
        "obligation": ObligationGoldminer,
        "ordering": OrderingGoldminer
    },
    "sokoban": {
        "avoidance": AvoidanceSokoban,
        "obligation": ObligationSokoban,
        "ordering": OrderingSokoban
    }
}

def get_domain_constraint(domain_name: str, constraint_name: str):
    domain_map = ALL_CONSTRAINTS_MAP.get(domain_name.lower())
    if not domain_map:
        raise NotImplementedError(f"Domain '{domain_name}' is not supported.")
        
    constraint_class = domain_map.get(constraint_name.lower())
    if not constraint_class:
        raise NotImplementedError(f"Constraint '{constraint_name}' not implemented for domain '{domain_name}'.")
        
    return constraint_class()