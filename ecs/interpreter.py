"""
ECS Interpreter - Core engine for parsing and executing ECS/ECSP files.
Fixed version with improved error handling and English comments.
"""

import os
import re
import math


class ECSPBlock:
    """Represents an ECSP block with a type and variables."""

    def __init__(self, name, block_type):
        self.name = name
        self.block_type = block_type
        self.variables = {}
        self.unknowns = set()

    def set_variable(self, var_name, value):
        """Set a variable in the block."""
        self.variables[var_name] = value

    def mark_unknown(self, var_name):
        """Mark a variable as unknown (to be solved)."""
        self.unknowns.add(var_name)

    def get_variable(self, var_name):
        """Get a variable value."""
        if var_name in self.variables:
            return self.variables[var_name]
        raise ValueError(
            f"Variable '{var_name}' not found in block '{self.name}'")

    def solve_unknowns(self):
        """Solve for unknown variables based on block type."""
        if self.block_type == "hooke":
            # Hooke's Law: F = K * (L_final - L_init)
            K = self.variables.get("K", 0)
            L_init = self.variables.get("L_init", 0)
            L_final = self.variables.get("L_final", 0)
            F = self.variables.get("F", 0)

            if "F" in self.unknowns:
                self.variables["F"] = K * (L_final - L_init)
                self.unknowns.discard("F")
            elif "K" in self.unknowns and (L_final - L_init) != 0:
                self.variables["K"] = F / (L_final - L_init)
                self.unknowns.discard("K")
            elif "L_final" in self.unknowns and K != 0:
                self.variables["L_final"] = (F / K) + L_init
                self.unknowns.discard("L_final")
            elif "L_init" in self.unknowns and K != 0:
                self.variables["L_init"] = L_final - (F / K)
                self.unknowns.discard("L_init")

            # Extension L = L_final - L_init
            if "L" in self.unknowns:
                self.variables["L"] = self.variables.get(
                    "L_final", 0) - self.variables.get("L_init", 0)
                self.unknowns.discard("L")

        elif self.block_type == "combined_gas_laws":
            # Combined Gas Law: (P1*V1)/T1 = (P2*V2)/T2
            p1 = self.variables.get("p1", 0)
            v1 = self.variables.get("v1", 0)
            t1 = self.variables.get("t1", 0)
            p2 = self.variables.get("p2", 0)
            v2 = self.variables.get("v2", 0)
            t2 = self.variables.get("t2", 0)

            # Ensure temperature is not zero to avoid division by zero
            left_side = (p1 * v1) / t1 if t1 != 0 else 0

            if "v2" in self.unknowns and t2 != 0 and p2 != 0:
                self.variables["v2"] = (left_side * t2) / p2
                self.unknowns.discard("v2")
            elif "p2" in self.unknowns and t2 != 0 and v2 != 0:
                self.variables["p2"] = (left_side * t2) / v2
                self.unknowns.discard("p2")
            elif "t2" in self.unknowns and p2 != 0 and v2 != 0:
                self.variables["t2"] = (
                    p2 * v2) / left_side if left_side != 0 else 0
                self.unknowns.discard("t2")
            elif "p1" in self.unknowns and t1 != 0 and v1 != 0:
                self.variables["p1"] = (p2 * v2 * t1) / (
                    t2 * v1) if t2 != 0 and v1 != 0 else 0
                self.unknowns.discard("p1")
            elif "v1" in self.unknowns and t1 != 0 and p1 != 0:
                self.variables["v1"] = (p2 * v2 * t1) / (
                    t2 * p1) if t2 != 0 and p1 != 0 else 0
                self.unknowns.discard("v1")
            elif "t1" in self.unknowns and p1 != 0 and v1 != 0:
                self.variables["t1"] = (p1 * v1 * t2) / (
                    p2 * v2) if p2 != 0 and v2 != 0 else 0
                self.unknowns.discard("t1")

        elif self.block_type == "ohm_law":
            # Ohm's Law: V = I * R
            v = self.variables.get("v", 0)
            i = self.variables.get("i", 0)
            r = self.variables.get("r", 0)
            if "v" in self.unknowns:
                self.variables["v"] = i * r
                self.unknowns.discard("v")
            elif "i" in self.unknowns and r != 0:
                self.variables["i"] = v / r
                self.unknowns.discard("i")
            elif "r" in self.unknowns and i != 0:
                self.variables["r"] = v / i
                self.unknowns.discard("r")

        elif self.block_type == "kinematics":
            # Kinematics equations: v = u + at, s = ut + 0.5at^2
            v = self.variables.get("v", 0)
            u = self.variables.get("u", 0)
            a = self.variables.get("a", 0)
            t = self.variables.get("t", 0)
            
            if "v" in self.unknowns:
                self.variables["v"] = u + (a * t)
                self.unknowns.discard("v")
            if "s" in self.unknowns:
                self.variables["s"] = (u * t) + (0.5 * a * (t**2))
                self.unknowns.discard("s")

        elif self.block_type == "energy":
            # Energy equations: KE = 0.5 * m * v^2, PE = m * g * h
            m = self.variables.get("m", 0)
            v = self.variables.get("v", 0)
            g = self.variables.get("g", 9.8)
            h = self.variables.get("h", 0)

            if "KE" in self.unknowns:
                self.variables["KE"] = 0.5 * m * (v**2)
                self.unknowns.discard("KE")
            if "PE" in self.unknowns:
                self.variables["PE"] = m * g * h
                self.unknowns.discard("PE")

        elif self.block_type == "projectile_motion":
            # Projectile motion equations
            v0 = self.variables.get("v0", 0)
            theta_deg = self.variables.get("theta", self.variables.get("θ", 0))
            theta = math.radians(theta_deg)
            g = self.variables.get("g", 9.8)

            if "R" in self.unknowns:
                self.variables["R"] = (v0**2 * math.sin(2 * theta)) / g
                self.unknowns.discard("R")
            if "t" in self.unknowns:
                self.variables["t"] = (2 * v0 * math.sin(theta)) / g
                self.unknowns.discard("t")
            if "H" in self.unknowns:
                self.variables["H"] = (v0**2 * (math.sin(theta)**2)) / (2 * g)
                self.unknowns.discard("H")

        elif self.block_type == "circular_motion":
            # Circular motion: F = (m * v^2) / r
            m = self.variables.get("m", 0)
            v = self.variables.get("v", 0)
            r = self.variables.get("r", 1)
            if "F" in self.unknowns and r != 0:
                self.variables["F"] = (m * (v**2)) / r
                self.unknowns.discard("F")

        elif self.block_type == "work_power":
            # Work and power: W = F * d, P = W / t
            f = self.variables.get("F", 0)
            d = self.variables.get("d", 0)
            t = self.variables.get("t", 1)

            if "W" in self.unknowns:
                self.variables["W"] = f * d
                self.unknowns.discard("W")
            if "P" in self.unknowns:
                w = self.variables.get("W", f * d)
                if t != 0:
                    self.variables["P"] = w / t
                    self.unknowns.discard("P")


