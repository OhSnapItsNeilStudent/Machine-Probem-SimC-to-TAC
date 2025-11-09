import json
import sys
from typing import List, Dict

'''
===========================================================
SimC Lexical Analyzer (Scanner)
===========================================================

This scanner takes a SimC source file (.smc) and produces
a list of tokens as JSON-formatted output for the parser.

The scanner implements a 30-state DFA to recognize:
- Keywords: if, else, while, return, print, iread
- Operators: +, -, *, /, %, ==, !=, <, <=, >, >=, =
- Delimiters: ( ) { } ; ,
- Identifiers and integer literals
- Single-line comments (//) which are ignored

The token stream serves as input for the Recursive Descent
Parser which builds the Abstract Syntax Tree (AST).

'''

class Token:
    def __init__(self, token_type, value, line_num):
        self.type = token_type
        self.value = value
        self.line_num = line_num
    
    def to_dict(self):
        return {"type": self.type, "value": self.value}

class State:
    def __init__(self):
        self.transitionDict = {}
        self.endStateBool = False
        self.startStateBool = False
        self.errorStateBool = False
        self.pushBackStateBool = False
        self.ignoreStateBool = False
        self.checkpointStateBool = False
        self.tokenType = None
        self.errorMsg = None

    def setDict(self, inputDict):
        self.transitionDict = inputDict

    def setEndState(self, endState, tokenType):
        self.endStateBool = endState
        self.tokenType = tokenType

    def setIgnoreState(self, ignoreState):
        self.ignoreStateBool = ignoreState

    def setCheckpointState(self, checkpointState):
        self.checkpointStateBool = checkpointState

    def setPushBackState(self, pushBackState, tokenType):
        self.pushBackStateBool = pushBackState
        self.tokenType = tokenType

    def setStartState(self, startState):
        self.startStateBool = startState

    def setErrorState(self, errorState, errorMsg):
        self.errorStateBool = errorState
        self.errorMsg = errorMsg

    def isEndState(self):
        return self.endStateBool
    
    def isIgnoreState(self):
        return self.ignoreStateBool
    
    def isPushBackState(self):
        return self.pushBackStateBool
    
    def isErrorState(self):
        return self.errorStateBool

    def isStartState(self):
        return self.startStateBool

    def isCheckpointState(self):
        return self.checkpointStateBool

    def getNewState(self, key):
        # Handle EOF
        if key == "":
            if "" in self.transitionDict:
                return self.transitionDict[""]
            return self.transitionDict.get("other", 0)
        
        # Check for digit
        if key.isdigit():
            return self.transitionDict.get("digit", self.transitionDict.get("other", 0))
        
        # Check for letter
        if key.isalpha():
            return self.transitionDict.get("letter", self.transitionDict.get("other", 0))
        
        # Check for whitespace
        if key in [" ", "\t"]:
            return self.transitionDict.get("space", self.transitionDict.get("other", 0))
        
        # Check for specific character
        if key in self.transitionDict:
            return self.transitionDict[key]
        
        # Default to "other"
        return self.transitionDict.get("other", 0)

