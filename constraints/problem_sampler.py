import os
import random

class ProblemSampler:
    """
    Gestisce il pescaggio dei problemi non vincolati basandosi sulla 
    reale distribuzione dei file e dei loro stratum presenti sul disco.
    """
    def __init__(self, unconstrained_base_dir: str, domain_name: str):
        self.unconstrained_dir = os.path.abspath(unconstrained_base_dir)
        self.domain_name = domain_name
        
        # Proprietà configurate esattamente secondo le tue specifiche
        self.stratums = {}            # {'4room3': [file1, file2], '9room2': [...]}
        self.stratums_weights = []    # [4.67, 32.67, ...]
        self.stratums_names = []      # ['4room3', '9room2', ...]
        
        # Analizza il disco una volta sola all'inizializzazione dell'oggetto
        self._analyze_disk_distribution()

    def _analyze_disk_distribution(self):
        """Scansiona il disco una volta sola, conta i file e calcola i pesi dello stratum."""
        if not os.path.exists(self.unconstrained_dir):
            return

        total_files = 0
        counts_per_stratum = {}

        # 1. Scansione e conteggio dei file per ciascuno stratum
        for folder_name in os.listdir(self.unconstrained_dir):
            stratum_path = os.path.join(self.unconstrained_dir, folder_name)
            solutions_path = os.path.join(stratum_path, "solutions")
            
            if os.path.isdir(stratum_path) and os.path.isdir(solutions_path):
                valid_pddl_files = [
                    f for f in os.listdir(stratum_path)
                    if f.startswith(f"{self.domain_name}-") and f.endswith(".pddl")
                ]
                if valid_pddl_files:
                    # Memorizzazione dei percorsi completi per azzerare l'I/O successivo
                    self.stratums[folder_name] = [os.path.join(stratum_path, f) for f in valid_pddl_files]
                    counts_per_stratum[folder_name] = len(valid_pddl_files)
                    total_files += len(valid_pddl_files)

        # 2. Calcolo delle percentuali reali da usare come pesi nel campionamento
        if total_files > 0:
            print(f"\n--- [COMPOSIZIONE STATISTICA DEL DISCO PER {self.domain_name.upper()}] ---")
            for folder_name, count in counts_per_stratum.items():
                percentage = (count / total_files) * 100
                self.stratums_names.append(folder_name)
                self.stratums_weights.append(percentage)
                print(f" -> Stratum '{folder_name}': {count} file trovati ({percentage:.2f}%)")
            print("----------------------------------------------------------------\n")

    def has_problems(self) -> bool:
        return len(self.stratums) > 0

    def sample_next_problem(self) -> tuple[str, str]:
        """Estrae un file dalla memoria rispettando le percentuali dei pesi dello stratum."""
        if not self.has_problems():
            return None, None

        # Pesca lo stratum basandosi sulle frequenze reali registrate
        chosen_stratum = random.choices(
            population=self.stratums_names,
            weights=self.stratums_weights,
            k=1
        )[0]

        # Estrazione random uniforme locale del file dallo stratum vincente
        file_list = self.stratums[chosen_stratum]
        chosen_file_path = random.choice(file_list)
        
        return chosen_file_path, os.path.basename(chosen_file_path)