class Interpreter:
    """Main interpreter for ECS and ECSP files."""

    def __init__(self):
        self.variables = {}
        self.blocks = {}
        self.imported_files = set()
        self.dynamic_var_counter = 0

    def load_sheet(self, filename):
        """Load an .ecs or .ecsp file."""
        # Try .ecs first, then .ecsp
        ecs_path = f"{filename}.ecs"
        ecsp_path = f"{filename}.ecsp"

        if os.path.exists(ecs_path):
            self._parse_ecs_file(ecs_path)
        elif os.path.exists(ecsp_path):
            self._parse_ecsp_file(ecsp_path)
        else:
            raise FileNotFoundError(
                f"Error: No .ecs or .ecsp file found for '{filename}'")

    def _parse_ecs_file(self, filepath):
        """Parse an .ecs file."""
        with open(filepath, 'r') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            self._parse_ecs_line(line, line_num, filepath)

    def _parse_ecs_line(self, line, line_num, filepath):
        """Parse a single line from an .ecs file."""
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('//'):
            return

        # Handle imports
        if line.startswith('import '):
            import_name = line[7:].strip()
            if import_name not in self.imported_files:
                self.imported_files.add(import_name)
                self.load_sheet(import_name)
            return

        # Handle quadratic equation (0 = ...)
        if line.startswith('0 ='):
            self._handle_quadratic(line, line_num)
            return

        # Handle variable assignment
        if '=' in line and '{' not in line:
            self._handle_assignment(line, line_num)
            return

    def _handle_assignment(self, line, line_num):
        """Handle variable assignment."""
        # Split on first =
        parts = line.split('=', 1)
        if len(parts) != 2:
            return

        var_name = parts[0].strip()
        expr = parts[1].strip()

        # Remove inline comments
        if '//' in expr:
            expr = expr.split('//')[0].strip()

        # Handle indexed variable assignment: var(n) = value means var * n = value
        indexed_assign = re.match(r'^(\w+)\((\d+)\)$', var_name)
        if indexed_assign:
            actual_var = indexed_assign.group(1)
            index = float(indexed_assign.group(2))
            try:
                value = self._evaluate_expression(expr)
            except Exception as e:
                raise ValueError(
                    f"Error evaluating expression at line {line_num}: {e}")
            if index != 0:
                value = value / index
            self.variables[actual_var] = self._approximate(value)
            return

        # Check for block variable access (block.var)
        if '.' in var_name:
            raise ValueError(
                f"Error: Cannot assign to block variable directly at line {line_num}"
            )

        # Evaluate the expression
        try:
            value = self._evaluate_expression(expr)
        except Exception as e:
            raise ValueError(
                f"Error evaluating expression at line {line_num}: {e}")

        # Check for inconsistent redefinition
        if var_name in self.variables:
            old_value = self.variables[var_name]
            # Allow if values are the same (or very close for floats)
            if isinstance(old_value,
                          (int, float)) and isinstance(value, (int, float)):
                if abs(old_value - value) > 0.0001:
                    raise ValueError(
                        f"Error: '{var_name}' is inconsistent at line {line_num}"
                    )
            elif old_value != value:
                raise ValueError(
                    f"Error: '{var_name}' is inconsistent at line {line_num}")

        self.variables[var_name] = value

    def _handle_quadratic(self, line, line_num):
        """Handle quadratic equation of form 0 = a((x)^2) + b(x) + c."""
        # Extract the equation part after 0 =
        eq_part = line[3:].strip()

        # Find the variable name (look for pattern like ((x2)^2))
        var_match = re.search(r'\(\((\w+)\)\^2\)', eq_part)
        if not var_match:
            # Try alternative pattern
            var_match = re.search(r'\((\w+)\)\^2', eq_part)
            if not var_match:
                raise ValueError(
                    f"Error: Cannot parse quadratic equation at line {line_num}"
                )

        var_name = var_match.group(1)

        # Parse coefficients
        temp_eq = eq_part.replace(f"(({var_name})^2)", "QUAD_TERM")
        temp_eq = temp_eq.replace(f"({var_name})", "LINEAR_TERM")

        # Extract coefficients
        a_coef = 0
        b_coef = 0
        c_coef = 0

        # Find coefficient for squared term
        quad_match = re.search(r'([+-]?\s*\d*\.?\d*)\s*QUAD_TERM', temp_eq)
        if quad_match:
            coef_str = quad_match.group(1).replace(' ', '')
            if coef_str == '+' or coef_str == '':
                a_coef = 1
            elif coef_str == '-':
                a_coef = -1
            else:
                try:
                    a_coef = float(coef_str)
                except ValueError:
                    # Evaluate expression if not a simple number
                    a_coef = self._evaluate_expression(coef_str)

        # Find coefficient for linear term
        linear_match = re.search(r'([+-]?\s*\d*\.?\d*)\s*LINEAR_TERM', temp_eq)
        if linear_match:
            coef_str = linear_match.group(1).replace(' ', '')
            if coef_str == '+' or coef_str == '':
                b_coef = 1
            elif coef_str == '-':
                b_coef = -1
            else:
                try:
                    b_coef = float(coef_str)
                except ValueError:
                    # Evaluate expression if not a simple number
                    b_coef = self._evaluate_expression(coef_str)

        # Find constant term (remaining numbers)
        remaining = temp_eq.replace(
            quad_match.group(0) if quad_match else '', '')
        remaining = remaining.replace(
            linear_match.group(0) if linear_match else '', '')
        remaining = remaining.replace('QUAD_TERM',
                                      '').replace('LINEAR_TERM', '')
        remaining = remaining.strip()

        # Extract constant
        const_match = re.search(r'([+-]?\s*\d+\.?\d*)', remaining)
        if const_match:
            coef_str = const_match.group(1).replace(' ', '')
            try:
                c_coef = float(coef_str)
            except ValueError:
                # Evaluate expression if not a simple number
                c_coef = self._evaluate_expression(coef_str)

        # Solve quadratic: ax^2 + bx + c = 0
        discriminant = b_coef**2 - 4 * a_coef * c_coef

        if discriminant < 0:
            print(
                f"Warning: Negative discriminant for equation at line {line_num}: {line}"
            )
            return

        # Use quadratic formula
        solution = 0
        if a_coef != 0:
            x1 = (-b_coef + math.sqrt(discriminant)) / (2 * a_coef)
            x2 = (-b_coef - math.sqrt(discriminant)) / (2 * a_coef)
            # Store the positive solution or first solution
            solution = x1 if x1 >= 0 else x2
        else:
            # Linear equation
            if b_coef != 0:
                solution = -c_coef / b_coef
            else:
                raise ValueError(f"Error: Invalid equation at line {line_num}")

        # Check for inconsistent redefinition
        if var_name in self.variables:
            old_value = self.variables[var_name]
            if abs(old_value - solution) > 0.0001:
                raise ValueError(
                    f"Error: '{var_name}' is inconsistent at line {line_num}")

        self.variables[var_name] = self._approximate(solution)

    def _parse_ecsp_file(self, filepath):
        """Parse an .ecsp file."""
        with open(filepath, 'r') as f:
            content = f.read()

        # Parse blocks
        block_pattern = r'(\w+)\s*=\s*(\w+)\s*\{([^}]*)\}'
        blocks = re.findall(block_pattern, content, re.DOTALL)

        for block_name, block_type, block_content in blocks:
            block = ECSPBlock(block_name, block_type)

            # Parse variables inside block
            for line in block_content.strip().split('\n'):
                line = line.strip()
                if not line or line.startswith('//'):
                    continue

                if '=' in line:
                    parts = line.split('=', 1)
                    var_name = parts[0].strip()
                    value_str = parts[1].strip()

                    # Remove inline comments
                    if '//' in value_str:
                        value_str = value_str.split('//')[0].strip()

                    if value_str == '?':
                        block.mark_unknown(var_name)
                    else:
                        try:
                            value = self._evaluate_expression(value_str)
                            block.set_variable(var_name, value)
                        except Exception as e:
                            # Try to evaluate as number directly
                            try:
                                value = float(value_str)
                                block.set_variable(var_name, value)
                            except:
                                raise ValueError(
                                    f"Error parsing variable '{var_name}' in block '{block_name}': {e}"
                                )

            # Solve unknowns
            block.solve_unknowns()
            self.blocks[block_name] = block

    def _evaluate_expression(self, expr):
        """Evaluate an ECS expression."""
        expr = expr.strip()

        # Handle block variable access (block.var)
        if '.' in expr:
            parts = expr.split('.')
            if len(parts) == 2:
                block_name, var_name = parts[0], parts[1]
                if block_name in self.blocks:
                    return self.blocks[block_name].get_variable(var_name)

        # Handle scientific notation: (1.23)e(10)
        sci_pattern = r'\(([\d.]+)\)e\(([\d]+)\)'
        sci_matches = re.findall(sci_pattern, expr)
        for mantissa, exp in sci_matches:
            replacement = str(float(mantissa) * (10**int(exp)))
            expr = expr.replace(f"({mantissa})e({exp})", replacement)

        # Handle roots: (n)√(x) or (n)root(x)
        root_pattern = r'\((\d+)\)√\(([^)]+)\)'
        expr = re.sub(
            root_pattern, lambda m: str(
                self._nth_root(self._evaluate_expression(m.group(2)),
                               int(m.group(1)))), expr)

        root_pattern2 = r'\((\d+)\)root\(([^)]+)\)'
        expr = re.sub(
            root_pattern2, lambda m: str(
                self._nth_root(self._evaluate_expression(m.group(2)),
                               int(m.group(1)))), expr)

        # Handle exponentiation: (x)^(y)
        while True:
            exp_match = re.search(r'\(([^()]+)\)\^\(([^()]+)\)', expr)
            if not exp_match:
                break

            base = self._evaluate_expression(exp_match.group(1))
            exp = self._evaluate_expression(exp_match.group(2))
            result = base**exp
            expr = expr[:exp_match.start()] + str(
                result) + expr[exp_match.end():]

        # Handle multiplication with parentheses: 6(8) or x(2)
        mul_pattern = r'(\d+\.?\d*|\w+)\s*\(([^()]+)\)'

        def replace_mul(match):
            left = match.group(1)
            right = match.group(2)

            # Evaluate left if it's a variable
            if left in self.variables:
                left_val = self.variables[left]
            else:
                try:
                    left_val = float(left)
                except:
                    left_val = left

            # Evaluate right
            right_val = self._evaluate_expression(right)

            return str(float(left_val) * float(right_val))

        # Keep replacing until no more matches
        prev_expr = None
        while prev_expr != expr:
            prev_expr = expr
            expr = re.sub(mul_pattern, replace_mul, expr)

        # Handle division: (a)/(b)
        div_pattern = r'\(([^()]+)\)/\(([^()]+)\)'

        def replace_div(match):
            left = self._evaluate_expression(match.group(1))
            right = self._evaluate_expression(match.group(2))
            if right == 0:
                raise ValueError("Division by zero")
            return str(left / right)

        prev_expr = None
        while prev_expr != expr:
            prev_expr = expr
            expr = re.sub(div_pattern, replace_div, expr)

        # Handle explicit multiplication with * operator
        if ' * ' in expr:
            mul_parts = expr.split(' * ')
            result = self._evaluate_expression(mul_parts[0])
            for part in mul_parts[1:]:
                result *= self._evaluate_expression(part)
            return self._approximate(result)

        # Handle addition and subtraction
        tokens = re.split(r'\s+([+-])\s+', expr)

        if len(tokens) > 1:
            result = self._evaluate_expression(tokens[0])
            i = 1
            while i < len(tokens):
                op = tokens[i]
                val = self._evaluate_expression(tokens[i + 1])
                if op == '+':
                    result += val
                else:
                    result -= val
                i += 2
            return self._approximate(result)

        # Single value
        expr = expr.strip()

        # Check if it's a variable
        if expr in self.variables:
            return self.variables[expr]

        # Check if it's a block variable
        if '.' in expr:
            parts = expr.split('.')
            if len(parts) == 2 and parts[0] in self.blocks:
                return self.blocks[parts[0]].get_variable(parts[1])

        # Try to parse as number
        try:
            return float(expr)
        except:
            pass

        # Handle negative numbers in parentheses: (-7)
        if expr.startswith('(') and expr.endswith(')'):
            inner = expr[1:-1].strip()
            if inner.startswith('-'):
                try:
                    return float(inner)
                except:
                    pass
            # Try evaluating inner expression
            try:
                return self._evaluate_expression(inner)
            except:
                pass

        raise ValueError(f"Cannot evaluate expression: {expr}")

    def _nth_root(self, x, n):
        """Calculate the n-th root of x."""
        if x < 0 and n % 2 == 0:
            raise ValueError("Cannot compute even root of negative number")
        if n == 0:
            raise ValueError("Cannot compute 0th root")
        return x**(1.0 / n)

    def _approximate(self, value):
        """Approximate to 2 decimal places if needed."""
        if isinstance(value, (int, float)):
            # Check if it has many decimal places
            str_val = str(value)
            if '.' in str_val and len(str_val.split('.')[1]) > 2:
                # Round to 2 decimal places
                return round(value, 2)
        return value

    def get_variable(self, var_name):
        """Get a variable value."""
        # Check for block variable access
        if '.' in var_name:
            parts = var_name.split('.')
            if len(parts) == 2:
                block_name, var_name = parts[0], parts[1]
                if block_name in self.blocks:
                    return self.blocks[block_name].get_variable(var_name)

        if var_name in self.variables:
            return self.variables[var_name]

        raise ValueError(f"Variable '{var_name}' not found")

    def define_variable(self, value):
        """Dynamically define a new variable."""
        self.dynamic_var_counter += 1
        var_name = f"X{self.dynamic_var_counter}" if self.dynamic_var_counter > 1 else "X"
        self.variables[var_name] = value
        return var_name


