import os

class PDDLGenerator:
    """Abstract interface for stateless PDDL problem instance generators."""
    def __init__(self, domain_name):
        self.domain_name = domain_name

    def get_command_and_mode(self, params):
        """Returns a tuple: (command_list, is_stdout_mode_bool)."""
        pass


class MiniGridGenerator(PDDLGenerator):
    """Stateless generator strategy for the GridWorld (MiniGrid) domain."""
    def __init__(self):
        super().__init__("gridworld")
        self.script_path = os.path.abspath(os.path.join("pddl-generators", "minigrid", "mini_grid.py"))
        self.floorplans_folder = os.path.abspath(os.path.join("pddl-generators", "minigrid", "floorplans"))

    def get_command_and_mode(self, params):
        command = [
            "python3", self.script_path,
            str(params["floorplan"]), 
            str(params["nshapes"]),
            "--seed", str(params["seed"]),
            "--num_instances", "1",
            "--results", ".",  
            "--floorplans_path", self.floorplans_folder  
        ]
        return command, False


class CityCarGenerator(PDDLGenerator):
    """Stateless generator strategy for the CityCar domain."""
    def __init__(self):
        super().__init__("citycar")
        self.script_path = os.path.abspath(os.path.join("pddl-generators", "citycar", "generator.py"))

    def get_command_and_mode(self, params):
        command = [
            "python3", self.script_path,
            str(params["rows"]), 
            str(params["columns"]), 
            str(params["cars"]), 
            str(params["garages"]), 
            "--seed", str(params["seed"])
        ]
        return command, True


class GoldminerGenerator(PDDLGenerator):
    """Stateless generator strategy for the Goldminer domain."""
    def __init__(self):
        super().__init__("goldminer")
        self.executable_path = os.path.abspath(os.path.join("pddl-generators", "goldminer", "gold-miner-generator"))

    def get_command_and_mode(self, params):
        command = [
            self.executable_path,
            "-r", str(params["rows"]),
            "-c", str(params["columns"]),
            "-s", str(params["seed"])
        ]
        return command, True

class SokobanGenerator(PDDLGenerator):
    """Stateless generator strategy for the Sokoban domain (IPC 2023 Version)."""
    def __init__(self):
        super().__init__("sokoban")
        self.script_path = os.path.abspath(os.path.join("pddl-generators", "sokoban", "sokoban.py"))

    def get_command_and_mode(self, params):
        command = [
            "python3", self.script_path,
            "-g", str(params["grid_size"]),
            "-b", str(params["boxes"]),
            "--seed", str(params["seed"]),
            "-id", str(params["instance_id"]),
            "-out", "." 
        ]
        return command, False