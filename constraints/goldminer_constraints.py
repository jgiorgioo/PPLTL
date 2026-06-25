from abc import ABC
from constraints.base_constraint import BaseConstraint

class GoldminerConstraint(BaseConstraint, ABC):

    @property
    def _target_token_regex(self) -> str:
        return r'[a-zA-Z0-9\-]+'

class AvoidanceGoldminer(GoldminerConstraint):

    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell = target_objects[0]
        return f"!O(clear_{cell})"
class ObligationGoldminer(GoldminerConstraint):

    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell = target_objects[0]
        return f"O(clear_{cell})"
    

class OrderingGoldminer(GoldminerConstraint):

    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell_a = target_objects[0]
        cell_b = target_objects[1]
        
        return f"O(clear_{cell_b} & O(clear_{cell_a}))"


GOLDMINER_CONSTRAINTS = {
    "avoidance": AvoidanceGoldminer,
    "obligation": ObligationGoldminer,
    "ordering": OrderingGoldminer
}

def get_goldminer_constraint(constraint_name: str):
    constraint_class = GOLDMINER_CONSTRAINTS.get(constraint_name)
    if not constraint_class:
        raise NotImplementedError(f"Constraint '{constraint_name}' not implemented for Goldminer.")
    return constraint_class()