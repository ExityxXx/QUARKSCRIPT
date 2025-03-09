from parser import *

class Interpreter:
    def __init__(self, ast):
        self.ast = ast
        self.variables = {}
        self.variable_types = {}

    def visit(self, node):
        if isinstance(node, IntNumberNode):
            return self.visit_IntNumberNode(node)
        elif isinstance(node, FloatNumberNode):
            return self.visit_FloatNumberNode(node)
        elif isinstance(node, StringNode):
            return self.visit_StringNode(node)
        elif isinstance(node, BinOpNode):
            return self.visit_BinOpNode(node)
        elif isinstance(node, VariableDeclarationNode):
            return self.visit_VariableDeclarationNode(node)
        elif isinstance(node, VariableNode):
            return self.visit_VariableNode(node)
        elif isinstance(node, ConcatenationNode):
            return self.visit_ConcatenationNode(node)
        elif isinstance(node, StdoutNode):
            return self.visit_StdoutNode(node)
        elif isinstance(node, UnaryOpNode):
            return self.visit_UnaryOpNode(node)
        elif isinstance(node, AssignmentNode):
            return self.visit_AssignmentNode(node)
        elif isinstance(node, BooleanNode):
            return self.visit_BooleanNode(node)
        else:
            raise Exception(f"No visit_{type(node).__name__} method defined.")
    def infer_type_from_value(self, value):
        if isinstance(value, int):
            return "TYPE_INT"
        elif isinstance(value, float):
            return "TYPE_FLOAT"
        elif isinstance(value, str):
            return "TYPE_STRING"
        elif isinstance(value, bool):
            return "TYPE_BOOL"
        else:
            return None
    def visit_IntNumberNode(self, node):
        return node.value

    def visit_FloatNumberNode(self, node):
        return node.value

    def visit_StringNode(self, node):
        return node.value

    def visit_BinOpNode(self, node):
        left_value = self.visit(node.left)
        right_value = self.visit(node.right)
        left_type = self.variable_types.get(node.left.name) if isinstance(node.left, VariableNode) else None
        right_type = self.variable_types.get(node.right.name) if isinstance(node.right, VariableNode) else None

        if node.op == "PLUS":
            if left_type == "TYPE_BOOL" and right_type == "TYPE_BOOL":
                return left_value or right_value
            else:
                return left_value + right_value
        elif node.op == "MINUS":
            return left_value - right_value
        elif node.op == "DIVIDE":
            if right_value != 0:
                return left_value / right_value
            raise ZeroDivisionError("Division by zero")
        elif node.op == "MULTIPLY":
            return left_value * right_value
        else:
            raise Exception(f"Unknown binary operator: {node.op}")

    def visit_VariableDeclarationNode(self, node):
        var_name = node.name
        var_value = self.visit(node.value)

        if node.type is None:
            var_type = self.infer_type_from_value(var_value)
            if var_type is None:
                raise Exception(f"InterpreterVarDecErr: Cannot infer type for variable '{var_name}'")
        else:
            var_type = node.type
        if var_type == "TYPE_INT" and not isinstance(var_value, int):
            raise TypeError(f"Expected TYPE_INT, got {type(var_value)}")
        elif var_type == "TYPE_FLOAT" and not isinstance(var_value, (int, float)):
            raise TypeError(f"Expected TYPE_FLOAT, got {type(var_value)}")
        elif var_type == "TYPE_STRING" and not isinstance(var_value, str):
            raise TypeError(f"Expected TYPE_STRING, got {type(var_value)}")
        elif var_type == "TYPE_BOOL" and not isinstance(var_value, bool):
            raise TypeError(f"Expected TYPE_BOOL got {type(var_value)}")

        if var_name not in self.variables:
            self.variables[var_name] = var_value
            self.variable_types[var_name] = var_type
            return var_value
        else:
            raise InterpreterErrors("Invalid Syntax", f"Variable '{var_name}' already exists")
    def visit_VariableNode(self, node):
        var_name = node.name
        if var_name in self.variables:
            return self.variables[var_name]
        else:
            raise Exception(f"Variable {var_name} is not defined")
    def visit_ConcatenationNode(self, node):
        left_value = self.visit(node.left)
        right_value = self.visit(node.right)
        return str(left_value) + str(right_value)

    def visit_StdoutNode(self, node):
        if node.expression is None: return None
        if isinstance(node.expression, MultiValueNode):
            output = self.visit_MultiValueNode(node.expression)
        elif isinstance(node.expression, FloatNumberNode):
            output = float(self.visit(node.expression))
        else:
            output = str(self.visit(node.expression))

        return output
    def visit_UnaryOpNode(self, node):
        value = self.visit(node.node)

        if node.op == "MINUS":
            return -value
        else:
            raise Exception(f"Unknown unary operator: {node.op}")

    def visit_MultiValueNode(self, node):
        values = (str(self.visit(value_node)) for value_node in node.values)
        return node.separator.join(values)
    def visit_AssignmentNode(self, node):
        var_name = node.variable_name
        var_value = self.visit(node.expression)

        if var_name not in self.variables:
            raise Exception(f"Name '{var_name}' is not defined")

        declared_type = self.variable_types[var_name]
        inferred_type = self.infer_type_from_value(var_value)

        if declared_type == "TYPE_INT" and not isinstance(var_value, int):
            raise TypeError(f"Expected TYPE_INT, got {type(var_value)}")
        elif declared_type == "TYPE_FLOAT" and not isinstance(var_value, (int, float)):
            raise TypeError(f"Expected TYPE_FLOAT, got {type(var_value)}")
        elif declared_type == "TYPE_STRING" and not isinstance(var_value, str):
            raise TypeError(f"Expected TYPE_STRING, got {type(var_value)}")
        elif declared_type == "TYPE_BOOL" and not isinstance(var_value, bool):
            raise TypeError(f"Excepted TYPE_BOOL, got {type(var_value)}")
        elif declared_type is None and inferred_type is None:
            raise Exception("Cannot infer type for assignment")
        elif declared_type is None and declared_type != inferred_type:
            raise Exception(f"Type mismatch: cannot assign {inferred_type} to {declared_type}")

        self.variables[var_name] = var_value
        return var_value
    def visit_BooleanNode(self, node):
        return node.value

def interpret(ast):
    interpreter = Interpreter(ast)
    results = []
    for node in ast:
        result = interpreter.visit(node)
        if isinstance(node, StdoutNode):
            results.append(result)
    return results

