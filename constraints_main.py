import os
import sys
from constraints.constraints_manager import ConstraintManager
from utils import count_constrained_instances

# Dynamic absolute path mapping for unconstrained input and constrained output datasets
UNCONSTRAINED_MAP = {
    "gridworld": os.path.abspath(os.path.join("plans", "unconstrained", "gridworld")),
    "goldminer": os.path.abspath(os.path.join("plans", "unconstrained", "goldminer")),
    "sokoban":   os.path.abspath(os.path.join("plans", "unconstrained", "sokoban"))
}

CONSTRAINED_MAP = {
    "gridworld": os.path.abspath(os.path.join("plans", "constrained", "gridworld")),
    "goldminer": os.path.abspath(os.path.join("plans", "constrained", "goldminer")),
    "sokoban":   os.path.abspath(os.path.join("plans", "constrained", "sokoban"))
}

def ui_status_logger(event_type, data):
    """Callback function handling all screen outputs for the LTL constraint pipeline."""
    match event_type:
        case "init":
            print(f"Starting a new constraint compilation session. Target: {data['target']} new instances.")
            
        case "attempt":
            print("[DEBUG] Extracting targets, compiling LTL rule and testing solver...", flush=True)
            
        case "success":
            print(f"  └─> VALIDATED AND PACKAGED! -> Progress: {data['current']}/{data['target']}")
            
        case "failed":
            print("  └─> Discarded (Unsolvable target or LTL compilation error).")
            
        case "finished":
            print(f"\n[OK] Success! Generated all constrained instances for {data['prefix']}.")
            
        case "interrupted":
            print("\n\n[WARNING] Batch execution interrupted by user (Ctrl+C). Cleaning up workspace...")
            
        case "timeout_error":
            print(f"\n[TIMEOUT ERROR] {data['details']}")
            
        case "binary_error":
            print(f"\n[MISSING BINARY ERROR] {data['details']}\n -> Check solver configuration and path variables.")
            
        case "unknown_error":
            print(f"\n[UNKNOWN ERROR] Unexpected pipeline crash:\n -> {data['details']}")

def get_choice(prompt, valid_choices):
    """UI Helper: Manages secure user input on the terminal."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid_choices:
            return choice
        print(f"Invalid input. Please choose among: {', '.join(valid_choices)}")

def main():
    domain_map = {"1": "gridworld", "2": "sokoban", "3": "goldminer"}
    constraint_map = {"1": "avoidance", "2": "obligation", "3": "ordering"}

    while True:
        print("\n==================================================")
        print("            PDDL+LTL DATASET COMPILER TOOL        ")
        print("==================================================")
        print("Select Domain:")
        print("  [1] GridWorld")
        print("  [2] Sokoban")
        print("  [3] Goldminer")
        print("  [q] Quit")
        
        domain_choice = get_choice("Select domain option: ", ["1", "2", "3", "q"])
        
        if domain_choice == "q":
            print("Exiting tool. Goodbye!")
            sys.exit(0)
            
        print("--------------------------------------------------")
        print("Select Constraint Type:")
        print("  [1] Avoidance")
        print("  [2] Obligation")
        print("  [3] Ordering")
        constraint_choice = get_choice("Select constraint option: ", ["1", "2", "3"])
        
        selected_domain = domain_map[domain_choice]
        selected_constraint = constraint_map[constraint_choice]
        
        # Verify unconstrained source paths exist before execution
        source_dir = UNCONSTRAINED_MAP.get(selected_domain)
        if not source_dir or not os.path.exists(source_dir):
            print(f"\n[CRITICAL ERROR] Unconstrained source directory missing at: '{source_dir}'")
            print("Please ensure unconstrained base problems are generated first.")
            print("==================================================")
            continue

        constraint_folder = os.path.join(CONSTRAINED_MAP[selected_domain], selected_constraint)
        existing_count = count_constrained_instances(selected_domain, constraint_folder)

        print(f"\n[STATUS] Found {existing_count} existing {selected_domain} [{selected_constraint}] instances.")
        print("--------------------------------------------------")
        
        try:
            problems_num = int(input("\nHow many constrained instances do you want to secure?: ").strip())
            if problems_num <= 0:
                print("[ERROR] Please enter a valid positive integer.")
                continue

            print("--------------------------------------------------")
            print(f"[INFO] Launching ConstraintManager loop for {selected_domain} [{selected_constraint}]...")
            print("--------------------------------------------------")
            
            # Instantiate manager passing the maps directly from the UI layer
            manager = ConstraintManager(
                domain=selected_domain, 
                constraint=selected_constraint,
                unconstrained_mapping=UNCONSTRAINED_MAP,
                constrained_mapping=CONSTRAINED_MAP
            )
            manager.run_loop(count=problems_num, status_callback=ui_status_logger)

        except ValueError:
            print("[ERROR] Invalid numeric input. Please try again.")
        except KeyboardInterrupt:
            ui_status_logger("interrupted", None)
            break
        except Exception as e:
            print(f"\n[CRASH] A critical error occurred during execution:\n -> {e}")
            print("[INFO] Resetting system and recovering main menu...")
            
        print("==================================================")

if __name__ == "__main__":
    main()