import os
import re
import math


class Function:
    """Represents a user-defined function with parameters and expression."""
    
    def __init__(self, name, params, defaults, expression):
        self.name = name
        self.params = params  # List of parameter names
        self.defaults = defaults  # Dict of param_name -> default_value
        self.expression = expression  # Expression body as string
    
    def evaluate(self, interpreter, **kwargs):
        """Evaluate the function with given arguments."""
        # Create local scope
        local_vars = {}
        
        # Apply default values first
        for param in self.params:
            if param in self.defaults:
                local_vars[param] = self.defaults[param]
        
        # Override with provided arguments
        for param, value in kwargs.items():
            if param not in self.params:
                raise ValueError(f"Function '{self.name}' does not have parameter '{param}'")
            local_vars[param] = value
        
        # Check all required parameters are provided
        for param in self.params:
            if param not in local_vars:
                raise ValueError(f"Missing required parameter '{param}' for function '{self.name}'")
        
        # Evaluate expression with local variables
        return interpreter._evaluate_expression_with_locals(self.expression, local_vars)


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
        raise ValueError(f"Variable '{var_name}' not found in block '{self.name}'")
    
    def _check_and_raise_unspecified(self):
        """Raise error if there are remaining unspecified variables."""
        if self.unknowns:
            sorted_unknowns = sorted(self.unknowns)
            raise ValueError(
                f"Unspecified variables in block '{self.name}': {', '.join(sorted_unknowns)}"
            )
    
    def solve_unknowns(self):
        """Solve for unknown variables based on block type."""
        if self.block_type == "hooke":
            # Hooke's Law: F = K * (L_final - L_init) and L = L_final - L_init
            K = self.variables.get("K")
            L_init = self.variables.get("L_init")
            L_final = self.variables.get("L_final")
            F = self.variables.get("F")
            
            # Solve for marked unknowns
            if "F" in self.unknowns:
                if K is not None and L_init is not None and L_final is not None:
                    self.variables["F"] = K * (L_final - L_init)
                    self.unknowns.discard("F")
            if "K" in self.unknowns:
                if F is not None and L_init is not None and L_final is not None and (L_final - L_init) != 0:
                    self.variables["K"] = F / (L_final - L_init)
                    self.unknowns.discard("K")
            if "L_final" in self.unknowns:
                if K is not None and F is not None and L_init is not None and K != 0:
                    self.variables["L_final"] = (F / K) + L_init
                    self.unknowns.discard("L_final")
            if "L_init" in self.unknowns:
                if K is not None and F is not None and L_final is not None and K != 0:
                    self.variables["L_init"] = L_final - (F / K)
                    self.unknowns.discard("L_init")
            if "L" in self.unknowns:
                if L_final is not None and L_init is not None:
                    self.variables["L"] = L_final - L_init
                    self.unknowns.discard("L")
            
            # Calculate all possible variables even if not marked as unknown
            if "F" not in self.variables and K is not None and L_init is not None and L_final is not None:
                self.variables["F"] = K * (L_final - L_init)
            if "K" not in self.variables and F is not None and L_init is not None and L_final is not None and (L_final - L_init) != 0:
                self.variables["K"] = F / (L_final - L_init)
            if "L_final" not in self.variables and K is not None and F is not None and L_init is not None and K != 0:
                self.variables["L_final"] = (F / K) + L_init
            if "L_init" not in self.variables and K is not None and F is not None and L_final is not None and K != 0:
                self.variables["L_init"] = L_final - (F / K)
            if "L" not in self.variables and L_final is not None and L_init is not None:
                self.variables["L"] = L_final - L_init
            
            self._check_and_raise_unspecified()
        
        elif self.block_type == "combined_gas_laws":
            # Combined Gas Law: (P1*V1)/T1 = (P2*V2)/T2
            p1 = self.variables.get("p1")
            v1 = self.variables.get("v1")
            t1 = self.variables.get("t1")
            p2 = self.variables.get("p2")
            v2 = self.variables.get("v2")
            t2 = self.variables.get("t2")
            
            # Solve for marked unknowns
            if "p1" in self.unknowns:
                if p2 is not None and v1 is not None and v2 is not None and t1 is not None and t2 is not None and t2 != 0 and v1 != 0:
                    self.variables["p1"] = (p2 * v2 * t1) / (t2 * v1)
                    self.unknowns.discard("p1")
            if "v1" in self.unknowns:
                if p1 is not None and p2 is not None and v2 is not None and t1 is not None and t2 is not None and t2 != 0 and p1 != 0:
                    self.variables["v1"] = (p2 * v2 * t1) / (t2 * p1)
                    self.unknowns.discard("v1")
            if "t1" in self.unknowns:
                if p1 is not None and v1 is not None and p2 is not None and v2 is not None and t2 is not None and p2 != 0 and v2 != 0:
                    self.variables["t1"] = (p1 * v1 * t2) / (p2 * v2)
                    self.unknowns.discard("t1")
            if "p2" in self.unknowns:
                if p1 is not None and v1 is not None and t1 is not None and v2 is not None and t2 is not None and t2 != 0 and v2 != 0:
                    left_side = (p1 * v1) / t1 if t1 != 0 else 0
                    self.variables["p2"] = (left_side * t2) / v2
                    self.unknowns.discard("p2")
            if "v2" in self.unknowns:
                if p1 is not None and v1 is not None and t1 is not None and p2 is not None and t2 is not None and t2 != 0 and p2 != 0:
                    left_side = (p1 * v1) / t1 if t1 != 0 else 0
                    self.variables["v2"] = (left_side * t2) / p2
                    self.unknowns.discard("v2")
            if "t2" in self.unknowns:
                if p1 is not None and v1 is not None and t1 is not None and p2 is not None and v2 is not None and p2 != 0 and v2 != 0:
                    left_side = (p1 * v1) / t1 if t1 != 0 else 0
                    self.variables["t2"] = (p2 * v2) / left_side if left_side != 0 else 0
                    self.unknowns.discard("t2")
            
            # Calculate all possible variables even if not marked as unknown
            # Calculate left side for convenience
            left_side = None
            if p1 is not None and v1 is not None and t1 is not None and t1 != 0:
                left_side = (p1 * v1) / t1
            
            if left_side is not None:
                if "p2" not in self.variables and v2 is not None and t2 is not None and t2 != 0 and v2 != 0:
                    self.variables["p2"] = (left_side * t2) / v2
                if "v2" not in self.variables and p2 is not None and t2 is not None and t2 != 0 and p2 != 0:
                    self.variables["v2"] = (left_side * t2) / p2
                if "t2" not in self.variables and p2 is not None and v2 is not None and p2 != 0 and v2 != 0:
                    self.variables["t2"] = (p2 * v2) / left_side if left_side != 0 else 0
            
            # Calculate right side for convenience
            right_side = None
            if p2 is not None and v2 is not None and t2 is not None and t2 != 0:
                right_side = (p2 * v2) / t2
            
            if right_side is not None:
                if "p1" not in self.variables and v1 is not None and t1 is not None and t1 != 0 and v1 != 0:
                    self.variables["p1"] = (right_side * t1) / v1
                if "v1" not in self.variables and p1 is not None and t1 is not None and t1 != 0 and p1 != 0:
                    self.variables["v1"] = (right_side * t1) / p1
                if "t1" not in self.variables and p1 is not None and v1 is not None and p1 != 0 and v1 != 0:
                    self.variables["t1"] = (p1 * v1) / right_side if right_side != 0 else 0
            
            self._check_and_raise_unspecified()
        
        elif self.block_type == "ohm_law":
            # Ohm's Law: V = I * R
            v = self.variables.get("v")
            i = self.variables.get("i")
            r = self.variables.get("r")
            
            # Solve for marked unknowns
            if "v" in self.unknowns:
                if i is not None and r is not None:
                    self.variables["v"] = i * r
                    self.unknowns.discard("v")
            if "i" in self.unknowns:
                if v is not None and r is not None and r != 0:
                    self.variables["i"] = v / r
                    self.unknowns.discard("i")
            if "r" in self.unknowns:
                if v is not None and i is not None and i != 0:
                    self.variables["r"] = v / i
                    self.unknowns.discard("r")
            
            # Calculate all possible variables even if not marked as unknown
            if "v" not in self.variables and i is not None and r is not None:
                self.variables["v"] = i * r
            if "i" not in self.variables and v is not None and r is not None and r != 0:
                self.variables["i"] = v / r
            if "r" not in self.variables and v is not None and i is not None and i != 0:
                self.variables["r"] = v / i
            
            self._check_and_raise_unspecified()
        
        elif self.block_type == "kinematics":
            # Kinematics equations: v = u + at, s = ut + 0.5at^2
            v = self.variables.get("v")
            u = self.variables.get("u")
            a = self.variables.get("a")
            t = self.variables.get("t")
            s = self.variables.get("s")
            
            # Solve for marked unknowns
            if "v" in self.unknowns:
                if u is not None and a is not None and t is not None:
                    self.variables["v"] = u + (a * t)
                    self.unknowns.discard("v")
            if "s" in self.unknowns:
                if u is not None and a is not None and t is not None:
                    s_calc = (u * t) + (0.5 * a * (t**2))
                    self.variables["s"] = s_calc
                    self.unknowns.discard("s")
            
            # Calculate all possible variables even if not marked as unknown
            if "v" not in self.variables and u is not None and a is not None and t is not None:
                self.variables["v"] = u + (a * t)
            if "s" not in self.variables and u is not None and a is not None and t is not None:
                s_calc = (u * t) + (0.5 * a * (t**2))
                self.variables["s"] = s_calc
                print(f"Calculated displacement s: {s_calc}")
            
            self._check_and_raise_unspecified()
        
        elif self.block_type == "energy":
            # Energy equations: KE = 0.5 * m * v^2, PE = m * g * h
            m = self.variables.get("m")
            v = self.variables.get("v")
            g = self.variables.get("g", 9.8)  # default gravity
            h = self.variables.get("h")
            
            # Solve for marked unknowns
            if "KE" in self.unknowns:
                if m is not None and v is not None:
                    self.variables["KE"] = 0.5 * m * (v**2)
                    self.unknowns.discard("KE")
            if "PE" in self.unknowns:
                if m is not None and h is not None:
                    self.variables["PE"] = m * g * h
                    self.unknowns.discard("PE")
            
            # Calculate all possible variables even if not marked as unknown
            if "KE" not in self.variables and m is not None and v is not None:
                self.variables["KE"] = 0.5 * m * (v**2)
            if "PE" not in self.variables and m is not None and h is not None:
                self.variables["PE"] = m * g * h
            
            self._check_and_raise_unspecified()
        
        elif self.block_type == "projectile_motion":
            # Projectile motion equations
            v0 = self.variables.get("v0")
            theta_deg = self.variables.get("theta", self.variables.get("θ"))
            theta = math.radians(theta_deg) if theta_deg is not None else None
            g = self.variables.get("g", 9.8)
            
            # Solve for marked unknowns
            if "R" in self.unknowns:
                if v0 is not None and theta is not None and g != 0:
                    self.variables["R"] = (v0**2 * math.sin(2 * theta)) / g
                    self.unknowns.discard("R")
            if "t" in self.unknowns:
                if v0 is not None and theta is not None and g != 0:
                    self.variables["t"] = (2 * v0 * math.sin(theta)) / g
                    self.unknowns.discard("t")
            if "H" in self.unknowns:
                if v0 is not None and theta is not None and g != 0:
                    self.variables["H"] = (v0**2 * (math.sin(theta)**2)) / (2 * g)
                    self.unknowns.discard("H")
            
            # Calculate all possible variables even if not marked as unknown
            if "R" not in self.variables and v0 is not None and theta is not None and g != 0:
                self.variables["R"] = (v0**2 * math.sin(2 * theta)) / g
            if "t" not in self.variables and v0 is not None and theta is not None and g != 0:
                self.variables["t"] = (2 * v0 * math.sin(theta)) / g
            if "H" not in self.variables and v0 is not None and theta is not None and g != 0:
                self.variables["H"] = (v0**2 * (math.sin(theta)**2)) / (2 * g)
            
            self._check_and_raise_unspecified()
        
        elif self.block_type == "circular_motion":
            # Circular motion: F = (m * v^2) / r
            m = self.variables.get("m")
            v = self.variables.get("v")
            r = self.variables.get("r")
            
            # Solve for marked unknowns
            if "F" in self.unknowns:
                if m is not None and v is not None and r is not None and r != 0:
                    self.variables["F"] = (m * (v**2)) / r
                    self.unknowns.discard("F")
            
            # Calculate all possible variables even if not marked as unknown
            if "F" not in self.variables and m is not None and v is not None and r is not None and r != 0:
                self.variables["F"] = (m * (v**2)) / r
            
            self._check_and_raise_unspecified()
        
        elif self.block_type == "gravitation":
            # Newton's Law of Universal Gravitation: F = G * (m1 * m2) / r^2
            f = self.variables.get("F")
            m1 = self.variables.get("m1")
            m2 = self.variables.get("m2")
            r = self.variables.get("r")
            g_const = self.variables.get("G", 6.67430e-11)
            
            # Solve for marked unknowns
            if "F" in self.unknowns:
                if m1 is not None and m2 is not None and r is not None and r != 0:
                    self.variables["F"] = g_const * (m1 * m2) / (r**2)
                    self.unknowns.discard("F")
            
            # Calculate all possible variables
            if "F" not in self.variables and m1 is not None and m2 is not None and r is not None and r != 0:
                self.variables["F"] = g_const * (m1 * m2) / (r**2)
            
            self._check_and_raise_unspecified()
            
        elif self.block_type == "work_power":
            # Work and power: W = F * d, P = W / t
            f = self.variables.get("F")
            d = self.variables.get("d")
            t = self.variables.get("t")
            
            # Solve for marked unknowns
            if "W" in self.unknowns:
                if f is not None and d is not None:
                    self.variables["W"] = f * d
                    self.unknowns.discard("W")
            if "P" in self.unknowns:
                w = self.variables.get("W")
                if w is None and f is not None and d is not None:
                    w = f * d
                if w is not None and t is not None and t != 0:
                    self.variables["P"] = w / t
                    self.unknowns.discard("P")
            
            # Calculate all possible variables even if not marked as unknown
            if "W" not in self.variables and f is not None and d is not None:
                self.variables["W"] = f * d
            if "P" not in self.variables:
                w = self.variables.get("W")
                if w is None and f is not None and d is not None:
                    w = f * d
                if w is not None and t is not None and t != 0:
                    self.variables["P"] = w / t
            
            self._check_and_raise_unspecified()


