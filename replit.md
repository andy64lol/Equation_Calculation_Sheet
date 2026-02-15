# ECS - Equation Calculation Sheet

## Overview
ECS is a Python library implementing a Domain Specific Language (DSL) for mathematical calculations. It supports variables, equations, scientific notation, roots, exponents, quadratic equation solving, and physics blocks (ECSP).

This is a library/package project (not a web application). The main entry point for demonstration is `ecs/example/main.py`.

## Project Architecture

### Structure
```
ecs/                    # Main package
  __init__.py           # Public API: add_sheet(), get(), define_var()
  interpreter.py        # Core interpreter engine (ECS/ECSP parser & evaluator)
  example/              # Example usage
    main.py             # Demo script showing all features
    constants.ecs       # Example constants file
    main.ecs            # Example ECS equations file
    physics.ecsp        # Example ECSP physics blocks file
pyproject.toml          # Package build configuration
setup.py                # Alternative setup script
```

### Key Components
- **Interpreter** (`ecs/interpreter.py`): Parses `.ecs` and `.ecsp` files, evaluates expressions, solves quadratics, handles physics blocks
- **ECSPBlock**: Handles physics formula blocks (Hooke's Law, Combined Gas Laws)
- **Public API** (`ecs/__init__.py`): Simple interface with `add_sheet()`, `get()`, `define_var()`

### Languages & Tools
- Python 3.12
- No external dependencies (uses only stdlib: os, re, math)
- Build system: setuptools

## Recent Changes
- 2026-02-15: Fixed parsing order so quadratic equations (0 = ...) are checked before assignments
- 2026-02-15: Fixed quadratic example equation to have real solutions
- 2026-02-15: Added indexed variable assignment support (e.g., `y1(2) = 6`)
- 2026-02-15: Added explicit `*` multiplication operator support
- 2026-02-15: Initial Replit setup with workflow configuration