# Initialize scanner DFA
def create_scanner_dfa():
    # Create states for SimC scanner
    num_states = 30
    scannerDFA = [State() for _ in range(num_states)]
    
    # State 0: Start state
    scannerDFA[0].setStartState(True)
    scannerDFA[0].setDict({
        "\n": 0, "space": 0,
        "(": 1, ")": 2, "{": 3, "}": 4,
        ";": 5, ",": 6,
        "+": 7, "-": 8, "*": 9, "/": 10, "%": 11,
        "=": 12, "!": 14, "<": 16, ">": 18,
        "digit": 20, "letter": 22, "_": 22,
        "": 24,  # EOF
        "other": 25
    })
    
    # Delimiter states (1-6)
    scannerDFA[1].setEndState(True, "LPAREN")
    scannerDFA[2].setEndState(True, "RPAREN")
    scannerDFA[3].setEndState(True, "LBRACE")
    scannerDFA[4].setEndState(True, "RBRACE")
    scannerDFA[5].setEndState(True, "SEMI")
    scannerDFA[6].setEndState(True, "COMMA")
    
    # Arithmetic operators (7-11)
    scannerDFA[7].setEndState(True, "PLUS")
    scannerDFA[8].setEndState(True, "MINUS")
    scannerDFA[9].setEndState(True, "MUL")
    scannerDFA[10].setDict({"/": 26, "other": 27})  # Check for comment
    scannerDFA[10].setCheckpointState(True)
    scannerDFA[11].setEndState(True, "MOD")
    
    # Assignment and equality operators (12-15)
    scannerDFA[12].setDict({"=": 13, "other": 28})  # = or ==
    scannerDFA[12].setCheckpointState(True)
    scannerDFA[13].setEndState(True, "EQ")  # ==
    
    # Not equal (14-15)
    scannerDFA[14].setDict({"=": 15, "other": 25})  # !=
    scannerDFA[15].setEndState(True, "NE")
    
    # Less than operators (16-17)
    scannerDFA[16].setDict({"=": 17, "other": 29})  # < or <=
    scannerDFA[16].setCheckpointState(True)
    scannerDFA[17].setEndState(True, "LE")
    
    # Greater than operators (18-19)
    scannerDFA[18].setDict({"=": 19, "other": 29})  # > or >=
    scannerDFA[18].setCheckpointState(True)
    scannerDFA[19].setEndState(True, "GE")
    
    # Integer literals (20-21)
    scannerDFA[20].setDict({"digit": 20, "other": 21})
    scannerDFA[20].setCheckpointState(True)
    scannerDFA[21].setPushBackState(True, "INT")
    
    # Identifiers/Keywords (22-23)
    scannerDFA[22].setDict({
        "letter": 22, "digit": 22, "_": 22, 
        "other": 23
    })
    scannerDFA[22].setCheckpointState(True)
    scannerDFA[23].setPushBackState(True, "ID")
    
    # EOF (24)
    scannerDFA[24].setEndState(True, "EOF")
    
    # Error state (25)
    scannerDFA[25].setErrorState(True, "Illegal character")
    
    # Comment state (26)
    scannerDFA[26].setIgnoreState(True)
    scannerDFA[26].setDict({
        "\n": 0,  # End of comment, back to start
        "": 0,    # EOF ends comment
        "other": 26  # Continue in comment
    })
    
    # Division operator (27)
    scannerDFA[27].setPushBackState(True, "DIV")
    
    # Assignment operator (28)
    scannerDFA[28].setPushBackState(True, "ASSIGN")
    
    # Comparison operators pushback (29)
    scannerDFA[29].setPushBackState(True, "COMPARISON")
    
    return scannerDFA