class Interpreter:
    """Main interpreter for ECS and ECSP files."""
    
    def __init__(self):
        self.variables = {}
        self.blocks = {}
        self.imported_files = set()
        self.functions = {}
    
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
            raise FileNotFoundError(f"Error: No .ecs or .ecsp file found for '{filename}'")
    
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
            # Check if it's a linear equation (no squared term)
            if not re.search(r'\(\(\w+\)\^2\)', line) and not re.search(r'\(\w+\)\^2', line):
                self._handle_linear(line, line_num)
            else:
                self._handle_quadratic(line, line_num)
            return
        
        # Handle function definition: f(x, y) = expression
        func_match = re.match(r'^(\w+)\s*\(([^)]*)\)\s*=\s*(.+)$', line)
        if func_match:
            self._handle_function_definition(func_match, line, line_num)
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
        
        # Check for block variable access (block.var)
        if '.' in var_name:
            raise ValueError(f"Error: Cannot assign to block variable directly at line {line_num}")
        
        # Check for indexed variable assignment (numeric constants not allowed as parameters)
        indexed_assign = re.match(r'^(\w+)\((\d+)\)$', var_name)
        if indexed_assign:
            raise ValueError(
                f"Error: Numeric constants not allowed as parameters at line {line_num}. "
                f"Use '{indexed_assign.group(1)} = ({expr})/({indexed_assign.group(2)})' instead."
            )
        
        # Evaluate the expression
        try:
            value = self._evaluate_expression(expr)
        except Exception as e:
            raise ValueError(f"Error evaluating expression at line {line_num}: {e}")
        
        # Check for inconsistent redefinition
        if var_name in self.variables:
            old_value = self.variables[var_name]
            # Allow if values are the same (or very close for floats)
            if isinstance(old_value, (int, float)) and isinstance(value, (int, float)):
                if abs(old_value - value) > 0.0001:
                    raise ValueError(f"Error: '{var_name}' is inconsistent at line {line_num}")
            elif old_value != value:
                raise ValueError(f"Error: '{var_name}' is inconsistent at line {line_num}")
        
        self.variables[var_name] = value
    
    def _handle_function_definition(self, match, line, line_num):
        """Handle function definition like f(x, y=1) = x + y."""
        func_name = match.group(1)
        params_str = match.group(2).strip()
        expression = match.group(3).strip()
        
        # Remove inline comments from expression
        if '//' in expression:
            expression = expression.split('//')[0].strip()
        
        # Parse parameters
        params = []
        defaults = {}
        
        if params_str:
            for param in params_str.split(','):
                param = param.strip()
                if '=' in param:
                    # Parameter with default value
                    parts = param.split('=', 1)
                    param_name = parts[0].strip()
                    default_expr = parts[1].strip()
                    
                    # Validate: parameter name must be a valid identifier, not a number
                    if not re.match(r'^[a-zA-Z_]\w*$', param_name):
                        raise ValueError(
                            f"Error: Invalid parameter name '{param_name}' at line {line_num}. "
                            f"Parameter names must be valid variable names, not numeric constants."
                        )
                    
                    # Evaluate default value
                    try:
                        default_value = self._evaluate_expression(default_expr)
                    except Exception as e:
                        raise ValueError(f"Error evaluating default value for '{param_name}' at line {line_num}: {e}")
                    
                    params.append(param_name)
                    defaults[param_name] = default_value
                else:
                    # Parameter without default
                    # Validate: parameter name must be a valid identifier, not a number
                    if not re.match(r'^[a-zA-Z_]\w*$', param):
                        raise ValueError(
                            f"Error: Invalid parameter '{param}' at line {line_num}. "
                            f"Use variable names as parameters, not numeric constants. "
                            f"Example: define 'x = {param}' first, then 'f(x) = ...'"
                        )
                    params.append(param)
        
        # Store the function
        self.functions[func_name] = Function(func_name, params, defaults, expression)
    
    def _handle_linear(self, line, line_num):
        """Handle linear equation of form 0 = b(x) + c."""
        # Extract the equation part after 0 =
        eq_part = line[3:].strip()
        
        # Find the variable name (look for pattern like (x) or (x1))
        var_match = re.search(r'\((\w+)\)', eq_part)
        if not var_match:
            raise ValueError(f"Error: Cannot parse linear equation at line {line_num}")
        
        var_name = var_match.group(1)
        
        # Parse coefficients
        temp_eq = eq_part.replace(f"({var_name})", "LINEAR_TERM")
        
        # Extract coefficient for linear term
        b_coef = 0
        c_coef = 0
        
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
        else:
            # No coefficient found, assume 1
            b_coef = 1
        
        # Find constant term (remaining numbers)
        remaining = temp_eq.replace(linear_match.group(0) if linear_match else '', '')
        remaining = remaining.replace('LINEAR_TERM', '')
        remaining = remaining.strip()
        
        # Extract constant
        if remaining:
            const_match = re.search(r'([+-]?\s*\d+\.?\d*)', remaining)
            if const_match:
                coef_str = const_match.group(1).replace(' ', '')
                try:
                    c_coef = float(coef_str)
                except ValueError:
                    # Evaluate expression if not a simple number
                    c_coef = self._evaluate_expression(coef_str)
        
        # Solve linear equation: bx + c = 0  =>  x = -c / b
        if b_coef == 0:
            if c_coef == 0:
                raise ValueError(f"Error: Infinite solutions for equation at line {line_num}")
            else:
                raise ValueError(f"Error: No solution for equation at line {line_num}")
        
        solution = -c_coef / b_coef
        
        # Check for inconsistent redefinition
        if var_name in self.variables:
            old_value = self.variables[var_name]
            if abs(old_value - solution) > 0.0001:
                raise ValueError(f"Error: '{var_name}' is inconsistent at line {line_num}")
        
        self.variables[var_name] = self._approximate(solution)
    
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
                raise ValueError(f"Error: Cannot parse quadratic equation at line {line_num}")
        
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
        remaining = temp_eq.replace(quad_match.group(0) if quad_match else '', '')
        remaining = remaining.replace(linear_match.group(0) if linear_match else '', '')
        remaining = remaining.replace('QUAD_TERM', '').replace('LINEAR_TERM', '')
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
        discriminant = b_coef**2 - 4*a_coef*c_coef
        
        if discriminant < 0:
            print(f"Warning: Negative discriminant for equation at line {line_num}: {line}")
            return
        
        # Use quadratic formula
        solution = 0
        if a_coef != 0:
            x1 = (-b_coef + math.sqrt(discriminant)) / (2*a_coef)
            x2 = (-b_coef - math.sqrt(discriminant)) / (2*a_coef)
            # Store the positive solution or first solution
            solution = x1 if x1 >= 0 else x2
        else:
            # Linear equation (fallback, though should be handled by _handle_linear)
            if b_coef != 0:
                solution = -c_coef / b_coef
            else:
                raise ValueError(f"Error: Invalid equation at line {line_num}")
        
        # Check for inconsistent redefinition
        if var_name in self.variables:
            old_value = self.variables[var_name]
            if abs(old_value - solution) > 0.0001:
                raise ValueError(f"Error: '{var_name}' is inconsistent at line {line_num}")
        
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
                        except (ValueError, TypeError, Exception) as e:
                            # Try to evaluate as number directly
                            try:
                                value = float(value_str)
                                block.set_variable(var_name, value)
                            except (ValueError, TypeError):
                                raise ValueError(f"Error parsing variable '{var_name}' in block '{block_name}': {e}")
            
            # Solve unknowns
            try:
                block.solve_unknowns()
            except ValueError as e:
                print(f"Error in block '{block_name}': {e}")
                raise
            
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
            replacement = str(float(mantissa) * (10 ** int(exp)))
            expr = expr.replace(f"({mantissa})e({exp})", replacement)
        
        # Handle pi function: pi(n) returns n * pi
        pi_pattern = r'pi\(([^)]+)\)'
        expr = re.sub(pi_pattern, lambda m: str(self._evaluate_expression(m.group(1)) * math.pi), expr)

        # Handle euler function: euler(n) returns n * e
        euler_pattern = r'euler\(([^)]+)\)'
        expr = re.sub(euler_pattern, lambda m: str(self._evaluate_expression(m.group(1)) * math.e), expr)

        # Handle abs function: abs(n) returns absolute value
        abs_pattern = r'abs\(([^)]+)\)'
        expr = re.sub(abs_pattern, lambda m: str(abs(self._evaluate_expression(m.group(1)))), expr)
        
        # Handle roots: (n)√(x) or (n)root(x)
        root_pattern = r'\((\d+)\)√\(([^)]+)\)'
        expr = re.sub(root_pattern, lambda m: str(self._nth_root(
            self._evaluate_expression(m.group(2)), 
            int(m.group(1))
        )), expr)
        
        root_pattern2 = r'\((\d+)\)root\(([^)]+)\)'
        expr = re.sub(root_pattern2, lambda m: str(self._nth_root(
            self._evaluate_expression(m.group(2)), 
            int(m.group(1))
        )), expr)
        
        # Handle exponentiation: (x)^(y)
        while True:
            exp_match = re.search(r'\(([^()]+)\)\^\(([^()]+)\)', expr)
            if not exp_match:
                break
            
            base = self._evaluate_expression(exp_match.group(1))
            exp = self._evaluate_expression(exp_match.group(2))
            result = base ** exp
            expr = expr[:exp_match.start()] + str(result) + expr[exp_match.end():]
        
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
                except (ValueError, TypeError):
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
        except (ValueError, TypeError):
            pass
        
        # Handle negative numbers in parentheses: (-7)
        if expr.startswith('(') and expr.endswith(')'):
            inner = expr[1:-1].strip()
            if inner.startswith('-'):
                try:
                    return float(inner)
                except (ValueError, TypeError):
                    pass
            # Try evaluating inner expression
            try:
                return self._evaluate_expression(inner)
            except (ValueError, TypeError, Exception):
                pass
        
        raise ValueError(f"Cannot evaluate expression: {expr}")
    
    def _nth_root(self, x, n):
        """Calculate the n-th root of x."""
        if x < 0 and n % 2 == 0:
            raise ValueError("Cannot compute even root of negative number")
        if n == 0:
            raise ValueError("Cannot compute 0th root")
        return x ** (1.0 / n)
    
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
    
    def evaluate_function(self, func_name, **kwargs):
        """Evaluate a function with given arguments."""
        if func_name not in self.functions:
            raise ValueError(f"Function '{func_name}' not found")
        
        func = self.functions[func_name]
        return func.evaluate(self, **kwargs)
    
    def _evaluate_expression_with_locals(self, expr, local_vars):
        """Evaluate expression with local variable scope."""
        # Store original variables
        original_vars = self.variables.copy()
        
        try:
            # Add local variables to scope (they take precedence)
            self.variables.update(local_vars)
            
            # Evaluate the expression
            result = self._evaluate_expression(expr)
            return result
        finally:
            # Restore original variables
            self.variables = original_vars
