from docutils.frontend import validate_url_trailing_slash

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

        else:
            raise Exception(f"No visit_{type(node).__name__} method defined.")
    def infer_type_from_value(self, value):
        if isinstance(value, int):
            return "TYPE_INT"
        elif isinstance(value, float):
            return "TYPE_FLOAT"
        elif isinstance(value, str):
            return "TYPE_STRING"
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

        if node.op == "PLUS":
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

        self.variables[var_name] = var_value
        self.variable_types[var_name] = var_type
        return var_value
    def visit_VariableNode(self, node):
        var_name = node.name
        if var_name in self.variables:
            return self.variables[var_name]
        else:
            raise Exception(f"Variable {var_name} is not defined")
    def visit_ConcatenationNode(self, node):
        left_value = node.get_value(node.left, self)
        right_value = node.get_value(node.right, self)

        return str(left_value) + str(right_value)

    def visit_StdoutNode(self, node):
        if node.expression is None: return None
        if isinstance(node.expression, MultiValueNode):
            output = self.visit_MultiValueNode(node.expression)
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
        # result = []
        # for value_node in node.values:
        #     value = self.visit(value_node)
        #     result.append(str(value))
        # return " ".join(result)
        values = (str(self.visit(value_node)) for value_node in node.values)
        return node.separator.join(values)
def interpret(ast):
    interpreter = Interpreter(ast)
    results = []
    for node in ast:
        result = interpreter.visit(node)
        if isinstance(node, StdoutNode):
            results.append(result)
    return results