class Scanner:
    def __init__(self, input_path):
        self.input_path = input_path
        with open(input_path, 'r') as f:
            self.input_stream = f.read()
        
        self.line_num = 1
        self.states = create_scanner_dfa()
        self.tokens = []
        
        # SimC keywords (case-sensitive)
        self.keywords = {
            'if': 'IF',
            'else': 'ELSE',
            'while': 'WHILE',
            'return': 'RETURN',
            'print': 'PRINT',
            'iread': 'IREAD'
        }
    
    def scan_file(self):
        """Scan the entire file and return list of tokens"""
        while len(self.input_stream) > 0:
            token = self.get_token()
            if token:
                self.tokens.append(token)
            if token and token.type == "EOF":
                break
        return self.tokens
    
    def get_token(self):
        """Get the next token from input stream"""
        auto_start = 0
        auto_current = auto_start
        token_string = ''
        checkpoint_string = ''
        
        while len(self.input_stream) > 0:
            char = self.input_stream[0]
            
            # Track line numbers
            if char == '\n':
                self.line_num += 1
            
            # Get next state
            auto_current = self.states[auto_current].getNewState(char)
            
            # Build token string (except for ignored states)
            if not self.states[auto_current].isIgnoreState() and auto_current != auto_start:
                token_string += char
            
            # Save checkpoint for pushback
            if self.states[auto_current].isCheckpointState():
                checkpoint_string = token_string
            
            # Consume character
            self.input_stream = self.input_stream[1:]
            
            # Handle ignore state (comments)
            if self.states[auto_current].isIgnoreState():
                token_string = ''
                continue
            
            # Handle error state
            if self.states[auto_current].isErrorState():
                print(f"Lexical Error: {self.states[auto_current].errorMsg} '{char}' at line {self.line_num}")
                return None
            
            # Handle end state
            if self.states[auto_current].isEndState():
                token_type = self.states[auto_current].tokenType
                
                # Check for keywords
                if token_type == "ID" and token_string in self.keywords:
                    token_type = self.keywords[token_string]
                
                # Handle special comparison operators
                if token_type == "COMPARISON":
                    if checkpoint_string == '<':
                        token_type = "LT"
                    elif checkpoint_string == '>':
                        token_type = "GT"
                    token_string = checkpoint_string
                
                return Token(token_type, token_string, self.line_num)
            
            # Handle pushback state
            if self.states[auto_current].isPushBackState():
                token_type = self.states[auto_current].tokenType
                
                # For pushback, use checkpoint string
                if checkpoint_string and token_type in ["COMPARISON", "ASSIGN", "DIV"]:
                    # Map to correct token types
                    if token_type == "COMPARISON":
                        if checkpoint_string == '<':
                            token_type = "LT"
                        elif checkpoint_string == '>':
                            token_type = "GT"
                    elif token_type == "DIV":
                        token_type = "DIV"
                    
                    # Push back characters after checkpoint
                    pushback_count = len(token_string) - len(checkpoint_string)
                    if pushback_count > 0:
                        self.input_stream = token_string[-pushback_count:] + self.input_stream
                    token_string = checkpoint_string
                else:
                    # Regular pushback - put last character back
                    if token_string:
                        self.input_stream = token_string[-1] + self.input_stream
                        token_string = token_string[:-1]
                
                # Check for keywords
                if token_type == "ID" and token_string in self.keywords:
                    token_type = self.keywords[token_string]
                
                return Token(token_type, token_string, self.line_num)
        
        # Handle EOF
        if len(self.input_stream) == 0:
            # Check if we have a pending token
            if token_string:
                # Process pending identifier or number
                if auto_current == 22:  # Identifier state
                    token_type = "ID"
                    if token_string in self.keywords:
                        token_type = self.keywords[token_string]
                    return Token(token_type, token_string, self.line_num)
                elif auto_current == 20:  # Number state
                    return Token("INT", token_string, self.line_num)
            
            # Return EOF token
            return Token("EOF", "", self.line_num)
        
        return None
    
'''
===========================================================
SimC Recursive Descent Parser
===========================================================

This parser takes a token list (output from the scanner) and
produces an Abstract Syntax Tree (AST) representing the
SimC program structure.

The AST serves as the input for the Intermediate Code
Generator (ICG) that produces Three-Address Code (TAC).
'''

class ParserError(Exception):
    '''Raised when a syntax error is encountered during parsing.'''
    pass


