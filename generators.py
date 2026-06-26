import os
import random

# Pool di configurazione spostati nel contesto dei generatori (coesione)
MINIGRID_POOL = {
    "floorplans": [
        ("9room3.fpl", 35), ("9room2.fpl", 35), ("4room3.fpl", 10),
        ("3Vroom3.fpl", 10), ("3Hroom3.fpl", 10)
    ],
    "nshapes_range": (2, 6)
}

GOLDMINER_POOL = {"rows_range": (5, 10), "cols_range": (5, 10)}
SOKOBAN_POOL = {"grid_size_range": (5, 10), "boxes_range": (2, 5)}


class PDDLGenerator:
    """Interfaccia astratta per i generatori di istanze PDDL."""
    def __init__(self, domain_name: str, base_dir: str):
        self.domain_name = domain_name
        # Ogni generatore conosce le proprie sottocartelle di destinazione
        self.problems_dir = os.path.abspath(os.path.join(base_dir, domain_name))
        self.plans_dir = os.path.abspath(os.path.join(self.problems_dir, "solutions"))

    def prepare_execution(self) -> tuple[list[str], bool, int]:
        """Genera parametri casuali e restituisce (comando, is_stdout_mode, seed)."""
        pass


class MiniGridGenerator(PDDLGenerator):
    def __init__(self, base_dir: str = "plans/uncostrained"):
        super().__init__("gridworld", base_dir)
        self.script_path = os.path.abspath(os.path.join("pddl-generators", "minigrid", "mini_grid.py"))
        self.floorplans_folder = os.path.abspath(os.path.join("pddl-generators", "minigrid", "floorplans"))

    def prepare_execution(self):
        seed = random.randint(0, 10**9)
        floorplan_options = [item[0] for item in MINIGRID_POOL["floorplans"]]
        floorplan_weights = [item[1] for item in MINIGRID_POOL["floorplans"]]
        chosen_fpl = random.choices(floorplan_options, weights=floorplan_weights, k=1)[0]
        nshapes = random.randint(*MINIGRID_POOL["nshapes_range"])

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

    def prepare_execution(self):
        seed = random.randint(0, 10**9)
        rows = random.randint(*GOLDMINER_POOL["rows_range"])
        cols = random.randint(*GOLDMINER_POOL["cols_range"])

        command = [self.executable_path, "-r", str(rows), "-c", str(cols), "-s", str(seed)]
        return command, True, seed


class SokobanGenerator(PDDLGenerator):
    def __init__(self, base_dir: str = "plans/uncostrained"):
        super().__init__("sokoban", base_dir)
        self.script_path = os.path.abspath(os.path.join("pddl-generators", "sokoban", "sokoban.py"))

    def prepare_execution(self):
        seed = random.randint(0, 10**9)
        grid_size = random.randint(*SOKOBAN_POOL["grid_size_range"])
        boxes = random.randint(*SOKOBAN_POOL["boxes_range"])

        command = [
            "python3", self.script_path,
            "-g", str(grid_size), "-b", str(boxes),
            "--seed", str(seed), "-id", "0", "-out", "." 
        ]
        return command, False, seed