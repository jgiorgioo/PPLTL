import sys

from constraints_manager import ConstraintManager

def ui_status_logger(event_type, data):
    """Callback function handling all screen outputs for the LTL constraint pipeline."""
    if event_type == "init":
        print(f"Initial progress: {data['current']} constrained instances found. Final target: {data['target']}")
    elif event_type == "attempt":
        print("[DEBUG] Extracting targets, compiling LTL rule and testing solver...", flush=True)
    elif event_type == "success":
        print(f"  └─> VALIDATED AND PACKAGED! -> Progress: {data['current']}/{data['target']}")
    elif event_type == "failed":
        print("  └─> Discarded (Unsolvable target or LTL compilation error).")
    elif event_type == "finished":
        print(f"\n[OK] Success! Generated all constrained instances for {data['prefix']}.")
    elif event_type == "interrupted":
        print("\n\n[WARNING] Batch execution interrupted by user (Ctrl+C). Cleaning up work space...")

def get_choice(prompt, valid_choices):
    """UI Helper: Manages user input on the terminal."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid_choices:
            return choice
        print(f"Invalid input. Please choose among: {', '.join(valid_choices)}")

def main():
    print("==================================================")
    print("            PDDL+LTL DATASET COMPILER TOOL        ")
    print("==================================================")
    
    print("Select Domain:")
    print("  [1] GridWorld")
    print("  [2] Sokoban [Coming Soon]")
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
    constraint_choice = get_choice("Select constraint option: ", ["1", "2","3"])
    
    domain_map = {"1": "gridworld", "2": "sokoban", "3": "goldminer"}
    constraint_map = {"1": "avoidance", "2": "obligation", "3": "ordering"}
    
    selected_domain = domain_map[domain_choice]
    selected_constraint = constraint_map[constraint_choice]
    
    try:
        problems_num = int(input("\nHow many constrained instances do you want to secure?: ").strip())
        if problems_num <= 0: raise ValueError
    except ValueError:
        print("Error: Please enter a valid positive integer.")
        sys.exit(1)

    print("--------------------------------------------------")
    print(f"[INFO] Launching ConstraintManager loop for {selected_domain} [{selected_constraint}]...")
    print("--------------------------------------------------")
    
    try:
        manager = ConstraintManager(domain=selected_domain, constraint=selected_constraint)
        manager.run_loop(count=problems_num, status_callback=ui_status_logger)

    except NotImplementedError as nie:
        print(f"\n[ERROR] {nie}")
    except KeyboardInterrupt:
        ui_status_logger("interrupted", None)

    print("==================================================")

if __name__ == "__main__":
    main()