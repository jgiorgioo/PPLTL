import os
import sys
from generation.generators_manager import GeneratorsManager
from generation.generators import MiniGridGenerator, GoldminerGenerator, SokobanGenerator
from utils.functions import count_unconstrained_total_instances

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
            print(f"Starting a new generation session. Target: {data['target']} new instances.")
            
        case "attempt":
            print("Attempting instance generation and validation...", flush=True)
            
        case "success":
            print(f"  └─> VALIDATED AND SAVED! -> Progress: {data['current']}/{data['target']}")
            
        case "failed":
            print("  └─> Discarded (Unsolvable or Validation Error).")
            
        case "finished":
            print(f"\nSuccess! Generated all PDDL instances and plans for {data['prefix']}.")
            
        case "interrupted":
            print("\n\n[WARNING] Generation interrupted by user (Ctrl+C). Cleaning up temporary files...")

        case "timeout_error":
            print(f"\n[TIMEOUT ERROR] {data['details']}")

        case "binary_error":
            print(f"\n[MISSING BINARY ERROR] {data['details']}")
            print(" -> Check your configuration and paths on the server.")

        case "file_error":
            print(f"\n[FILE ERROR] {data['details']}")
            print(" -> The current seed will be skipped. Moving to the next attempt.")

        case  "unknown_error":
            print(f"\n[UNKNOWN ERROR] {data['details']}")

def get_choice(prompt, valid_choices):
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid_choices:
            return choice
        print(f"Invalid input. Please choose among: {', '.join(valid_choices)}")

def main():
    manager = GeneratorsManager(domain_mapping=DOMAIN_MAPPING)

    while True:
        print("\n==================================================")
        print("            PDDL INSTANCE GENERATOR TOOL          ")
        print("==================================================")
        print("Available domains:")
        print("  [1] GridWorld (MiniGrid)")
        print("  [2] Sokoban")
        print("  [3] Goldminer")
        print("  [q] Quit")
        
        choice = get_choice("Select an option: ", ["1", "2", "3", "q"])
        
        if choice == "q":
            print("Exiting tool. Goodbye!")
            sys.exit(0)
            
        generator_class = GENERATOR_FACTORY.get(choice)
        if not generator_class:
            continue
            
        generator_instance = generator_class()
        domain_key = generator_instance.domain_name 
        domain_path = DOMAIN_MAPPING.get(domain_key)

        if not domain_path or not os.path.exists(domain_path):
            print(f"\n[CRITICAL ERROR] Domain file missing at: '{domain_path}'")
            print("Please restore the domain file before generating new instances.")
            print("==================================================")
            continue

        base_path = os.path.dirname(domain_path)
        existing_count = count_unconstrained_total_instances(domain_key, base_path)
        print(f"\n[STATUS] Found {existing_count} existing {domain_key} instances.")
        print("--------------------------------------------------")
        
        try:
            problems_num = int(input("How many new instances do you want to generate?: ").strip())
            if problems_num <= 0: 
                print("[ERROR] Please enter a valid positive integer.")
                continue

            print("--------------------------------------------------")
            
            manager.run_loop(
                generator=generator_instance,
                count=problems_num,
                status_callback=ui_status_logger
            )
                
        except ValueError:
            print("[ERROR] Invalid numeric input. Please try again.")
        except Exception as e:
            print(f"\n[CRASH] A critical error occurred during execution:\n -> {e}")
            print("[INFO] Resetting system and recovering main menu...")
            
        print("==================================================")

if __name__ == "__main__":
    main()