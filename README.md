# PDDL+LTL Dataset Generator & Compiler

A Python tool designed for generating, validating, and compiling Automated Planning benchmarks (PDDL). The project supports the generation of standard base instances (unconstrained) grouped by difficulty layers, and the injection of Linear Temporal Logic constraints (LTL) using Plan4Past to create constrained planning datasets.

## Key Features

* **Supported Domains:** Generation logic for standard planning domains such as GridWorld, Sokoban, and Goldminer.
* **Automated Validation:** Every generated instance is tested with the Fast Downward planner and checked through VAL to ensure the problem is solvable and the plan is correct.
* **LTL Constraint Injection:** Automatically extracts valid targets and objects from base problems to compile rules (Avoidance, Obligation, Ordering) into standard PDDL axioms.
* **Error and Exception Handling:** Centralized management for common pipeline issues, such as planner timeouts, missing binaries, or instances that become unsolvable after applying constraints.
* **CLI Interface:** Terminal-based interactive menus to select domains, difficulty settings, and the number of instances to generate.

---

## Project Structure

```text
├── constraints/
│   ├── base_constraint.py       # Core logic for LTL injection and Plan4Past wrapper
│   ├── constraints_manager.py   # Main constrained pipeline loop management
│   ├── domain_constraints.py    # Domain-specific LTL formula definitions
│   ├── problem_sampler.py       # Logic for sampling and selecting base unconstrained instances
│   ├── target_extractors.py     # Functions to parse and extract valid LTL targets from PDDL files
│   └── target_sampler.py        # Logic for sampling valid combinations of extracted targets
├── generation/
│   ├── generators.py            # Python functions that wrap and launch the domain-specific scripts
│   └── generators_manager.py    # Unconstrained pipeline management logic
├── pddl-generators/
│   ├── goldminer/               # C++ source code and Makefile for Goldminer generator
│   ├── gridworld/               # Python source code and instance templates for GridWorld
│   └── sokoban/                 # Patched Python source code for Sokoban generator
├── utils/
│   ├── exceptions.py            # Global exception handler and dispatcher
│   ├── functions.py             # Shared utilities (I/O, indexing, loop orchestration)
│   ├── solver.py                # Execution wrapper for Fast Downward
│   └── validator.py             # Verification interface with VAL
├── generation_main.py           # Entry point for unconstrained base instance generation
└── constraints_main.py          # Entry point for LTL constraint compilation
```


## Prerequisites

The system requires the following tools to be installed and accessible within the system's PATH environment variables or correctly mapped inside the Python wrappers:

* **Python 3.10+** (heavily utilizes structural match/case syntax)
* **Fast Downward** (for problem resolution and feasibility filtering)
* **VAL (Validator for PDDL)** (for formal plan correctness verification)
* **Plan4Past / PLTL Parser** (for compiling LTL formulas into standard PDDL constructs)

---

## Compilation and Setup Guide

The system requires external planning, validation, and generation tools. They need to be compiled for thi system to work.

### 1. System Dependencies
Install the essential packages required for building the components:

```bash
sudo apt update && sudo apt install -y build-essential cmake g++ flex bison git python3
```

### 2. Compile Fast Downward (Planner)
Clone the repository into preferred directory (e.g., home folder):
```bash
cd ~ && git clone [https://github.com/aibasel/downward](https://github.com/aibasel/downward) && cd downward
```
Build the planner in optimized Release mode:
```bash
python3 build.py release
```

### 3. Compile VAL (PDDL Plan Validator)
Clone the VAL repository:
```bash
cd ~ && git clone [https://github.com/KCL-Planning/VAL](https://github.com/KCL-Planning/VAL) && cd VAL
```
Configure the CMake environment and compile:
```bash
mkdir -p build && cd build
cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --config Release
```

### 4. Compile the Goldminer Generator
The PDDL generators originate from the official IPC benchmarks. To compile the Goldminer tool, navigate to the generator source directory inside the project:
```bash
cd PPLTL/pddl-generators/goldminer
```
Compile the executable using the native Makefile:
```bash
make
```
#### Configuration
After compiling the required binaries, the core modules will automatically search for them within your home (`~`) directory using `os.path.expanduser`. 

If your installation paths differ, you must manually override the return statements inside these functions:

* **Fast Downward Path:** Open `utils/solver.py` and modify the path in `_get_default_fd_path()` (defaults to `~/downward/fast-downward.py`).
* **VAL Path:** Open `utils/validator.py` and modify the path in `_get_default_val_path()` (defaults to `~/VAL/build/bin/Validate`).
* 
### 5. Python Dependencies

Unlike the native binaries, the LTL parser/compiler component must be installed directly as a Python library via `pip`:

```bash
pip install plan4past
```
---

## Usage Guide

### 1. Generating the Base Dataset (Unconstrained)
Before applying any logical constraint, you need to populate the dataset with base planning problems. Launch the primary generation script:

```bash
python generation_main.py
```

The tool will save the verified `.pddl` files and their corresponding `.plan` solutions inside the `plans/unconstrained/domain/*/` directory.

### 2. Compiling LTL Constraints (Constrained)
Once the unconstrained base instances are generated, you can enrich them by injecting LTL constraints:

```bash
python constraints_main.py
```

* **The Constraint Type** to apply:
  * **Avoidance:** Prevents certain states or interactions with specific target objects.
  * **Obligation:** Forces the satisfaction of intermediate conditions during the execution trace.
  * **Ordering:** Imposes a strict sequential order when reaching sub-goals.

The system will automatically extract eligible targets, compile the LTL rule, clean up redundant PDDL object structures, verify the solubility of the new combined problem, and package everything into isolated subdirectories under `plans/constrained/`.

---

### Error Handling

* **Unsolvable Constraints (Skipped):** If injecting an LTL rule renders a problem mathematically impossible to solve due to object configurations, the instance is silently discarded and the tool moves to the next seed.
* **Timeouts:** If the solver exceeds the predefined time limit (default: `20 seconds`), the execution is safely aborted to prevent hardware deadlocks.
* **System Crashes:** Any unexpected I/O or parsing error is isolated as an `unknown_error`, logged to the terminal, and bypassed, allowing the batch to complete the remaining requested generations.

---

### 🌐 Acknowledgments & Tool Sources

The PDDL generators and LTL compilation tools integrated into this framework are sourced from the following official repositories:

* **Goldminer & GridWorld Generators:** Sourced from the official [AI-Planning PDDL Generators](https://github.com/AI-Planning/pddl-generators) repository.
* **Sokoban Generator:** Sourced from the [IPC 2023 Learning Track Benchmarks](https://github.com/ipc2023-learning/benchmarks/tree/main/sokoban).
* **Plan4Past (P4P):** Sourced from on [GitHub](https://github.com/whitemech/Plan4Past).

---