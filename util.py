import os
import re
import shutil

def rename_problem(domain_name, output_dir, target_file_path=None):
    """
    Rinomina il file PDDL aggiornando l'indice progressivo interno.
    Usa target_file_path per rinominare direttamente il file temporaneo standardizzato.
    """
    if not os.path.exists(output_dir):
        return None

    target_file = target_file_path

    if not target_file or not os.path.exists(target_file):
        return None

    # Inizializza i dizionari degli indici se non esistono
    if not hasattr(rename_problem, "current_indices"):
        rename_problem.current_indices = {}
        
    # Trova l'indice più alto già presente nella cartella per non sovrascrivere i file esistenti
    if domain_name not in rename_problem.current_indices:
        highest_index = 0
        prefix = f"{domain_name}-"
        for filename in os.listdir(output_dir):
            if filename.startswith(prefix) and filename.endswith(".pddl"):
                try:
                    parts = filename.replace(".pddl", "").split("-")
                    index = int(parts[-1])
                    if index > highest_index:
                        highest_index = index
                except (ValueError, IndexError):
                    continue
        rename_problem.current_indices[domain_name] = highest_index + 1

    final_id = rename_problem.current_indices[domain_name]
    rename_problem.current_indices[domain_name] += 1

    new_filename = f"{domain_name}-{final_id}.pddl"
    new_file_path = os.path.join(output_dir, new_filename)
    
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Sostituisce il nome del problema all'interno del file PDDL (es. (problem gridworld-1))
        match = re.search(r"\(define\s+\(problem\s+([^\s\)]+)", content)
        if match:
            native_prob_name = match.group(1)
            content = content.replace(f"(problem {native_prob_name})", f"(problem {domain_name}-{final_id})")
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        if os.path.exists(new_file_path):
            os.remove(new_file_path)
            
        os.rename(target_file, new_file_path)
        return final_id
        
    except Exception as e:
        print(f"[ERROR] Renaming failed for {target_file}. Reason: {e}")
        return None

def clear_domain_dirs(prob_dir, plan_dir):
    """
    Pulisce i file PDDL, i piani (.plan) e i residui temporanei dalle directory.
    Preserva rigorosamente il file 'domain.pddl'.
    Ritorna il numero di file eliminati.
    """
    removed = 0
    targets = [prob_dir, plan_dir]
    
    for folder in targets:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                
                # Ignora le sottocartelle e preserva il file del dominio fisso
                if os.path.isdir(file_path) or file == "domain.pddl":
                    continue
                    
                # Rimuove solo istanze numerate, piani e file temporanei/intermedi
                if file.endswith(".pddl") or file.endswith(".plan") or file.startswith("temp_") or file in ["output.sas", "sas_plan"]:
                    try:
                        os.remove(file_path)
                        removed += 1
                    except:
                        pass
                        
    return removed

def save_valid_instance(domain_name, candidate_path, local_plan, problems_dir, plans_dir):
    """Handles the naming, movement, and persistence of validated PDDL problems and plans."""
    try:
        final_id = rename_problem(domain_name, problems_dir, target_file_path=candidate_path)
        if final_id is not None:
            os.makedirs(plans_dir, exist_ok=True)
            dest_plan_path = os.path.join(plans_dir, f"{domain_name}-{final_id}.plan")
            shutil.move(local_plan, dest_plan_path)
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Failed to save instance: {e}")
        return False