# Test the interpreter
def test_interpreter():
    """Test the ECS interpreter with sample calculations."""
    interpreter = Interpreter()

    # Test basic variable assignment
    interpreter.variables["x"] = 5
    interpreter.variables["y"] = 3

    # Test expression evaluation
    test_exprs = [
        ("2 + 3", 5),
        ("x + y", 8),
        ("(x) * (y)", 15),
        ("(10)/(2)", 5),
        ("(x)^(2)", 25),
        ("(2)√(16)", 4),
    ]

    print("Testing expression evaluation:")
    for expr, expected in test_exprs:
        try:
            result = interpreter._evaluate_expression(expr)
            print(
                f"  {expr} = {result} (expected: {expected}) - {'PASS' if abs(result - expected) < 0.001 else 'FAIL'}"
            )
        except Exception as e:
            print(f"  {expr} - ERROR: {e}")

    # Test block creation and solving
    print("\nTesting block solving:")

    # Create a Hooke's law block
    hooke_block = ECSPBlock("spring1", "hooke")
    hooke_block.set_variable("K", 100)
    hooke_block.set_variable("L_init", 0.5)
    hooke_block.set_variable("L_final", 0.7)
    hooke_block.mark_unknown("F")
    hooke_block.solve_unknowns()

    print(
        f"  Hooke's Law: Force = {hooke_block.get_variable('F')} N (expected: 20.0)"
    )

    # Test Ohm's Law
    ohm_block = ECSPBlock("circuit1", "ohm_law")
    ohm_block.set_variable("v", 12)
    ohm_block.set_variable("r", 4)
    ohm_block.mark_unknown("i")
    ohm_block.solve_unknowns()

    print(
        f"  Ohm's Law: Current = {ohm_block.get_variable('i')} A (expected: 3.0)"
    )

    print("\nAll tests completed.")


if __name__ == "__main__":
    test_interpreter()
