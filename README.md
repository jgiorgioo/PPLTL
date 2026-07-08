# PDDL+LTL Dataset Generator & Compiler Tool

A modular and robust Python framework designed for the automatic generation, formal validation, and compilation of Automated Planning benchmarks (PDDL). The system supports both flat instance generation (unconstrained) divided by difficulty strata, and the dynamic injection of Linear Temporal Logic constraints over the past/present (PLTL/LTL) via Plan4Past integration, ensuring pure and mathematically sound synthetic datasets.

## Key Features

* **Multi-Domain Generation:** Native support for classic planning domains including GridWorld, Sokoban, and Goldminer.
* **Feasibility Filtering and Strict Validation:** Every generated instance is preemptively tested with the Fast Downward planner and formally validated through VAL before being archived into the definitive dataset.
* **Integrated LTL Constraint Compiler:** Automatically extracts valid targets and objects from base problems, compiles logical rules (Avoidance, Obligation, Ordering), and injects them into the domain by transforming them into standard PDDL axioms.
* **Centralized Error Handling:** Fault-tolerant architecture based on a universal generic loop and a centralized exception manager natively handling timeouts, missing solver binaries, and logically unsolvable constraints.
* **Interactive CLI Interface:** Intuitive terminal-driven menus to configure parallel or sequential batch-generation sessions.

---

## Project Structure

```text
├── constraints/
│   ├── __init__.py
│   ├── base_constraint.py       # Logic for injection and cleanup of LTL constraints
│   └── constraints_manager.py   # Candidate exploration and sampling logic
├── utils/
│   ├── __init__.py
│   ├── exceptions.py            # Global exception handler and dispatcher
│   ├── functions.py             # Shared utilities (I/O, indexing, loop orchestration)
│   ├── solver.py                # Execution wrapper for Fast Downward
│   └── validator.py             # Verification interface with VAL
├── generation_main.py           # Entry point for unconstrained base instance generation
└── constraints_main.py          # Entry point for LTL constraint compilation
```


## Prerequisites

The system requires the following tools to be installed and accessible within your system's PATH environment variables or correctly mapped inside the Python wrappers:

* **Python 3.10+** (heavily utilizes structural match/case syntax)
* **Fast Downward** (for problem resolution and feasibility filtering)
* **VAL (Validator for PDDL)** (for formal plan correctness verification)
* **Plan4Past / PLTL Parser** (for compiling LTL formulas into standard PDDL constructs)

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