# ECS - Equation Calculation Sheet

ECS is a Domain Specific Language (DSL) for mathematical calculations, designed to make equation writing intuitive and readable. It supports variables, equations, scientific notation, roots, exponents, and physics blocks (ECSP).

## Installation

```bash
pip install ecs-equation
```

## Quick Start

```python
import ecs

# Load ECS sheets
ecs.add_sheet("constants")   # loads constants.ecs
ecs.add_sheet("main")        # loads main.ecs

# Get variable values
print(ecs.get("x"))          # 48
print(ecs.get("gravity"))    # 9.8
```

## ECS Syntax

### Variables

```ecs
// Basic assignment
x = 6(8)               // 48 (multiplication with parentheses)

// Addition/Subtraction (spaces required)
y = 12 + 3             // 15
z = (-5) + 10          // 5

// Division
a = (20)/(10)          // 2

// Exponentiation
b = (x)^(2)            // 2304

// Roots
r1 = (2)√(4)           // 2 (square root)
r2 = (3)root(27)       // 3 (cube root)

// Scientific notation
c1 = (1.23)e(10)
c2 = 1.23((10)^(10))
c3 = 1.23 * (10)^(10)

// Negative numbers (must be in parentheses)
d = (-7) + 3           // -4

// Indexed variables
y1(2) = 6
x3 = y1 + 1            // 4
```

### Quadratic Equations

ECS can solve quadratic equations automatically:

```ecs
0 = 4((x2)^2) - 6(x2) + 9
```

### Imports

Import other ECS files:

```ecs
import constants
import physics
```

### ECSP Blocks (Physics Blocks)

ECSP files support physics formula blocks:

```ecsp
spring = hooke{
    F = 20
    K = 4
    L_init = 3
    L_final = 8
}

gas = combined_gas_laws{
    t1 = 2
    p1 = 4
    v1 = 8
    t2 = 6
    p2 = 8
    v2 = ?   // unknown - will be solved automatically
}
```

Access block variables in ECS:

```ecs
force = spring.F
extension = spring.L_final - spring.L_init
```

## Python API

### `ecs.add_sheet(filename)`

Load an `.ecs` or `.ecsp` file. The extension is automatically detected.

```python
ecs.add_sheet("constants")   # loads constants.ecs
ecs.add_sheet("physics")     # loads physics.ecsp
```

### `ecs.get(var_name)`

Get a variable value. Supports dot notation for block variables.

```python
x = ecs.get("x")
spring_force = ecs.get("spring.F")
```

### `ecs.define_var(value)`

Dynamically define a new variable.

```python
ecs.define_var(42)      # defines X = 42
ecs.define_var(100)     # defines X2 = 100
```

## Syntax Rules

1. **Multiplication**: Must use parentheses - `6(8)` or `x(2)`
2. **Division**: Must use parentheses - `(20)/(10)`
3. **Addition/Subtraction**: Must have spaces - `12 + 3`, `(-5) + 10`
4. **Negative numbers**: Must be wrapped in parentheses - `(-7)`
5. **Exponentiation**: Must use parentheses - `(x)^(2)`
6. **Roots**: Use `(n)√(x)` or `(n)root(x)` syntax
7. **Scientific notation**: Use `(mantissa)e(exponent)` or `mantissa((10)^(exponent))`
8. **Variable reuse**: Overwriting a variable with a different value throws an error

## Example Files

### constants.ecs
```ecs
gravity = 9.8
pi = 3.14159
```

### main.ecs
```ecs
import constants

x = 6(8)
y = 12 + 3
result = (x)^(2) + gravity
```

## License

MIT License - see LICENSE file for details.