class Parser:
    '''
    The Parser class implements a recursive descent parser for
    the simplified C-like SimC language. It constructs a
    structured Abstract Syntax Tree (AST) for each valid
    statement, expression, and function definition.
    '''

    def __init__(self, tokens: List[Dict[str, str]]):
        '''Initialize the parser with a list of tokens.'''
        self.tokens = tokens
        self.pos = 0

    '''--------------------- Utility Methods ---------------------'''

    def peek(self) -> Dict[str, str]:
        '''Return the current token without consuming it.'''
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return {'type': 'EOF', 'value': ''}

    def advance(self) -> Dict[str, str]:
        '''Consume and return the current token.'''
        tok = self.peek()
        self.pos += 1
        return tok

    def match(self, expected_type: str):
        '''Ensure the next token matches the expected type.'''
        tok = self.peek()
        if tok['type'] == expected_type:
            self.advance()
            return tok
        raise ParserError(f"Expected {expected_type}, got {tok}")

    '''---------------------- Entry Point ------------------------'''

    def parse_program(self):
        '''
        Parse the entire program.
        A program may contain multiple function definitions
        followed by global-level statements.
        '''
        functions = []
        statements = []
        while self.peek()['type'] != 'EOF':
            if self.peek()['type'] == 'ID' and self._is_function_def():
                functions.append(self.parse_function())
            else:
                statements.append(self.parse_statement())
        return {'type': 'Program', 'functions': functions, 'statements': statements}

    def _is_function_def(self):
        '''Check ahead to determine if the current token begins a function definition.'''
        if (self.pos + 1 < len(self.tokens)
            and self.tokens[self.pos + 1]['type'] == 'LPAREN'):
            for i in range(self.pos + 2, len(self.tokens)):
                if self.tokens[i]['type'] == 'RPAREN':
                    if (i + 1 < len(self.tokens)
                        and self.tokens[i + 1]['type'] == 'LBRACE'):
                        return True
        return False

    '''---------------------- Grammar Rules ----------------------'''

    def parse_function(self):
        '''Parse a function definition: ID(params) { statements }'''
        name = self.match('ID')['value']
        self.match('LPAREN')
        params = []
        if self.peek()['type'] != 'RPAREN':
            params.append(self.match('ID')['value'])
            while self.peek()['type'] == 'COMMA':
                self.advance()
                params.append(self.match('ID')['value'])
        self.match('RPAREN')
        body = self.parse_block()
        return {'type': 'FunctionDef', 'name': name, 'params': params, 'body': body}

    def parse_block(self):
        '''Parse a statement block enclosed in braces.'''
        stmts = []
        self.match('LBRACE')
        while self.peek()['type'] != 'RBRACE':
            stmts.append(self.parse_statement())
        self.match('RBRACE')
        return stmts

    def parse_statement(self):
        '''Determine and parse the next statement type.'''
        tok = self.peek()
        if tok['type'] == 'IF':
            return self.parse_if()
        elif tok['type'] == 'WHILE':
            return self.parse_while()
        elif tok['type'] == 'RETURN':
            return self.parse_return()
        elif tok['type'] == 'PRINT':
            return self.parse_print()
        elif tok['type'] == 'ID':
            return self.parse_assignment()
        else:
            raise ParserError(f"Unexpected token {tok}")

    def parse_if(self):
        '''Parse an if-else statement.'''
        self.match('IF')
        self.match('LPAREN')
        cond = self.parse_expression()
        self.match('RPAREN')
        then_block = self.parse_block()
        else_block = []
        if self.peek()['type'] == 'ELSE':
            self.advance()
            else_block = self.parse_block()
        return {'type': 'If', 'condition': cond, 'then': then_block, 'else': else_block}

    def parse_while(self):
        '''Parse a while loop.'''
        self.match('WHILE')
        self.match('LPAREN')
        cond = self.parse_expression()
        self.match('RPAREN')
        body = self.parse_block()
        return {'type': 'While', 'condition': cond, 'body': body}

    def parse_return(self):
        '''Parse a return statement.'''
        self.match('RETURN')
        expr = self.parse_expression()
        self.match('SEMI')
        return {'type': 'Return', 'value': expr}

    def parse_print(self):
        '''Parse a print statement.'''
        self.match('PRINT')
        self.match('LPAREN')
        expr = self.parse_expression()
        self.match('RPAREN')
        self.match('SEMI')
        return {'type': 'Print', 'value': expr}

    def parse_assignment(self):
        '''Parse an assignment or function call assignment.'''
        name = self.match('ID')['value']
        self.match('ASSIGN')
        expr = None
        if self.peek()['type'] == 'IREAD':
            self.advance()
            self.match('LPAREN')
            self.match('RPAREN')
            expr = {'type': 'FuncCall', 'name': 'iread', 'args': []}
        elif self.peek()['type'] == 'ID' and self._is_func_call():
            expr = self.parse_function_call()
        else:
            expr = self.parse_expression()
        self.match('SEMI')
        return {'type': 'Assignment', 'target': name, 'value': expr}

    def _is_func_call(self):
        '''Check if the current identifier starts a function call.'''
        return (self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1]['type'] == 'LPAREN')

    def parse_function_call(self):
        '''Parse a function call expression.'''
        name = self.match('ID')['value']
        self.match('LPAREN')
        args = []
        if self.peek()['type'] != 'RPAREN':
            args.append(self.parse_expression())
            while self.peek()['type'] == 'COMMA':
                self.advance()
                args.append(self.parse_expression())
        self.match('RPAREN')
        return {'type': 'FuncCall', 'name': name, 'args': args}

    '''------------------- Expression Parsing --------------------'''

    def parse_expression(self):
        '''Parse an expression, starting from relational operators.'''
        return self.parse_relational()

    def parse_relational(self):
        '''Parse relational operations (>, <, >=, <=, ==, !=).'''
        left = self.parse_term()
        while self.peek()['type'] in ('LT', 'GT', 'LE', 'GE', 'EQ', 'NE'):
            op = self.advance()['value']
            right = self.parse_term()
            left = {'type': 'BinaryOp', 'op': op, 'left': left, 'right': right}
        return left

    def parse_term(self):
        '''Parse addition and subtraction expressions.'''
        left = self.parse_factor()
        while self.peek()['type'] in ('PLUS', 'MINUS'):
            op = self.advance()['value']
            right = self.parse_factor()
            left = {'type': 'BinaryOp', 'op': op, 'left': left, 'right': right}
        return left

    def parse_factor(self):
        '''Parse multiplication, division, and modulo operations.'''
        left = self.parse_primary()
        while self.peek()['type'] in ('MUL', 'DIV', 'MOD'):
            op = self.advance()['value']
            right = self.parse_primary()
            left = {'type': 'BinaryOp', 'op': op, 'left': left, 'right': right}
        return left

    def parse_primary(self):
        '''Parse literals, identifiers, or parenthesized sub-expressions.'''
        tok = self.peek()
        if tok['type'] == 'INT':
            self.advance()
            return {'type': 'IntConst', 'value': int(tok['value'])}
        elif tok['type'] == 'ID':
            if self._is_func_call():
                return self.parse_function_call()
            return {'type': 'Var', 'name': self.advance()['value']}
        elif tok['type'] == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.match('RPAREN')
            return expr
        else:
            raise ParserError(f"Unexpected token in expression: {tok}")

def main():

    # open input file to be scanned
    if len(sys.argv) != 2:
        print("Usage: python scanner.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Create scanner and scan file
    scanner = Scanner(input_file)
    tokens = scanner.scan_file()

    # Convert tokens to JSON format
    tokens = [token.to_dict() for token in tokens]
    
    # scanner output for safekeeping
    with open("scanner_output.txt", "w") as f:
        json.dump(tokens, f, indent=4)

    print('Token lists saved to scanner_output.txt')

    parser = Parser(tokens)
    ast = parser.parse_program()

    with open("parser_output.txt", "w") as f:
        json.dump(ast, f, indent=4)

    with open("sample_parser_out.txt", "r") as f:
        expected = json.load(f)

    # verify parser output
    if ast == expected:
        print("Parser output matches expected sample_out.txt")
    else:
        print("Parser output differs from expected sample_out.txt")
        print("Generated output saved to parser_output.txt")

if __name__ == "__main__":
    main()