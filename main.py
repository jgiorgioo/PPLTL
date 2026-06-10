import os
import sys
from generators import MiniGridGenerator, CityCarGenerator, GoldminerGenerator, SokobanGenerator

from generators_manager import run_generation_loop
from util import clear_domain_dirs

def ui_status_logger(event_type, data):
    """Callback function handling all screen outputs for the generation pipeline."""
    if event_type == "init":
        print(f"Initial progress: {data['current']} files found. Final target: {data['target']}")
    elif event_type == "attempt":
        print("[DEBUG] Attempting instance generation and validation...", flush=True)
    elif event_type == "success":
        print(f"  └─> VALIDATED AND SAVED! -> Progress: {data['current']}/{data['target']}")
    elif event_type == "failed":
        print("  └─> Discarded (Unsolvable or Validation Error).")
    elif event_type == "finished":
        print(f"\n[OK] Success! Generated all PDDL instances and plans for {data['domain']}.")
    elif event_type == "interrupted":
        print("\n\n[WARNING] Generation interrupted by user (Ctrl+C). Cleaning up temporary files...")

def get_choice(prompt, valid_choices):
    """UI Helper: Manages user input on the terminal."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid_choices:
            return choice
        print(f"Invalid input. Please choose among: {', '.join(valid_choices)}")

def main():
    print("==================================================")
    print("            PDDL INSTANCE GENERATOR TOOL          ")
    print("==================================================")
    print("Available domains:")
    print("  [1] GridWorld (MiniGrid)")
    print("  [2] CityCar")
    print("  [3] Sokoban")
    print("  [4] Goldminer")
    print("  [5] Clear dataset folders")
    print("  [q] Quit")
    
    choice = get_choice("Select an option: ", ["1", "2", "3", "4", "5", "q"])
    
    if choice == "q":
        print("Exiting tool. Goodbye!")
        sys.exit(0)
        
    if choice == "5":
        print("--------------------------------------------------")
        print("\n--- SELECT DOMAIN TO CLEAR ---")
        print(" [1] GridWorld (gridworld)")
        print(" [2] CityCar")
        print(" [3] Sokoban")
        print(" [4] Goldminer")
        print(" [c] Cancel")
        
        sub_choice = input("Select domain: ").strip().lower()
        mapping = {"1": "gridworld", "2": "citycar", "3": "sokoban", "4": "goldminer"}
        
        if sub_choice == "c" or sub_choice not in mapping:
            print("[CANCELLED] Directory clearing aborted.")
            print("==================================================")
            sys.exit(0)
            
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
            
        print("==================================================")
        sys.exit(0)
        
    # Request generation volume for domains 1, 2, 3, 4
    try:
        problems_num = int(input("How many instances do you want to generate?: ").strip())
        if problems_num <= 0: raise ValueError
    except ValueError:
        print("Error: Please enter a valid positive integer.")
        sys.exit(1)

    print("--------------------------------------------------")
    
    # UI mapping logic routes to stateless factories and manager loop
    if choice == "1":
        run_generation_loop(
            generator=MiniGridGenerator(),
            problems_dir="plans/uncostrained/gridworld",
            plans_dir="plans/uncostrained/gridworld/solutions",
            count=problems_num,
            status_callback=ui_status_logger
        )
        
    elif choice == "2":
        run_generation_loop(
            generator=CityCarGenerator(),
            problems_dir="plans/uncostrained/citycar",
            plans_dir="plans/uncostrained/citycar/solutions",
            count=problems_num,
            status_callback=ui_status_logger
        )
        
    elif choice == "3":
            run_generation_loop(
                generator=SokobanGenerator(),
                problems_dir="plans/uncostrained/sokoban",
                plans_dir="plans/uncostrained/sokoban/solutions",
                count=problems_num,
                status_callback=ui_status_logger
            )
            
    elif choice == "4":
        run_generation_loop(
            generator=GoldminerGenerator(),
            problems_dir="plans/uncostrained/goldminer",
            plans_dir="plans/uncostrained/goldminer/solutions",
            count=problems_num,
            status_callback=ui_status_logger
        )

    print("==================================================")

if __name__ == "__main__":
    main()