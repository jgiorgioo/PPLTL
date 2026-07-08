from constraints.base_constraint import BaseConstraint

# =============================================================================
# DOMAIN CONSTRAINTS: GRIDWORLD
# =============================================================================
class AvoidanceGridworld(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        return f"!O(at-robot_{target_objects[0]})"

class ObligationGridworld(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        return f"O(at-robot_{target_objects[0]})"
    
class OrderingGridworld(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell_a, cell_b = target_objects[0], target_objects[1]
        return f"O(at-robot_{cell_b} & O(at-robot_{cell_a}))"


# =============================================================================
# DOMAIN CONSTRAINTS: GOLDMINER
# =============================================================================
class AvoidanceGoldminer(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        return f"!O(clear_{target_objects[0]})"

class ObligationGoldminer(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        return f"O(clear_{target_objects[0]})"
    
class OrderingGoldminer(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell_a, cell_b = target_objects[0], target_objects[1]
        return f"O(clear_{cell_b} & O(clear_{cell_a}))"


# =============================================================================
# DOMAIN CONSTRAINTS: SOKOBAN
# =============================================================================
class AvoidanceSokoban(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        return f"!O(at-robot_{target_objects[0]})"

class ObligationSokoban(BaseConstraint):
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        return f"O(at-robot_{target_objects[0]})"
    
class OrderingSokoban(BaseConstraint):
    # Note on the negative formula: Sokoban goals are PERMANENT (boxes remain in place).
    # Since Plan4Past evaluates the past exclusively from the final state, a positive 
    # formula O(A & O(B)) would see both boxes already at their goals, making it always true.
    # We use !O(atom_A & !O(atom_B)) to forbid the intermediate state where A is stored 
    # while B has NEVER reached its goal yet, effectively forcing the inversion of the ordering.
    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        box_A, loc_A, box_B, loc_B = target_objects
        return f"!O(at_{box_A}_{loc_A} & !O(at_{box_B}_{loc_B}))"


# =============================================================================
# GENERAL DISPATCH FACTORY
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

def get_domain_constraint(domain_name: str, constraint_name: str) -> BaseConstraint:
    domain_map = ALL_CONSTRAINTS_MAP.get(domain_name.lower())
    if not domain_map:
        raise NotImplementedError(f"Domain '{domain_name}' is not supported.")
        
    constraint_class = domain_map.get(constraint_name.lower())
    if not constraint_class:
        raise NotImplementedError(f"Constraint '{constraint_name}' not implemented for domain '{domain_name}'.")
        
    return constraint_class()