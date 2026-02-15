"""
ECS - Equation Calculation Sheet
A DSL for mathematical calculations with support for equations, blocks, and imports.
"""

from .interpreter import Interpreter

# Global interpreter instance
_interpreter = Interpreter()

def add_sheet(filename):
    """Load an .ecs or .ecsp file."""
    _interpreter.load_sheet(filename)

def get(var_name):
    """Get a variable value by name. Supports 'block.variable' syntax for ECSP blocks."""
    return _interpreter.get_variable(var_name)

def evaluate(func_name, **kwargs):
    """Evaluate a function defined in an .ecs file with given arguments.
    
    Example:
        ecs.evaluate("f", x=4, y=9)  # evaluates f(x, y) = 2(y + x)
    """
    return _interpreter.evaluate_function(func_name, **kwargs)

# Version info
__version__ = "1.0.0"
__all__ = ["add_sheet", "get", "evaluate"]
