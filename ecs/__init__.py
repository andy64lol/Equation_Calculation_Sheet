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

def define_var(value):
    """Dynamically define a new variable with the given value."""
    return _interpreter.define_variable(value)

# Version info
__version__ = "1.0.0"
__all__ = ["add_sheet", "get", "define_var"]
