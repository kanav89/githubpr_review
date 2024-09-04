import radon.complexity as cc
from radon.visitors import ComplexityVisitor

def analyze_complexity(code):
    results = []
    v = ComplexityVisitor.from_code(code)
    for func in v.functions:
        if func.complexity > 10:  # You can adjust this threshold
            results.append(f"Function '{func.name}' has a complexity of {func.complexity}. Consider refactoring.")
    
    return "\n".join(results) if results else "No overly complex functions found."
