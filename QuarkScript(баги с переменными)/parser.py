from colorama import Fore, init
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
        current_token_line = self.current_token.line
        current_token_column = self.current_token.column
        if self.current_token is None:
            return None

        if self.current_token.type == 'STDOUT':
            statement = self.parse_stdout()
        elif self.current_token.type == "VAR_KEYWORD":
            statement = self.parse_var_declaration()

        elif self.current_token.type == "VAR_IDENTIFIER":
            variable_name = self.current_token.value
            self.advance()
            if self.current_token is not None and self.current_token.type == "ASSIGN":
                self.advance()
                expression = self.parse_expression()
                if self.current_token is not None and self.current_token.type == "SEMI_COLON":
                    self.advance()
                return AssignmentNode(variable_name, expression)
            else:
                return VariableNode(variable_name)
        else:
            statement = self.parse_expression()



        if self.current_token is None or self.current_token.type != "SEMI_COLON":
            raise Error("Statement Syntax Error",
                        "Excepted ';' at the end of statement",
                        current_token_line, current_token_column)
        self.advance()
        return statement

    def parse_var_declaration(self):
        current_token_line = self.current_token.line # запоминаем данные токена пока токен не None
        current_token_column = self.current_token.column
        self.advance() # пропускаем ключевое слово "var" и идем к идентификатору

        if self.current_token is None or self.current_token.type != "VAR_IDENTIFIER": # если после слова "var" не идентификатор, выбрасываем ошибку
                raise Error(
                    "Invalid Syntax",
                    "Excepted variable name after keyword var.",
                    current_token_line, current_token_column)

        var_name = self.current_token.value # записываем идентификатор переменной
        self.advance() # после записи продвигаемся на следующий токен, ожидается что этот токен будет: или:=
        var_type = None


        if self.current_token.type == "COLON":
            self.advance()

            if self.current_token is None or self.current_token.type not in ("TYPE_INT", "TYPE_FLOAT", "TYPE_STRING", "TYPE_BOOL"):
                raise Error("Invalid Variable Declaration",
                            "Excepted type after ':'",
                            current_token_line, current_token_column
                        )

            var_type = self.current_token.type
            self.advance()

            if self.current_token.type != "ASSIGN":
                raise Error("Invalid Syntax",
                            "Excepted '=' after type declaration",
                            current_token_line, current_token_column
                        )
            self.advance()

        elif self.current_token.type == "DYNAMIC_ASSIGN":
            self.advance()
        elif self.current_token.type == "ASSIGN":
            raise Error("Invalid Syntax",
                        "You can't use '=' to declare a variable. Use ':=' or ': type ='",
                        current_token_line, current_token_column)
        else:
            raise Error("Invalid Syntax",
                        "Expected ':='  after variable id",
                        current_token_line, current_token_column)

        value = self.parse_expression()

        if self.current_token is not None and self.current_token.type != "SEMI_COLON":
            raise Error("Invalid Syntax",
                        "Expected ';' after variable declaration",
                        current_token_line, current_token_column)

        return VariableDeclarationNode(var_name, var_type, value)

    def parse_stdout(self):
        current_token_line = self.current_token.line
        current_token_column = self.current_token.column
        self.advance()
        if self.current_token.type == "SEMI_COLON":
            return StdoutNode(None)

        elif self.current_token.type == "VAR_KEYWORD":
            raise Error("SyntaxError",
                        "an attempt to declare a variable inside 'stdout'",
                        current_token_line,
                        current_token_column)
        first_value = self.parse_expression()

        if self.current_token is not None and self.current_token.type == "COMMA":
            values = [first_value]
            while self.current_token is not None and self.current_token.type == "COMMA":
                self.advance()
                values.append(self.parse_expression())

            return StdoutNode(MultiValueNode(values))
        else:
            return StdoutNode(first_value)

    def parse_expression(self):
        left = self.parse_term()

        while self.current_token is not None and self.current_token.type in ("PLUS", "MINUS"):
            op = self.current_token
            self.advance()
            right = self.parse_term()
            # левое | правое
            if (isinstance(left, StringNode) or isinstance(right, StringNode) or
                    isinstance(left, ConcatenationNode) or isinstance(right, ConcatenationNode)):
                left = ConcatenationNode(left, right)
            else:
                left = BinOpNode(op.type, left, right)

        return left

    def parse_term(self):
        left = self.parse_factor()

        while self.current_token is not None and self.current_token.type in ('MULTIPLY', 'DIVIDE'):
            op = self.current_token
            self.advance()


            if self.current_token is None or (self.current_token.type not in (
            "INTEGER", "FLOAT", "LEFT_PAREN", "STRING", "VAR_IDENTIFIER", "FALSE", "TRUE") and self.current_token.type != "MINUS"):
                line = op.line
                column = op.column
                raise Error("SyntaxError", "Expected factor after operator", line, column)

            if self.current_token is not None and self.current_token.type == "MINUS":
                unary_op = self.current_token.type
                self.advance()
                right = UnaryOpNode(unary_op, self.parse_factor())
            else:
                right = self.parse_factor()

            if isinstance(left, StringNode) or isinstance(right, StringNode):
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
        elif self.current_token.type == "TRUE":
            node = BooleanNode(True)
            self.advance()
            return node
        elif self.current_token.type == "FALSE":
            node = BooleanNode(False)
            self.advance()
            return node
        elif self.current_token.type == "STRING":
            node = StringNode(self.current_token.value)
            self.advance()
            return node
        elif self.current_token.type == "VAR_IDENTIFIER":
            node = VariableNode(self.current_token.value)
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
            raise Error("Parsing error", f"Unexpected token: {self.current_token.type}", line, column)



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

    def __repr__(self):
        return f"ConcatenationNode(left={self.left}, right={self.right})"

class VariableNode(ASTNode):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"VariableNode(name={Fore.CYAN}{self.name}{Fore.RESET})"

class VariableDeclarationNode(ASTNode):
    def __init__(self, variable_name, variable_type, variable_value):
        self.name = variable_name
        self.type = variable_type
        self.value = variable_value
    def __repr__(self):
        return f"VariableDeclarationNode(variable_name={Fore.RED}\"{self.name}\"{Fore.RESET}, type={Fore.RED}{self.type}{Fore.RESET}, value={self.value})"
class MultiValueNode(ASTNode):
    def __init__(self, values, separator=" "):
        self.values = values
        self.separator = separator
    def __repr__(self):
        return f"MultiValueNode(values={self.values}, sep={self.separator})"
class AssignmentNode(ASTNode):
    def __init__(self, variable_name, expression):
        self.variable_name = variable_name
        self.expression = expression
    def __repr__(self):
        return f"AssignmentNode(variable_name={self.variable_name}, expression={self.expression})"
class BooleanNode(ASTNode):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"BooleanNode(value={Fore.YELLOW}{self.value}{Fore.RESET})"

def parse(tokens):
    parser = Parser(tokens)
    ast = parser.parse()
    return ast
