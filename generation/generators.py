import os
import random

# Configuration pools for random parameter generation per domain
MINIGRID_POOL = {
    "floorplans": [
        ("9room3.fpl", 35), ("9room2.fpl", 35), ("4room3.fpl", 10),
        ("3Vroom3.fpl", 10), ("3Hroom3.fpl", 10)
    ],
    "nshapes_range": (2, 6)
}

GOLDMINER_POOL = {"rows_range": (5, 10), "cols_range": (5, 10)}
SOKOBAN_POOL = {"grid_size_range": (5, 10), "boxes_range": (2, 6)}


class PDDLGenerator:
    """
    Abstract interface supplying domain-specific configurations for the actual generators.
    """
    def __init__(self, domain_name: str, base_dir: str):
        self.domain_name = domain_name
        self.base_dir = os.path.abspath(base_dir)
        # Dynamic internal state fields managed through getter properties
        self._current_problems_dir = None
        self._current_plans_dir = None
        self._current_stratum_tag = None

    def get_problems_dir(self) -> str:
        """Returns the problems directory computed during the last execution preparation."""
        return self._current_problems_dir

    def get_plans_dir(self) -> str:
        """Returns the plans/solutions directory computed during the last execution preparation."""
        return self._current_plans_dir

    def get_current_stratum(self) -> str:
        """Returns the stratum tag identified during the last execution preparation."""
        return self._current_stratum_tag

    def prepare_execution(self) -> tuple[list[str], bool, int]:
        """
        Generates random parameters, updates state properties, and returns execution details.
        Returns: command, is_stdout_mode, seed
        """
        pass

    def get_stratum_tag(self, **kwargs) -> str:
        raise NotImplementedError


class MiniGridGenerator(PDDLGenerator):
    def __init__(self, base_dir: str = "plans/uncostrained"):
        super().__init__("gridworld", base_dir)
        self.script_path = os.path.abspath(os.path.join("pddl-generators", "minigrid", "mini_grid.py"))
        self.floorplans_folder = os.path.abspath(os.path.join("pddl-generators", "minigrid", "floorplans"))

    def get_stratum_tag(self, chosen_fpl: str) -> str:
        return chosen_fpl.replace(".fpl", "")

    def prepare_execution(self):
        seed = random.randint(0, 10**9)
        floorplan_options = [item[0] for item in MINIGRID_POOL["floorplans"]]
        floorplan_weights = [item[1] for item in MINIGRID_POOL["floorplans"]]
        chosen_fpl = random.choices(floorplan_options, weights=floorplan_weights, k=1)[0]
        nshapes = random.randint(*MINIGRID_POOL["nshapes_range"])
        
        self._current_stratum_tag = self.get_stratum_tag(chosen_fpl=chosen_fpl)
        self._current_problems_dir = os.path.join(self.base_dir, self.domain_name, self._current_stratum_tag)
        self._current_plans_dir = os.path.join(self._current_problems_dir, "solutions")

        command = [
            "python3", self.script_path, chosen_fpl, str(nshapes),
            "--seed", str(seed), "--num_instances", "1",
            "--results", ".", "--floorplans_path", self.floorplans_folder  
        ]
        return command, False, seed


class GoldminerGenerator(PDDLGenerator):
    def __init__(self, base_dir: str = "plans/uncostrained"):
        super().__init__("goldminer", base_dir)
        self.executable_path = os.path.abspath(os.path.join("pddl-generators", "goldminer", "gold-miner-generator"))

    def get_stratum_tag(self, rows: int = None, cols: int = None, **kwargs) -> str:
        area = rows * cols
        if area <= 39: return "xs"
        elif area <= 54: return "s"
        elif area <= 69: return "m"
        elif area <= 84: return "l"
        else: return "xl"

    def prepare_execution(self):
        seed = random.randint(0, 10**9)
        rows = random.randint(*GOLDMINER_POOL["rows_range"])
        cols = random.randint(*GOLDMINER_POOL["cols_range"])

        self._current_stratum_tag = self.get_stratum_tag(rows=rows, cols=cols)
        self._current_problems_dir = os.path.join(self.base_dir, self.domain_name, self._current_stratum_tag)
        self._current_plans_dir = os.path.join(self._current_problems_dir, "solutions")

        command = [self.executable_path, "-r", str(rows), "-c", str(cols), "-s", str(seed)]
        return command, True, seed


class SokobanGenerator(PDDLGenerator):
    def __init__(self, base_dir: str = "plans/uncostrained"):
        super().__init__("sokoban", base_dir)
        self.script_path = os.path.abspath(os.path.join("pddl-generators", "sokoban", "sokoban.py"))

    def get_stratum_tag(self, boxes: int = None, **kwargs) -> str:
        return f"{boxes}_boxes"

    def prepare_execution(self):
        seed = random.randint(0, 10**9)
        grid_size = random.randint(*SOKOBAN_POOL["grid_size_range"])
        boxes = random.randint(*SOKOBAN_POOL["boxes_range"])

        self._current_stratum_tag = self.get_stratum_tag(boxes=boxes)
        self._current_problems_dir = os.path.join(self.base_dir, self.domain_name, self._current_stratum_tag)
        self._current_plans_dir = os.path.join(self._current_problems_dir, "solutions")

        command = [
            "python3", self.script_path,
            "-g", str(grid_size), "-b", str(boxes),
            "--seed", str(seed), "-id", "0", "-out", "." 
        ]
        return command, False, seed