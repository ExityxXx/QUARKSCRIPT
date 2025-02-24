
from exception import *

DIGITS = "0123456789"
OPERATORS = {
    "PLUS": "+",
    "MINUS": "-",
    "DIVIDE": "/",
    "MULTIPLY": "*",
    "LEFT_PAREN": "(",
    "RIGHT_PAREN": ")",
    "NEW_LINE": "\n",
    "SEMI_COLON": ";",
    "ASSIGN": "=",
    "COLON": ":",
    "DYNAMIC_COLON": ":=",
    "COMMA": ","
}

KEYWORDS = {
    "var": "VAR_KEYWORD",
    "int": "TYPE_INT",
    "float": "TYPE_FLOAT",
    "string": "TYPE_STRING",
    "sep": "SEP_KEYWORD"
}


class Token:
    def __init__(self, type_, line, column, value=None):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        if self.value:
            return f"(TYPE : {self.type} | VALUE : {self.value} | LINE : {self.line} | COLUMN : {self.column})"
        return f"(OPERATOR : {self.type} | LINE : {self.line} | COLUMN : {self.column})"

class Lexer:
    def __init__(self, text):
        self.text = text
        self.position = 0
        self.line = 1
        self.column = 1
        self.current_char = self.text[self.position] if len(self.text) > 0 else None

    def advance(self):
        self.position += 1
        if self.position < len(self.text):
            self.current_char = self.text[self.position]
        else:
            self.current_char = None



    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            if self.current_char == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.advance()

    def number(self):
        result = ''
        dot_count = 0
        while self.current_char is not None and self.current_char in DIGITS + ".":
            if self.current_char == ".":
                dot_count += 1
                if dot_count > 1:
                    break
            result += self.current_char
            self.advance()

        if result.startswith("."):
            result = "0" + result

        if dot_count == 0:
            return "INTEGER", int(result)
        else:
            return "FLOAT", float(result)

    def string(self):
        result = ""
        self.advance()
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        if self.current_char == '"' or self.current_char == "'":
            self.advance()
        else:
            raise StringError(f"'{self.current_char}'", self.line, self.column)

        return result


    def is_valid_expression_char(self, char):
        return char.isdigit() or char in "+-*/. \"'()"

    def read_expression(self):
        result = ""
        quote_type = None
        start_line = self.line
        start_column = self.column

        while self.current_char is not None and self.current_char != '\n':
            if quote_type:
                if self.current_char == quote_type:
                    result += self.current_char
                    self.advance()
                    return result, True
                else:
                    result += self.current_char
                    self.advance()
            elif self.is_valid_expression_char(self.current_char):
                if self.current_char == '"' or self.current_char == "'":
                    quote_type = self.current_char
                    result += self.current_char
                    self.advance()
                else:
                    result += self.current_char
                    self.advance()
            else:
                return result, False

        if quote_type:
            raise StringError(f"'{self.current_char}'", start_line, start_column)

        return result, True

    def tokenize(self):
        tokens = []
        is_var_context = False

        while self.current_char is not None:

            start_line = self.line
            start_column = self.column

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == OPERATORS["NEW_LINE"]:
                tokens.append(Token("NEW_LINE", start_line, start_column, "\n"))
                self.advance()
                continue

            if self.current_char == '.' and (
                    self.position + 1 >= len(self.text) or not self.text[self.position + 1].isdigit()):
                raise InvalidCharacterError(f"'{self.current_char}'", self.line, self.column)

            if self.current_char.isdigit() or self.current_char == '.':
                token_type, token_value = self.number()
                tokens.append(Token(token_type, start_line, start_column, token_value))
                continue

            if self.current_char == "/":
                if self.position + 1 < len(self.text) and self.text[self.position + 1] == '/':
                    while self.position < len(self.text) and self.text[self.position] != "\n":
                        self.advance()
                    continue

            if self.current_char == '"' or self.current_char == "'":
                quote_type = self.current_char
                string_value = ""
                self.advance()
                while self.current_char is not None and self.current_char != quote_type:
                    string_value += self.current_char
                    self.advance()

                if self.current_char is None:
                    raise SyntaxError(f"Unterminated String", start_line, start_column)

                self.advance()
                tokens.append(Token("STRING", start_line, start_column, string_value))
                continue
            if self.current_char == ":":
                if self.position + 1 < len(self.text) and self.text[self.position + 1] == "=":
                    tokens.append(Token("DYNAMIC_ASSIGN", start_line, start_column))
                    self.advance()
                    self.advance()
                    continue
                else:
                    tokens.append(Token("COLON", start_line, start_column))
                    self.advance()
                    continue

            if self.current_char == "=":
                tokens.append(Token("ASSIGN", start_line, start_column))
                self.advance()
                continue

            is_operator = False
            for token_type, operator_symbol in OPERATORS.items():
                if self.current_char == operator_symbol:
                    tokens.append(Token(token_type, start_line, start_column))
                    self.advance()
                    is_operator = True
                    break
            if is_operator:
                continue


            if self.current_char.isalpha():
                command = ""
                start_line = self.line
                start_column = self.column

                while self.position < len(self.text) and (self.text[self.position].isalnum() or self.text[
                    self.position] == '_'):
                    command += self.text[self.position]
                    self.advance()

                if command == "stdout":
                    tokens.append(Token("STDOUT", start_line, start_column))
                    self.skip_whitespace()
                    continue

                if command in KEYWORDS:
                    token = Token(KEYWORDS[command], start_line, start_column)
                    tokens.append(token)
                    self.skip_whitespace()
                    continue
                tokens.append(Token("VAR_IDENTIFIER", start_line, start_column, command))
                self.skip_whitespace()
                continue


            raise InvalidCharacterError(f"'{self.current_char}'", self.line, self.column)
        return tokens


def run(content):
    tokens = Lexer(content).tokenize()
    return tokens


