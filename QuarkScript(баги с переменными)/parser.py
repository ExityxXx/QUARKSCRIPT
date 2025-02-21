from colorama import Fore, Back, Style, init
from exception import *
init()

class Parser:
    def __init__(self, tokens):
        self.tokens = iter(tokens)
        self.current_token = None
        self.advance()

    def advance(self):
        try:
            self.current_token = next(self.tokens)
        except StopIteration:
            self.current_token = None

    def parse(self):
        statements = []
        while self.current_token is not None:
            if self.current_token.type == "NEW_LINE":
                self.advance()
                continue
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self):
        if self.current_token is None:
            return None



        if self.current_token.type == 'STDOUT':
            statement = self.parse_stdout()
        elif self.current_token.type == "VAR_KEYWORD":
            statement = self.parse_var_declaration()
        else:
            statement = self.parse_expression()

        if self.current_token is None or self.current_token.type != "SEMI_COLON":
            raise SyntaxError("SyntaxError, Expected semicolon at the end of statement")

        self.advance()

        return statement
    def parse_var_declaration(self):
        self.advance()

        if self.current_token is None or self.current_token.type != "IDENTIFIER":
            raise Error("SyntaxError", "Excepted variable name", self.current_token.line, self.current_token.column)

        var_name = self.current_token.value
        self.advance()

        if self.current_token is None:
            raise Error("SyntaxError", "Excepted ':' or ':='", self.current_token.line, self.current_token.column)

        var_type = None
        if self.current_token.type == "COLON":
            self.advance()

            if self.current_token is None or self.current_token.type not in ("TYPE_INT", "TYPE_FLOAT", "TYPE_STRING"):
                raise Error("SyntaxError", "Excepted type after ':'", self.current_token.line, self.current_token.column)

            var_type = self.current_token.type
            self.advance()
        if self.current_token is None or self.current_token.type not in ("ASSIGN", "DYNAMIC_ASSIGN"):
            raise Error("SyntaxError", "Excepted '=' or ':='", self.current_token.line, self.current_token.column)

        self.advance()
        value = self.parse_expression()

        return VariableDeclarationNode(var_name, var_type, value)
    def parse_stdout(self):
        self.advance()
        if self.current_token.type == "SEMI_COLON":
            return ""
            # raise Error("SyntaxError", "Expected expression after stdout", self.current_token.line,
            #             self.current_token.column if self.current_token else 0)

        expression = self.parse_expression()
        return StdoutNode(expression)

    def parse_number(self):
        node = IntNumberNode(self.current_token.value)
        self.advance()
        return node

    def parse_expression(self):
        left = self.parse_term()

        while self.current_token is not None and self.current_token.type in ("PLUS", "MINUS"):
            op = self.current_token
            self.advance()
            right = self.parse_term()

            if isinstance(left, StringNode) and isinstance(right, StringNode) and op.type == "PLUS":
                left = ConcatenationNode(left, right)
            elif isinstance(left, ConcatenationNode) and isinstance(right, StringNode) and op.type == "PLUS":
                left = ConcatenationNode(left, right)
            else:
                if (isinstance(left, StringNode) and not isinstance(right, StringNode)) or \
                        (not isinstance(left, StringNode) and isinstance(right, StringNode)):
                    line = op.line
                    column = op.column
                    raise Error("TypeError", f"Concatenation of two types is not possible: {left.__class__.__name__}[{left.value}] {op.value} {right.__class__.__name__}[\"{right.value}\"]", line, column)
                left = BinOpNode(op.type, left, right)

        return left

    def parse_term(self):
        left = self.parse_factor()

        while self.current_token is not None and self.current_token.type in ('MULTIPLY', 'DIVIDE'):
            op = self.current_token
            self.advance()
            right = self.parse_factor()

            if (isinstance(left, StringNode) or isinstance(right, StringNode)):
                line = op.line
                column = op.column
                raise Error("TypeError",
                            f"Multiplication or division of a string is not allowed: {left.__class__.__name__}[{left.value}] {op.value} {right.__class__.__name__}[\"{right.value}\"]",
                            line, column)


            left = BinOpNode(op.type, left, right)

        return left

    def parse_factor(self):
        if self.current_token is None:
            line = self.current_token.line if self.current_token else 1
            column = self.current_token.column if self.current_token else 1
            raise Error("Parsing error", "Expected factor, but got end of input", line, column)

        if self.current_token.type == "MINUS":
            op = self.current_token.type
            self.advance()
            node = self.parse_factor()
            return UnaryOpNode(op, node)
        if self.current_token.type == "INTEGER":
            node = IntNumberNode(self.current_token.value)
            self.advance()
            return node
        elif self.current_token.type == "FLOAT":
            node = FloatNumberNode(self.current_token.value)
            self.advance()
            return node

        elif self.current_token.type == "STRING":
            node = StringNode(self.current_token.value)
            self.advance()
            return node

        elif self.current_token.type == "LEFT_PAREN":
            left_paren_line = self.current_token.line
            left_paren_column = self.current_token.column
            self.advance()
            node = self.parse_expression()
            if self.current_token is None or self.current_token.type != "RIGHT_PAREN":

                raise Error("Parsing error", "Expected ')'", left_paren_line, left_paren_column)
            self.advance()
            return node
        elif self.current_token.type == "RIGHT_PAREN":
            line = self.current_token.line
            column = self.current_token.column
            raise Error("Parsing error", "Expected '('", line, column)

        elif self.current_token.type == 'NEW_LINE':
            self.advance()
            return self.parse_statement()
        elif self.current_token.type == "SEMI_COLON":
            self.advance()
        elif self.current_token.type == "VAR_KEYWORD":
            self.advance()
        else:
            line = self.current_token.line if self.current_token else 1
            column = self.current_token.column if self.current_token else 1
            raise Error("Parsing error", f"Unexpected token: {self.current_token}", line, column)


