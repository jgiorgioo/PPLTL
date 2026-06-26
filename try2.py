import os
import sys
import shutil
import subprocess
import re
from pathlib import Path

# Assicuriamoci che i moduli locali siano visibili
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from constraints.constraints_manager import ConstraintManager
from utils import get_search_config

def run_full_diagnostic_test():
    # ---- CONFIGURAZIONE PARAMETRI DI TEST ----
    DOMAIN = "goldminer"
    CONSTRAINT = "obligation"  
    PROBLEM_FILE = "goldminer-59.pddl" 
    TARGET_OBJECT = "f6-4f"    
    
    print("=" * 75)
    print(f"   🚀 RUNNER DI DIAGNOSTICA AGGRESSIVA P4P + PLANNER: {DOMAIN.upper()}")
    print("=" * 75)
    
    # 1. Inizializzazione dei manager
    manager = ConstraintManager(domain=DOMAIN, constraint=CONSTRAINT)
    unconstrained_domain_path = os.path.join(manager.unconstrained_dir, "domain.pddl")
    unconstrained_problem_path = os.path.join(manager.unconstrained_dir, PROBLEM_FILE)
    
    # 2. Creazione cartella di test isolata
    test_out_dir = os.path.abspath("test_atomic_p4p")
    if os.path.exists(test_out_dir):
        shutil.rmtree(test_out_dir)
    os.makedirs(test_out_dir, exist_ok=True)
    
    print(f"[1/4] Compilazione in corso con il processor '{CONSTRAINT}'...")
    try:
        compilation_success = manager.constraint_processor.apply_constraint(
            unconstrained_domain_path,
            unconstrained_problem_path,
            test_out_dir,
            TARGET_OBJECT
        )
        print(f"  -> Esito apply_constraint: {compilation_success}")
    except Exception as e:
        print(f"[🚨 ERRORE CRITICO COMPILAZIONE]: {e}")
        return

    compiled_domain = os.path.join(test_out_dir, "domain.pddl")
    compiled_problem = os.path.join(test_out_dir, "problem.pddl")
    compiled_rule = os.path.join(test_out_dir, "rule.txt")
    
    # 3. Ispezione visiva dei file generati
    print(f"\n[2/4] Ispezione dei file generati in '{test_out_dir}':")
    if not os.path.exists(compiled_domain) or not os.path.exists(compiled_problem):
        print("  [ERRORE] Manno! I file domain o problem non sono stati generati.")
        return
        
    # Controlliamo la clausola del GOAL
    with open(compiled_problem, "r", encoding="utf-8") as f:
        prob_content = f.read()
    goal_match = re.search(r'\(:goal.*?\)', prob_content, re.DOTALL)
    if goal_match:
        print("\n--- GOAL RILEVATO NEL PROBLEM.PDDL ---")
        print(goal_match.group(0).strip())
        print("---------------------------------------")
    
    # Controlliamo i requisiti del DOMINIO
    with open(compiled_domain, "r", encoding="utf-8") as f:
        dom_content = f.read()
    req_match = re.search(r'\(:requirements.*?\)', dom_content, re.DOTALL)
    if req_match:
        print(f" -> Requisiti attivi nel dominio: {req_match.group(0).strip()}")

    print(f"\n[3/4] Configurazione del comando del Planner (Simulazione solver.py)...")
    search_config = get_search_config(DOMAIN)
    
    # Ricostruiamo lo script di Fast Downward puntando al percorso standard di solver.py
    fd_script = os.path.abspath(os.path.join(os.path.expanduser("~"), "downward", "fast-downward.py"))
    if not os.path.exists(fd_script):
        print(f"  [WARN] Fast Downward non trovato in '{fd_script}'. Provo ad usare l'eseguibile globale 'fast-downward'.")
        command = ["fast-downward", compiled_domain, compiled_problem, "--search", search_config]
    else:
        command = ["python3", fd_script, compiled_domain, compiled_problem, "--search", search_config]
        
    print(f" -> Comando pronto: {' '.join(command)}")

    print(f"\n[4/4] LANCIO DI FAST DOWNWARD (OUTPUT REALE & RAW) ...")
    print("-" * 75)
    sys.stdout.flush()
    
    # Puliamo eventuali file di piani vecchi rimasti in giro
    if os.path.exists("sas_plan"):
        os.remove("sas_plan")
    if os.path.exists("output.sas"):
        os.remove("output.sas")

    try:
        # Lanciamo deviano l'output del processo direttamente sullo schermo corrente (stdout/stderr)
        # Questo bypassa qualsiasi cattura o filtro e ti mostra gli errori di parsing in diretta!
        result = subprocess.run(
            command,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True,
            timeout=30
        )
        
        print("-" * 75)
        print(f"[ESITO] Fast Downward ha terminato l'esecuzione con Exit Code: {result.returncode}")
        
        if result.returncode == 0 and os.path.exists("sas_plan"):
            print("\n🎉 [SUCCESS] PIANO TROVATO CON SUCCESSO!")
            with open("sas_plan", "r") as p_file:
                print("--- PIANO GENERATO ---")
                print(p_file.read().strip())
                print("----------------------")
        else:
            print("\n❌ [FAIL] Il planner non ha generato una soluzione.")
            print("Guarda i log di Fast Downward stampati qui sopra per capire se si tratta di:")
            print(" - Un errore sintattico di parsing del traduttore (es: Undeclared symbol)")
            print(" - Un problema insoddisfacibile (Search stopped / proved unsolvable)")

    except subprocess.TimeoutExpired:
        print("-" * 75)
        print("[TIMEOUT] Il planner ha superato il limite di tempo critico di 30 secondi.")
    except Exception as e:
        print(f"[ERRORE DURANTE L'ESECUZIONE DEL PLANNER]: {e}")
        
    finally:
        # Pulizia del file temporaneo sas generato dal traduttore di FD
        if os.path.exists("output.sas"):
            try: os.remove("output.sas")
            except: pass

if __name__ == "__main__":
    run_full_diagnostic_test()