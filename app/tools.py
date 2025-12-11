"""
Tool Registry - Manages tools (Python functions) that nodes can call
"""
from typing import Dict, Callable, Any
import re
import ast


class ToolRegistry:
    """Registry for workflow tools"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
    
    def register(self, name: str, func: Callable):
        """Register a tool"""
        self.tools[name] = func
    
    def register_decorator(self, name: str = None):
        """Decorator to register a function as a tool"""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            self.register(tool_name, func)
            return func
        return decorator
    
    def get_tool(self, name: str) -> Callable:
        """Get a tool by name"""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        return self.tools[name]
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool exists"""
        return name in self.tools
    
    def list_tools(self) -> Dict[str, str]:
        """List all registered tools"""
        return {name: func.__name__ for name, func in self.tools.items()}


# Global tool registry instance
registry = ToolRegistry()


# Code Review Tools
@registry.register_decorator("extract_functions")
def extract_functions(state):
    """Extract functions from code"""
    code = state.get("code", "")
    if not code:
        state.error = "No code provided"
        return None
    
    try:
        tree = ast.parse(code)
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                    "args_count": len(node.args.args),
                    "has_docstring": ast.get_docstring(node) is not None
                }
                functions.append(func_info)
        
        state.update(functions=functions, functions_count=len(functions))
        return {"functions": functions, "count": len(functions)}
    except SyntaxError as e:
        state.error = f"Syntax error in code: {str(e)}"
        return None


@registry.register_decorator("check_complexity")
def check_complexity(state):
    """Check cyclomatic complexity of functions"""
    functions = state.get("functions", [])
    code = state.get("code", "")
    
    if not functions:
        state.error = "No functions found. Run extract_functions first."
        return None
    
    try:
        tree = ast.parse(code)
        complexity_scores = []
        
        for func_info in functions:
            func_name = func_info["name"]
            complexity = 1  # Base complexity
            
            # Find the function node
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    # Count decision points
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                            complexity += 1
                        elif isinstance(child, ast.BoolOp):
                            complexity += len(child.values) - 1
                    break
            
            func_info["complexity"] = complexity
            complexity_scores.append(complexity)
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        max_complexity = max(complexity_scores) if complexity_scores else 0
        
        state.update(
            functions=functions,
            avg_complexity=avg_complexity,
            max_complexity=max_complexity
        )
        
        return {
            "avg_complexity": avg_complexity,
            "max_complexity": max_complexity,
            "functions": functions
        }
    except Exception as e:
        state.error = f"Error checking complexity: {str(e)}"
        return None


@registry.register_decorator("detect_issues")
def detect_issues(state):
    """Detect basic code issues"""
    code = state.get("code", "")
    functions = state.get("functions", [])
    
    if not code:
        state.error = "No code provided"
        return None
    
    issues = []
    
    # Check for long functions
    for func in functions:
        lines = func.get("line_end", 0) - func.get("line_start", 0)
        if lines > 50:
            issues.append({
                "type": "long_function",
                "function": func["name"],
                "message": f"Function {func['name']} is too long ({lines} lines)"
            })
        
        # Check for functions with many arguments
        if func.get("args_count", 0) > 5:
            issues.append({
                "type": "too_many_args",
                "function": func["name"],
                "message": f"Function {func['name']} has too many arguments ({func['args_count']})"
            })
        
        # Check for missing docstrings
        if not func.get("has_docstring", False):
            issues.append({
                "type": "missing_docstring",
                "function": func["name"],
                "message": f"Function {func['name']} is missing a docstring"
            })
    
    # Check for common code smells
    if "TODO" in code or "FIXME" in code:
        issues.append({
            "type": "todo_found",
            "message": "Code contains TODO or FIXME comments"
        })
    
    if code.count("print(") > 0:
        issues.append({
            "type": "print_statement",
            "message": "Code contains print statements (consider using logging)"
        })
    
    state.update(issues=issues, issues_count=len(issues))
    return {"issues": issues, "count": len(issues)}


@registry.register_decorator("suggest_improvements")
def suggest_improvements(state):
    """Suggest improvements based on detected issues"""
    issues = state.get("issues", [])
    functions = state.get("functions", [])
    avg_complexity = state.get("avg_complexity", 0)
    
    suggestions = []
    
    # Suggest based on complexity
    if avg_complexity > 10:
        suggestions.append({
            "priority": "high",
            "message": "Average cyclomatic complexity is high. Consider breaking down complex functions."
        })
    
    # Suggest based on issues
    long_functions = [i for i in issues if i.get("type") == "long_function"]
    if long_functions:
        suggestions.append({
            "priority": "medium",
            "message": f"Consider splitting {len(long_functions)} long function(s) into smaller ones"
        })
    
    missing_docs = [i for i in issues if i.get("type") == "missing_docstring"]
    if missing_docs:
        suggestions.append({
            "priority": "low",
            "message": f"Add docstrings to {len(missing_docs)} function(s)"
        })
    
    # Calculate quality score
    issues_count = len(issues)
    complexity_penalty = max(0, (avg_complexity - 5) * 2)
    quality_score = max(0, 100 - (issues_count * 5) - complexity_penalty)
    
    state.update(
        suggestions=suggestions,
        quality_score=quality_score,
        suggestions_count=len(suggestions)
    )
    
    return {
        "suggestions": suggestions,
        "quality_score": quality_score,
        "count": len(suggestions)
    }

