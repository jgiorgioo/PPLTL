from abc import ABC
from constraints.base_constraint import BaseConstraint

class SokobanConstraint(BaseConstraint, ABC):

    @property
    def _target_token_regex(self) -> str:
        return r'[a-zA-Z0-9_\-]+'

class AvoidanceSokoban(SokobanConstraint):

    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        avoid_cell = target_objects[0]
        return f"!O(at-robot_{avoid_cell})"


class ObligationSokoban(SokobanConstraint):

    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        obligation_cell = target_objects[0]
        return f"O(at-robot_{obligation_cell})"
    

class OrderingSokoban(SokobanConstraint):

    def generate_ltl_rule(self, target_objects: list[str]) -> str:
        cell_a = target_objects[0]
        cell_b = target_objects[1]
        # cell_a deve essere visitata prima di cell_b nel passato
        return f"O(at-robot_{cell_b} & O(at-robot_{cell_a}))"


SOKOBAN_CONSTRAINTS = {
    "avoidance": AvoidanceSokoban,
    "obligation": ObligationSokoban,
    "ordering": OrderingSokoban
}

def get_sokoban_constraint(constraint_name: str):
    constraint_class = SOKOBAN_CONSTRAINTS.get(constraint_name)
    if not constraint_class:
        raise NotImplementedError(f"Constraint '{constraint_name}' not implemented for Sokoban.")
    return constraint_class()