import os
import sys
from generation.generators_manager import GeneratorsManager
from generation.generators import MiniGridGenerator, GoldminerGenerator, SokobanGenerator
from utils import clear_domain_dirs

DOMAIN_MAPPING = {
    "gridworld": os.path.abspath(os.path.join("plans", "uncostrained", "gridworld", "domain.pddl")),
    "goldminer": os.path.abspath(os.path.join("plans", "uncostrained", "goldminer", "domain.pddl")),
    "sokoban":   os.path.abspath(os.path.join("plans", "uncostrained", "sokoban", "domain.pddl"))
}

def ui_status_logger(event_type, data):
    if event_type == "init":
        print(f"Initial progress: {data['current']} files found. Final target: {data['target']}")
    elif event_type == "attempt":
        print("[DEBUG] Attempting instance generation and validation...", flush=True)
    elif event_type == "success":
        print(f"  └─> VALIDATED AND SAVED! -> Progress: {data['current']}/{data['target']}")
    elif event_type == "failed":
        print("  └─> Discarded (Unsolvable or Validation Error).")
    elif event_type == "finished":
        print(f"\n[OK] Success! Generated all PDDL instances and plans for {data['prefix']}.")
    elif event_type == "interrupted":
        print("\n\n[WARNING] Generation interrupted by user (Ctrl+C). Cleaning up temporary files...")

def get_choice(prompt, valid_choices):
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid_choices:
            return choice
        print(f"Invalid input. Please choose among: {', '.join(valid_choices)}")

def handle_clear_datasets():
    print("--------------------------------------------------")
    print("\n--- SELECT DOMAIN TO CLEAR ---")
    print(" [1] GridWorld")
    print(" [2] Sokoban")
    print(" [3] Goldminer")
    print(" [c] Cancel")
    
    sub_choice = input("Select domain: ").strip().lower()
    mapping = {"1": "gridworld", "2": "sokoban", "3": "goldminer"}
    
    if sub_choice == "c" or sub_choice not in mapping:
        print("[CANCELLED] Directory clearing aborted.")
        return
        
    domain_folder = mapping[sub_choice]
    prob_path = os.path.abspath(os.path.join("plans", "uncostrained", domain_folder))
    plan_path = os.path.join(prob_path, "solutions")
    
    print(f"\n[WARNING] You are about to clear:")
    print(f" -> Problems: {prob_path}")
    print(f" -> Plans:     {plan_path}")
    confirm = input(f"Are you sure you want to delete all {domain_folder} data? (y/n): ").strip().lower()
    
    if confirm == 'y':
        count = clear_domain_dirs(prob_path, plan_path)
        print(f"[OK] Cleanup finished. Removed {count} file(s).")
        print("[INFO] 'domain.pddl' has been safely preserved.")
    else:
        print("[CANCELLED] Directory clearing aborted.")

def main():
    while True:
        print("\n==================================================")
        print("            PDDL INSTANCE GENERATOR TOOL          ")
        print("==================================================")
        print("Available domains:")
        print("  [1] GridWorld (MiniGrid)")
        print("  [2] Sokoban")
        print("  [3] Goldminer")
        print("  [4] Clear dataset folders")
        print("  [q] Quit")
        
        choice = get_choice("Select an option: ", ["1", "2", "3", "4", "q"])
        
        if choice == "q":
            print("Exiting tool. Goodbye!")
            sys.exit(0)
            
        if choice == "4":
            handle_clear_datasets()
            print("==================================================")
            continue
            
        try:
            problems_num = int(input("How many instances do you want to generate?: ").strip())
            if problems_num <= 0: 
                raise ValueError
        except ValueError:
            print("[ERROR] Please enter a valid positive integer.")
            continue

        print("--------------------------------------------------")
        
        try:
            manager = GeneratorsManager(domain_mapping=DOMAIN_MAPPING)
            
            generator_factory = {
                "1": MiniGridGenerator,
                "2": SokobanGenerator,
                "3": GoldminerGenerator
            }
            
            generator_class = generator_factory.get(choice)
            if generator_class:
                generator_instance = generator_class() 
                
                manager.run_loop(
                    generator=generator_instance,
                    count=problems_num,
                    status_callback=ui_status_logger
                )
        except Exception as e:
            print(f"\n❌ [CRASH ENCOUNTERED] Si è verificato un errore critico durante la generazione:\n -> {e}")
            print("[INFO] Ripristino del menu principale in corso...")
            
        print("==================================================")

if __name__ == "__main__":
    main()