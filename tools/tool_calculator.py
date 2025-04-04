"""
Calculator tool for safely evaluating mathematical expressions.
Supports basic arithmetic operations and common math functions.
"""
import math
import ast
import operator
from typing import Union, Any
from mcp_instance import mcp

class CalculatorError(Exception):
    """Exception raised for calculator-specific errors."""
    pass

@mcp.tool()
async def calculator(expression: str) -> dict:
    """
    Evaluate a mathematical expression
    
    Args:
        expression: The mathematical expression to evaluate
        
    Returns:
        The result of the calculation
    """
    # Define allowed operators
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.Mod: operator.mod
    }
    
    # Define a safe evaluator
    def eval_expr(node: ast.AST) -> Union[float, int]:
        # Use ast.Constant for Python 3.8+ but handle numeric values in a version-agnostic way
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        # Handle old-style numeric nodes without direct reference to ast.Num
        elif hasattr(node, 'n') and not isinstance(node, (ast.Constant, ast.BinOp, ast.UnaryOp, ast.Call)):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](eval_expr(node.left), eval_expr(node.right))
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](eval_expr(node.operand))
        elif isinstance(node, ast.Call):
            if node.func.id == 'sqrt':
                return math.sqrt(eval_expr(node.args[0]))
            elif node.func.id == 'sin':
                return math.sin(eval_expr(node.args[0]))
            elif node.func.id == 'cos':
                return math.cos(eval_expr(node.args[0]))
            elif node.func.id == 'tan':
                return math.tan(eval_expr(node.args[0]))
            raise ValueError(f"Function {node.func.id} not supported")
        else:
            raise TypeError(f"Unsupported operation: {node}")
    
    try:
        # Clean and prepare the expression
        expression = expression.replace('^', '**')
        
        # Special handling for sqrt, sin, cos, tan
        for func in ['sqrt', 'sin', 'cos', 'tan']:
            if func in expression:
                expression = expression.replace(f"{func}(", f"{func}(")
        
        # Parse the expression
        node = ast.parse(expression, mode='eval').body
        
        # Evaluate and return
        result = eval_expr(node)
        return {"result": result, "expression": expression}
    except (ValueError, TypeError, SyntaxError, ZeroDivisionError, OverflowError) as e:
        return {"error": str(e), "expression": expression}
    except Exception as e:
        # Still catch unknown errors to prevent crashes, but log them differently
        return {"error": f"Unexpected error: {str(e)}", "expression": expression}
