import os
import re
import shutil

def get_highest_index(domain_name, target_dir):
    if not os.path.exists(target_dir):
        return 0

    highest_index = 0
    prefix = f"{domain_name}-"

    for entry in os.listdir(target_dir):
        if entry.startswith(prefix):
            base_name = entry.split('.')[0] if '.' in entry else entry
            try:
                parts = base_name.split("-")
                index = int(parts[-1])
                if index > highest_index:
                    highest_index = index
            except (ValueError, IndexError):
                continue
                
    return highest_index


def rename_problem(domain_name, output_dir, target_file_path=None):
    if not os.path.exists(output_dir) or not target_file_path or not os.path.exists(target_file_path):
        return None

    if not hasattr(rename_problem, "current_indices"):
        rename_problem.current_indices = {}
        
    if domain_name not in rename_problem.current_indices:
        highest_index = get_highest_index(domain_name, output_dir)
        rename_problem.current_indices[domain_name] = highest_index + 1

    final_id = rename_problem.current_indices[domain_name]
    rename_problem.current_indices[domain_name] += 1

    new_filename = f"{domain_name}-{final_id}.pddl"
    new_file_path = os.path.join(output_dir, new_filename)
    
    try:
        with open(target_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        match = re.search(r"\(define\s*\(\s*problem\s+([^\s\)]+)", content, re.IGNORECASE)
        if match:
            native_prob_name = match.group(1)
            new_prob_name = f"{domain_name}-{final_id}"
            
            # Sostituzione mirata sull'header
            pattern = r"(\(define\s*\(\s*problem\s+)" + re.escape(native_prob_name) + r"(\s*\))"
            if re.search(pattern, content, re.IGNORECASE):
                content = re.sub(pattern, r"\1" + new_prob_name + r"\2", content, flags=re.IGNORECASE)
            else:
                content = content.replace(f"problem {native_prob_name}", f"problem {new_prob_name}")
        
        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        if os.path.exists(new_file_path):
            os.remove(new_file_path)
            
        os.rename(target_file_path, new_file_path)
        return final_id
        
    except Exception as e:
        print(f"[ERROR util] Renaming failed: {e}")
        return None

def clear_domain_dirs(prob_dir, plan_dir):
    removed = 0
    targets = [prob_dir, plan_dir]
    
    for folder in targets:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                
                if os.path.isdir(file_path) or file == "domain.pddl":
                    continue
                    
                if file.endswith(".pddl") or file.endswith(".plan") or file.startswith("temp_") or file in ["output.sas", "sas_plan"]:
                    try:
                        os.remove(file_path)
                        removed += 1
                    except:
                        pass
                        
    return removed


def save_valid_instance(domain_name, candidate_path, local_plan, problems_dir, plans_dir):
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


def save_constrained_instance(domain_name, temp_domain_path, temp_problem_path, local_plan, base_constrained_dir):
    try:
        next_id = get_highest_index(domain_name, base_constrained_dir) + 1
        
        problem_folder_name = f"{domain_name}-{next_id}"
        target_problem_dir = os.path.join(base_constrained_dir, problem_folder_name)
        os.makedirs(target_problem_dir, exist_ok=True)
        
        temp_dest_prob = os.path.join(target_problem_dir, os.path.basename(temp_problem_path))
        shutil.move(temp_problem_path, temp_dest_prob)
        
        if not hasattr(rename_problem, "current_indices"):
            rename_problem.current_indices = {}
        rename_problem.current_indices[domain_name] = next_id
        
        final_id = rename_problem.current_indices[domain_name]
        rename_problem(domain_name, target_problem_dir, target_file_path=temp_dest_prob)

        final_domain_path = os.path.join(target_problem_dir, f"{domain_name}-{final_id}-domain.pddl")
        final_plan_path = os.path.join(target_problem_dir, f"{domain_name}-{final_id}.plan")

        if os.path.exists(temp_domain_path):
            shutil.move(temp_domain_path, final_domain_path)
        else:
            print(f"[ERROR util] Compiled domain not found at: {temp_domain_path}")
            return False

        if os.path.exists(local_plan):
            shutil.move(local_plan, final_plan_path)
        else:
            print(f"[ERROR util] Plan solution not found at: {local_plan}")
            return False

        print(f"[SUCCESS] Packaged dataset folder: {target_problem_dir}/ containing files.")
        return True

    except Exception as e:
        print(f"[ERROR util] Failed to save encapsulated constrained instance: {e}")
        return False
    
def extract_raw_goal_string(problem_pddl_path):
    if not os.path.exists(problem_pddl_path):
        return None

    try:
        with open(problem_pddl_path, "r", encoding="utf-8") as f:
            content = f.read()

        content_clean = re.sub(r";.*", "", content)
        match_start = re.search(r"\(:goal\s*", content_clean, re.IGNORECASE)
        if not match_start:
            return None

        start_index = match_start.end()
        bracket_level = 1
        goal_chars = []
        
        for char in content_clean[start_index:]:
            if char == '(':
                bracket_level += 1
            elif char == ')':
                bracket_level -= 1
            
            if bracket_level == 0:
                break
                
            goal_chars.append(char)

        raw_goal = "".join(goal_chars).strip()
        return re.sub(r"\s+", " ", raw_goal)

    except Exception:
        return None


def join_goal_and_rule(problem_pddl_path, ltl_rule_str):
    raw_goal_str = extract_raw_goal_string(problem_pddl_path)
    if not raw_goal_str:
        return ltl_rule_str

    s = raw_goal_str.strip()
    
    if s.lower().startswith("and "):
        s = s[4:].strip()
    elif s.lower().startswith("and("):
        s = s[3:].strip()
        if s.endswith(")"):
            s = s[:-1].strip()
        
    matches = re.findall(r"\(([^\s\)]+)\s*([^\)]*)\)", s)
    
    pltl_parts = []
    for pred, args in matches:
        pred = pred.strip()
        args = args.strip()
        
        if args:
            formatted_args = ", ".join(args.split())
            pltl_parts.append(f"{pred}({formatted_args})")
        else:
            pltl_parts.append(f"{pred}()")
            
    pylogics_goal = " & ".join(pltl_parts) if pltl_parts else s
    return f"({pylogics_goal}) & {ltl_rule_str}"