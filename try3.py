import os
from utils import solve
def test_solve():
    # 📂 Cartella corretta del tuo workspace (con il typo 'uncostrained')
    target_dir = os.path.abspath("plans/uncostrained/goldminer")
    
    domain_path = os.path.join(target_dir, "domain.pddl")
    problem_path = os.path.join(target_dir, "goldminer-59.pddl")
    
    # 🎯 Il file di output finale che desideri fuori nella root
    output_plan_path = os.path.abspath("goldminer-59_soluzione.plan")

    print("=" * 75)
    print("   🚀 TEST SOLVER: UTILIZZO DELLA FUNZIONE SOLVE NATIVA DEL PROGETTO")
    print("=" * 75)

    if not os.path.exists(domain_path):
        print(f"[ERRORE] Dominio non trovato in: {domain_path}")
        return
    if not os.path.exists(problem_path):
        print(f"[ERRORE] Problema nativo non trovato in: {problem_path}")
        return

    # 🎯 RISOLUZIONE DEL BUG DI PARSING:
    # Poiché _run_planner scrive a schermo "--search {search_config}", 
    # dobbiamo passargli l'UNICA stringa pulita che non si rompe con le virgolette in WSL:
    #Questa è la sintassi reale accettata da Fast Downward per i Landmark veloci:
    search_config = "eager_wastar([ff()], preferred=[ff()], w=3)"

    print(f"[INFO] Chiamata a solve() con configurazione: {search_config}...")
    print(f"[INFO] Destinazione finale del piano: {output_plan_path}\n")
    print("-" * 75)

    # Chiamiamo la funzione nativa che hai caricato in solver.py
    # Questa si occupa già internamente di lanciare Fast Downward, controllare il successo,
    # e spostare il file 'sas_plan' nel percorso definitivo 'output_plan_path' pulendo i residui!
    success = solve(
        domain_file=domain_path,
        problem_file=problem_path,
        search_config=search_config,
        output_plan_path=output_plan_path,
        timeout=30
    )

    if success and os.path.exists(output_plan_path):
        print("🎉 PIANO GENERATO CON SUCCESSO DALLA FUNZIONE SOLVE NATIVA!")
        print("-" * 75)
        print(f"📂 Il file soluzione è stato creato e spostato in:\n   {output_plan_path}")
        print("-" * 75)
        
        # Leggiamo il costo stampato nel piano
        with open(output_plan_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                if "cost" in line:
                    print(f"📊 {line.strip()}")
        print("-" * 75)
    else:
        print("❌ La funzione solve() nativa è fallita o l'istanza è stata considerata irrisolvibile.")
        print("[SUGGERIMENTO] Assicurati che l'ambiente python del tuo stage veda correttamente fast-downward nella home.")

if __name__ == "__main__":
    test_solve()