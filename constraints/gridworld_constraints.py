from abc import ABC
from constraints.base_constraint import BaseConstraint

class GridworldConstraint(BaseConstraint, ABC):

    @property
    def _target_token_regex(self) -> str:
        return r'p[0-9]+'

class AvoidanceGridworld(GridworldConstraint):

    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        avoid_cell = target_objects[0]
        return f"!O(at-robot_{avoid_cell})"


class ObligationGridworld(GridworldConstraint):

    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        obligation_cell = target_objects[0]
        return f"O(at-robot_{obligation_cell})"
    
class OrderingGridworld(GridworldConstraint):

    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell_a = target_objects[0]
        cell_b = target_objects[1]
        return f"O(at-robot_{cell_b} & O(at-robot_{cell_a}))"

GRIDWORLD_CONSTRAINTS = {
    "avoidance": AvoidanceGridworld,
    "obligation": ObligationGridworld,
    "ordering": OrderingGridworld
}

def get_gridworld_constraint(constraint_name: str):
    constraint_class = GRIDWORLD_CONSTRAINTS.get(constraint_name)
    if not constraint_class:
        raise NotImplementedError(f"Constraint '{constraint_name}' not implemented for Gridworld.")
    return constraint_class()