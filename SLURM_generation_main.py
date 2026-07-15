import os
import sys
from generation.generators_manager import GeneratorsManager
from generation.generators import MiniGridGenerator, GoldminerGenerator, SokobanGenerator

# Configurazione dei domini
DOMAIN_MAPPING = {
    "gridworld": os.path.abspath(os.path.join("plans", "unconstrained", "gridworld", "domain.pddl")),
    "goldminer": os.path.abspath(os.path.join("plans", "unconstrained", "goldminer", "domain.pddl")),
    "sokoban":   os.path.abspath(os.path.join("plans", "unconstrained", "sokoban", "domain.pddl"))
}

GENERATOR_FACTORY = {
    "1": MiniGridGenerator,
    "2": SokobanGenerator,
    "3": GoldminerGenerator
}

def ui_status_logger(event_type, data):
    match event_type:
        case "init":
            print(f"Starting a new generation session. Target: {data['target']} new instances.", flush=True)
            
        case "attempt":
            pass
            
        case "success":
            print(f" -> VALIDATED AND SAVED! -> Progress: {data['current']}/{data['target']}", flush=True)
            
        case "failed":
            pass
            
        case "finished":
            print(f"\nSuccess! Generated all PDDL instances and plans for {data['prefix']}.", flush=True)
            
        case "interrupted":
            print("\n\n[WARNING] Generation interrupted by user. Cleaning up temporary files...", flush=True)

        case "timeout_error":
            print(f"\n[TIMEOUT ERROR] {data['details']}", flush=True)

        case "binary_error":
            print(f"\n[MISSING BINARY ERROR] {data['details']}", flush=True)
            print(" -> Check your configuration and paths on the server.", flush=True)

        case "file_error":
            print(f"\n[FILE ERROR] {data['details']}", flush=True)
            print(" -> The current seed will be skipped. Moving to the next attempt.", flush=True)

        case "unknown_error":
            print(f"\n[UNKNOWN ERROR] {data['details']}", flush=True)

def main():
    # LEGGE I PARAMETRI DA RIGA DI COMANDO
    # Esempio d'uso: python3 run_headless.py <scelta_dominio> <numero_problemi>
    if len(sys.argv) < 3:
        print("Uso: python3 run_headless.py <1|2|3> <numero_problemi>")
        sys.exit(1)

    choice = sys.argv[1]
    try:
        problems_num = int(sys.argv[2])
    except ValueError:
        print("Errore: Il numero di problemi deve essere un intero.")
        sys.exit(1)

    manager = GeneratorsManager(domain_mapping=DOMAIN_MAPPING)
    generator_class = GENERATOR_FACTORY.get(choice)

    if not generator_class:
        print(f"Errore: Dominio '{choice}' non valido (usa 1, 2 o 3).")
        sys.exit(1)

    generator_instance = generator_class()
    domain_key = generator_instance.domain_name 
    domain_path = DOMAIN_MAPPING.get(domain_key)

    if not domain_path or not os.path.exists(domain_path):
        print(f"[CRITICAL ERROR] Domain file missing at: '{domain_path}'")
        sys.exit(1)

    print(f"Lancio generazione di {problems_num} problemi per il dominio: {domain_key}")
    
    manager.run_loop(
        generator=generator_instance,
        count=problems_num,
        status_callback=ui_status_logger
    )

if __name__ == "__main__":
    main()