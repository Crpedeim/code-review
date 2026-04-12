import ast
import random

class BugInjector(ast.NodeTransformer):
    """Walks a Python AST and randomly injects common bugs."""
    def __init__(self, probability: float = 0.5):
        super().__init__()
        self.probability = probability
        self.planted_issues = []

    def visit_Compare(self, node):
        self.generic_visit(node)
        if not node.ops: return node

        if random.random() < self.probability:
            op = node.ops[0]
            if isinstance(op, ast.Lt):
                node.ops[0] = ast.LtE()
                self.planted_issues.append({
                    "line": getattr(node, 'lineno', 1),
                    "issue": "off_by_one_error",
                    "severity": "high",
                    "description": "Changed strictly less than (<) to less than or equal (<=).",
                    "suggestion": "Change <= back to < to prevent out-of-bounds errors."
                })
            elif isinstance(op, ast.Gt):
                node.ops[0] = ast.GtE()
                self.planted_issues.append({
                    "line": getattr(node, 'lineno', 1),
                    "issue": "off_by_one_error",
                    "severity": "high",
                    "description": "Changed greater than (>) to greater than or equal (>=).",
                    "suggestion": "Change >= back to >."
                })
            elif isinstance(op, ast.Is):
                if isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
                    node.ops[0] = ast.Eq()
                    self.planted_issues.append({
                        "line": getattr(node, 'lineno', 1),
                        "issue": "none_comparison",
                        "severity": "medium",
                        "description": "Used '==' instead of 'is' for None comparison.",
                        "suggestion": "Use 'is None' instead of '== None' per PEP 8."
                    })
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if random.random() < self.probability:
            if isinstance(node.op, ast.Add):
                node.op = ast.Sub()
                self.planted_issues.append({
                    "line": getattr(node, 'lineno', 1),
                    "issue": "logic_error_operator",
                    "severity": "critical",
                    "description": "Addition (+) was changed to subtraction (-).",
                    "suggestion": "Verify the mathematical logic; revert to addition (+)."
                })
        return node

def generate_buggy_code(clean_code_str: str, probability: float = 0.5) -> tuple[str, list]:
    tree = ast.parse(clean_code_str)
    injector = BugInjector(probability=probability)
    mutated_tree = injector.visit(tree)
    ast.fix_missing_locations(mutated_tree)
    buggy_code_str = ast.unparse(mutated_tree)
    return buggy_code_str, injector.planted_issues