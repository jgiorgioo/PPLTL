import os
import random

class ProblemSampler:
    """
    Manages random sampling of problems based on file distribution on disk.
    """
    def __init__(self, unconstrained_base_dir: str, domain_name: str):
        self.unconstrained_dir = os.path.abspath(unconstrained_base_dir)
        self.domain_name = domain_name
        
        # Pre-loaded data structures to avoid repeated disk reading during execution
        self.stratums = {}            # Maps each stratum folder name to its list of full file paths
        self.stratums_weights = []    # Calculated selection probabilities based on file counts
        self.stratums_names = []      # Flat list of folder names used as keys for random selection
        
        # Scan the disk once and populate the variables above immediately
        self._analyze_disk_distribution()

    def _analyze_disk_distribution(self):
        """Scans the directories, stores file paths, and calculates weights."""
        if not os.path.exists(self.unconstrained_dir):
            return

        total_files = 0
        counts_per_stratum = {}

        for folder_name in os.listdir(self.unconstrained_dir):
            stratum_path = os.path.join(self.unconstrained_dir, folder_name)
            solutions_path = os.path.join(stratum_path, "solutions")
            
            if os.path.isdir(stratum_path) and os.path.isdir(solutions_path):
                valid_pddl_files = [
                    f for f in os.listdir(stratum_path)
                    if f.startswith(f"{self.domain_name}-") and f.endswith(".pddl")
                ]
                if valid_pddl_files:
                    # Save the ready-to-use full paths into the dictionary
                    self.stratums[folder_name] = [os.path.join(stratum_path, f) for f in valid_pddl_files]
                    counts_per_stratum[folder_name] = len(valid_pddl_files)
                    total_files += len(valid_pddl_files)

        if total_files > 0:
            for folder_name, count in counts_per_stratum.items():
                percentage = (count / total_files) * 100
                self.stratums_names.append(folder_name)
                self.stratums_weights.append(percentage)

    def has_problems(self) -> bool:
        """Returns True if there are cached files available."""
        return len(self.stratums) > 0

    def sample_next_problem(self) -> str:
        """Picks a random file path respecting the disk distribution."""
        if not self.has_problems():
            return None

        chosen_stratum = random.choices(
            population=self.stratums_names,
            weights=self.stratums_weights,
            k=1
        )[0]

        file_list = self.stratums[chosen_stratum]
        chosen_file_path = random.choice(file_list)
        
        return chosen_file_path