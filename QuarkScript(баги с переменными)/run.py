import os
from sys import *

import colorama

from parser import *
from lexer import *
from exception import *
from interpreter import *
from colorama import Fore, init, Style
init()
if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "index.qs")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file.seek(0)
            content_to_compile = file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        exit(1)

    lexer_result = run(content_to_compile)
    if len(content_to_compile) > 0:
        print("CODE: ")
        print(f"    {content_to_compile}")
        print("LEXER TOKENS:")
        for l in lexer_result:
            print(f"    {l}")

        try:
            parser_result = parse(lexer_result)
            print("PARSER RESULT: ")
            for i in parser_result:
                print(f"    {i}")
            interpreter_result = interpret(parser_result)
            print("INTERPRETER RESULT:")
            for result in interpreter_result:
                if result is not None:
                    print(result)
        except InvalidCharacterError as inv:
            print(f"{Fore.RED}{colorama.Style.BRIGHT}{inv}{Fore.RESET}")
            exit(1)
        except Error as e:
            print(f"{Fore.RED}{colorama.Style.BRIGHT}{e}{Fore.RESET}")
            exit(1)
        except InterpreterErrors as ie:
            print(f"{Fore.RED}{colorama.Style.BRIGHT}{ie}{Fore.RESET}")
            exit(1)
        # except Exception as e:
        #     print(f"{Fore.RED}{Style.BRIGHT}Unexpected Error: {e}{Fore.RESET}")
        #     exit(1)

    else:
        print("EMPTY")