class ASTNode:
    pass

class StdoutNode(ASTNode):
    def __init__(self, expression):
        self.expression = expression
    def __repr__(self):
        return f"StdoutNode(expression={self.expression})"

class StringNode(ASTNode):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"StringNode(value={Fore.YELLOW}\"{self.value}\"{Fore.RESET})"

class IntNumberNode(ASTNode):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"IntNumberNode(value={Fore.BLUE}{self.value}{Fore.RESET})"

class FloatNumberNode(ASTNode):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"FloatNumberNode(value={Fore.BLUE}{self.value}{Fore.RESET})"
class BinOpNode(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
    def __repr__(self):
        return f"BinOpNode(op='{Fore.MAGENTA}{self.op}{Fore.RESET}', left={self.left}, right={self.right})"
class UnaryOpNode(ASTNode):
    def __init__(self, op, node):
        self.op = op
        self.node = node
    def __repr__(self):
        return f"UnaryOpNode(op='{Fore.MAGENTA}{self.op}{Fore.RESET}', node={self.node})"

class ConcatenationNode(ASTNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

        def get_value(node):
            if isinstance(node, StringNode):
                return node.value
            elif isinstance(node, ConcatenationNode):
                return node.result
            else:
                return str(node)

        self.result = get_value(self.left) + get_value(self.right)
    def __repr__(self):
        return f"ConcatenationNode(left={self.left}, right={self.right}, result={Fore.YELLOW}\"{self.result}\"{Fore.RESET})"
class VariableDeclarationNode(ASTNode):
    def __init__(self, variable_name, variable_type, variable_value):
        self.name = variable_name
        self.type = variable_type
        self.value = variable_value
    def __repr__(self):
        return f"VariableDeclarationNode(name={self.name}, type={self.type}, value={self.value})"
def parse(tokens):
    parser = Parser(tokens)
    ast = parser.parse()
    return ast
