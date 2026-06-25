import os
import subprocess
import sys
import shutil
from utils import get_search_config

def _get_default_val_path():
    """Recupera il percorso assoluto del binario di VAL preso dal tuo validator.py"""
    return os.path.abspath(os.path.join(os.path.expanduser("~"), "VAL", "build", "bin", "Validate"))

def run_val_diagnostic():
    test_dir = os.path.abspath("test_atomic_p4p")
    domain_path = os.path.join(test_dir, "domain.pddl")
    problem_path = os.path.join(test_dir, "problem.pddl")
    plan_path = os.path.join(test_dir, "sas_plan_debug.plan")
    
    print("=" * 75)
    print("   🔍 DETECTIVE LOG: GENERAZIONE PIANO & VAL VERBOSE ANALYSIS")
    print("=" * 75)
    
    if not os.path.exists(domain_path) or not os.path.exists(problem_path):
        print("[ERRORE] File PDDL non trovati in 'test_atomic_p4p/'.")
        print("Esegui prima 'try2.py' per generare il dominio e il problema.")
        return

    # 1. GENERAZIONE DEL PIANO FRESH CON FAST DOWNWARD
    print("[1/2] Lancio di Fast Downward per catturare il piano...")
    search_config = get_search_config("goldminer")
    fd_script = os.path.abspath(os.path.join(os.path.expanduser("~"), "downward", "fast-downward.py"))
    
    if os.path.exists("sas_plan"): os.remove("sas_plan")
    
    if not os.path.exists(fd_script):
        fd_command = ["fast-downward", domain_path, problem_path, "--search", search_config]
    else:
        fd_command = ["python3", fd_script, domain_path, problem_path, "--search", search_config]
        
    fd_result = subprocess.run(fd_command, capture_output=True, text=True, timeout=20)
    
    if fd_result.returncode == 0 and os.path.exists("sas_plan"):
        shutil.move("sas_plan", plan_path)
        print(f"  -> 🎉 PIANO GENERATO dal solver e congelato in:\n     {plan_path}")
    else:
        print("\n❌ [ERRORE PLANNER] Impossibile generare il piano.")
        return

    # 2. INVOCAZIONE DI VAL DAL TUO PATH SPECIFICO CON FLAG -v
    print("\n[2/2] Lancio di VAL in modalità Verbose dal tuo percorso custom...")
    val_binary = _get_default_val_path()
    
    if not os.path.exists(val_binary):
        print(f"[ERRORE] Il binario di VAL non esiste in: {val_binary}")
        return
        
    val_command = [val_binary, "-v", domain_path, problem_path, plan_path]
    print(f"Comando VAL: {' '.join(val_command)}\n")
    print("-" * 75)
    
    try:
        result = subprocess.run(val_command, capture_output=True, text=True, timeout=15)
        stdout_lines = result.stdout.splitlines()
        
        print("--- 📋 REQUISITI E STATO INIZIALE LETTI DA VAL ---")
        in_checking_phase = False
        
        for line in stdout_lines:
            if "Checking plan" in line or "Plan size" in line:
                print("\n" + "-"*50)
                print("--- 🚀 INIZIO VALUTAZIONE DEL PIANO PASSO-PASSO ---")
                print("-"*50)
                in_checking_phase = True
            
            if "detonate-bomb" in line.lower() or "clear-rock" in line.lower():
                print(f"\n👉 ACTION CRITICA: {line.strip()}")
                continue
                
            if "Adding derived" in line or "Deleting derived" in line:
                print(f"  [DERIVED ATOM] {line.strip()}")
                continue
                
            if "Precondition failed" in line or "Bad plan" in line or "Goal not achieved" in line:
                print(f"\n❌ [CRITICAL VAL FAIL]: {line.strip()}")
                continue
                
            if in_checking_phase and ("Step" in line or "Fact" in line or "Checking" in line):
                print(f"  {line.strip()}")
            elif not in_checking_phase:
                print(line.strip())
                
        print("\n" + "="*75)
        print("Exit Code finale di VAL:", result.returncode)
        print("=" * 75)

    except subprocess.TimeoutExpired:
        print("[TIMEOUT] VAL ha superato i 15 secondi.")

if __name__ == "__main__":
    run_val_diagnostic()