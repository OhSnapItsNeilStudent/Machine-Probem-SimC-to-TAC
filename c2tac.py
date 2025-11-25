'''

Nics De Vega (ID: 211951)
Christianneil Ocampo (ID: 214293)
Jenica Vizmanos (ID: 216351)
November 25, 2025
CSCI 202 WX2
[Machine Problem] SimC to Three-Address Code Translator

Source Code Certification:
We have not discussed the Python language code in our program with anyone 
other than my instructor or the teaching assistants assigned to this course.
We have not used Python language code obtained from another student, or any 
other unauthorized source, either modified or unmodified.
If any Python language code or documentation used in our program was obtained 
from another source, such as a textbook or course notes, that has been clearly 
noted with a proper citation in the comments of our program.

Sources:
    https://www.w3schools.com/python/python_regex.asp
    https://docs.python.org/3/library/re.html

'''

import sys
import re
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
        if tok['type'] == 'MINUS':
            self.advance()
            operand = self.parse_primary()
            return {'type': 'UnaryOp', 'op': '-', 'operand': operand}
        elif tok['type'] == 'INT':
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

'''
===========================================================
SimC Intermediate Code Generator (ICG)
===========================================================

This intermediate code generator takes an Abstract Syntax 
Tree (AST), which is formatted like a JSON file, and produces 
the corresponding Three-Address Code (TAC) instructions.

'''

class IntermediateCodeGenerator:
    def __init__(self, ast):
        # input AST (from parser)
        self.ast = ast
        # list of string instructions emitted 
        self.instructions = []
        # label -> instruction index
        self.labels = {}

        # global var names, including temporary global variables
        self.globals_list = []
        # name -> numeric mem index (assigned in finalize)
        self.globals_map = {}
        
        # temporary globals (for main program) which store 
        # placeholder names like mem[GLOBAL_t0]. 
        self.temp_globals = []
        self.free_temp_globals = []

        # registers r1..r16 (temporary pool for functions)
        # used in a stack-like manner, following LIFO
        self.regs = [f'r{i}' for i in range(16, 0, -1)]
        self.free_regs = self.regs.copy()
        
        # counters 
        self.label_count = 0
        self.return_count = 0
        self.global_temp_count = 0

        # Main program label
        self.main_label = 'MAIN'

    '''--------------------- Emit Methods ---------------------'''
    
    def emit(self, code):
        """Append a textual instruction and returns its index."""
        self.instructions.append(code)
        return len(self.instructions) - 1

    def emit_label(self, name):
        """Record a label as mapping to the next instruction index."""
        # This follows 0-based indexing. 
        self.labels[name] = len(self.instructions)


    '''--------------------- Globals / Global Temps ---------------------'''
    
    def add_global(self, name):
        """Adds a new global name/label."""
        if name not in self.globals_list:
            self.globals_list.append(name)

    def get_global_addr(self, name):
        """
        Adds a new global name/label and returns a placeholder mem[...] string
        All globals in emit are recorded as mem[GLOBAL_{name}]
        """
        self.add_global(name)
        return f'mem[GLOBAL_{name}]'

    # All temps follow a LIFO order in terms of allocation and de-allocation

    def new_global_temp_addr(self):
        """Create or allocate a named temp global and return its placeholder mem[...] string."""
        if not self.free_temp_globals: 
            name = f't{self.global_temp_count}'
            self.global_temp_count += 1
            self.add_global(name)
            placeholder = f'mem[GLOBAL_{name}]'
            self.temp_globals.append(placeholder)
            # newly created temp is immediately considered used; no entry added to free list
            return placeholder
        return self.free_temp_globals.pop()
        
    def free_global_temp(self, temp):
        """Add a temp global to the free temp globals list."""
        if temp in self.temp_globals and temp not in self.free_temp_globals:
            self.free_temp_globals.append(temp)

    '''--------------------- Registers ---------------------'''
    
    def alloc_reg(self):
        """Allocate a register, following LIFO."""
        # if exhausted (e.g., no free registers left), spill to r1 
        # This implements a simple deterministic fallback to prevent invalid TAC
        if not self.free_regs:
            return 'r1'
        # pop from the free_regs 
        return self.free_regs.pop()

    def free_reg(self, r):
        """Free a register, following LIFO."""
        if r in self.regs and r not in self.free_regs:
            self.free_regs.append(r)

    '''--------------------- Handling Temps Methods for Convenience ---------------------'''
    
    # Functions use registers for temps
    # Main program statements use memory locations (i.e., temp globals)

    def new_temp(self, in_function):
        """Allocate a register or a global temp."""
        if in_function:
            return self.alloc_reg()
        else:
            return self.new_global_temp_addr()

    def free_temp(self, in_function, name):
        """Free a register or a global temp."""
        if in_function: 
            # name should be a register
            return self.free_reg(name)
        else:
            # name is a temp global identifier like 't0'
            return self.free_global_temp(name)
    
    '''--------------------- Labels ---------------------'''
    
    def new_return_label(self):
        label = f'RET{self.return_count}'
        self.return_count += 1
        return label

    def new_label(self, prefix='L'):
        label = f'{prefix}{self.label_count}'
        self.label_count += 1
        return label

    '''--------------------- Process Expressions ---------------------'''
    
    def expr(self, e, in_function, params_map, locals_map, target_address=''):
        """
        Generate instructions for an expression and return an operand (register/mem/literal) or None.
        Note: target_address is only used for function calls. In this case, the instruction for the 
        assignment statement gets produced here instead of being produced in the stmt function.
        """

        e_type = e['type']

        # For constants
        if e_type == 'IntConst':
            return str(e['value'])
        
        # For variables
        if e_type == 'Var':
            name = e['name']
            if in_function:
                if name in params_map:
                    return f'mem[{params_map[name]} + bp]'
                else:
                    if name not in locals_map:
                        # allocate new local slot if referenced 
                        # (doesn't really happen but placed here for safety)
                        locals_map[name] = -(len(locals_map) + 1)
                    return f'mem[{locals_map[name]} + bp]'
            else:
                return self.get_global_addr(name)
        
        # For BinaryOp
        if e_type == 'BinaryOp':
            left = self.expr(e['left'], in_function, params_map, locals_map)
            right = self.expr(e['right'], in_function, params_map, locals_map)
            op = e['op']
            
            # Left operands must always be a temp global (in main) or a register (in function).
            # If the left operand is a constant, it'll be placed in a temp global or register.
            # The location of the left operand will always be the location of the resulting operation.
            left_reg = None
            if left.startswith('r') or left in self.temp_globals:
                left_reg = left
            else:
                left_reg = self.new_temp(in_function)
                self.emit(f'{left_reg} = {left}')

            # For the right operand, if it's an immediate integer constant, then use it inline.
            # -> This means that there's no need to create a temp global or register; just use it as is.
            right_is_imm = isinstance(right, str) and right.lstrip('-').isdigit()
            if right_is_imm:
                right_op = right
                right_reg = None
                right_is_temp = False
            else:
                # Otherwise, there's no need to assign a temp var to another temp again. 
                if right.startswith('r') or right in self.temp_globals:
                    right_reg = right
                    right_op = right_reg
                    right_is_temp = True
                else:
                    # Create a new temp to place the right operand.
                    right_reg = self.new_temp(in_function)
                    self.emit(f'{right_reg} = {right}')
                    right_op = right_reg
                    right_is_temp = True

            # Emit the operation into the left_reg (which is either a register or a temp global)
            self.emit(f'{left_reg} = {left_reg} {op} {right_op}')

            # free right if it's a temp before or a temp we allocated (and different from left for safety)
            if right_is_temp and right_reg is not None and right_reg != left_reg:
                # right_reg is either a register or a temp global
                self.free_temp(in_function, right_reg)

            # Return the left register (or temp global) that holds the result
            # The caller is responsible for freeing the resulting register or temp global when appropriate.
            return left_reg
        
        # PADOUBLE CHECK JENICA
        if e_type == 'UnaryOp':
            op = e['op']
            operand = self.expr(e['operand'], in_function, params_map, locals_map)

            if op == '-':
                t = self.new_temp(in_function)        # <-- FIX
                self.emit(f"{t} = 0 - {operand}")
                return t

            else:
                raise Exception("Unknown unary operator: " + op)

        
        # For function calls
        if e_type == 'FuncCall':
            # iread case
            if e['name'] == 'iread':
                r = self.new_temp(in_function)
                self.emit(f'{r} = iread()')
                return r
            
            # Otherwise, 
            #   push args from left-to-right, push return address, 
            #   go to function (ip = func_label)
            else:
                # Setup arguments
                for args in e.get('args', []):
                    op = self.expr(args, in_function, params_map, locals_map)
                    self.emit('sp = sp - 1')
                    self.emit(f'mem[sp] = {op}')
                    if op.startswith('r') or op in self.temp_globals:
                        self.free_temp(in_function, op)
                
                # Save the return label 
                # return_label is like 'RET0'
                return_label = self.new_return_label()
                self.emit('sp = sp - 1')
                self.emit(f'mem[sp] = {return_label}')
                
                # Call function
                f_label = f"FUNC_{e['name']}"
                self.emit(f'ip = {f_label}')

                # Mark the continuation after function returns -> emit return label
                self.emit_label(return_label)

                # If the caller provided a target_address, write ac to it, 
                # clean up stack, and return None. This is usually for when the 
                # statement is an assignment where you assign a variable to the 
                # result of the function (e.g., result = fact(5)).
                if target_address != '':
                    self.emit(f'{target_address} = ac')
                    self.emit(f'sp = sp + {len(e.get('args', [])) + 1}')
                    return None
                
                else: 
                    # If the function is called as part of other statements 
                    # (e.g. part of another operation), return the resulting temp 
                    # where the function result is temporarily stored.
                    r = self.new_temp(in_function)
                    self.emit(f'{r} = ac')
                    self.emit(f'sp = sp + {len(e.get('args', [])) + 1}')
                    return r
        
        # raise an exception if the expression wasn't processed as part of any cases above
        raise Exception('Unhandled expression: ' + str(e_type))

    '''--------------------- Process Statements ---------------------'''
    
    # For both while and if statements, we invert their relational operators 
    # so that the format of the instructions are like the following:

    #   IF a inv_op b: go to ELSE
    #   THEN statements 
    #   go to ENDIF 
    #   ELSE statements

    #   IF a inv_op b: go to ENDWHILE
    #   WHILEBODY statements
    #   go back to WHILESTART
    #   ENDWHILE (*Note that ENDWHILE is just a label and not really 
    #   an instruction, so, in terms of instructions, it's referring to 
    #   the next instruction after the WHILE statement.)

    # Helper Method
    def invert_op(self, op):
        """
        Invert relational operator for conditional statements. 
        This is used in processing if statements and while loops.
        """
        return {'>': '<=',
                '<': '>=',
                '>=': '<',
                '<=': '>',
                '==': '!=',
                '!=': '=='}[op]

    def stmt(self, s, in_function, params_map, locals_map):
        """
        Generate instructions for a statement. Note that this returns 
        True if a Return statement was processed.
        """
        s_type = s['type']

        # For assignment statement
        if s_type == 'Assignment':
            target = s['target']
            value = s['value']
            if in_function:
                if target in params_map:
                    address = f'mem[{params_map[target]} + bp]'
                else:
                    if target not in locals_map:
                        # allocate new local slot  
                        # (doesn't really happen but placed here for safety)
                        next_offset = -(len(locals_map) + 1)
                        locals_map[target] = next_offset
                    address = f'mem[{locals_map[target]} + bp]'
            else:
                address = self.get_global_addr(target)
            
            # case for if the right-hand side (RHS) is iread()
            if value['type'] == 'FuncCall' and value['name'] == 'iread':
                self.emit(f'{address} = iread()')
                return False
            
            # Otherwise, a general processing is performed for the expression in RHS.
            r = self.expr(value, in_function, params_map, locals_map, address)
            
            # r is not None -> usually indicates that the RHS is not a function call
            # In this case, we need to emit instructions.
            if r is not None: 
                self.emit(f'{address} = {r}')
                if r.startswith('r') or r in self.temp_globals:
                    self.free_temp(in_function, r)
            
            return False
        
        # For print statement
        if s_type == 'Print':
            r = self.expr(s['value'], in_function, params_map, locals_map)
            self.emit(f'print({r})')
            if r.startswith('r') or r in self.temp_globals:
                self.free_temp(in_function, r)
            return False

        # For return statement 
        # Note that the Return statement is only used within functions, 
        # so we can safely assume that registers were (if ever) used as 
        # temporary storage. 
        if s_type == 'Return':
            r = self.expr(s['value'], in_function, params_map, locals_map)
            self.emit(f'ac = {r}')
            if r.startswith('r'):
                self.free_reg(r)
            # pop saved bp + locals 
            num_locals = len(locals_map) if locals_map is not None else 0
            self.emit(f'sp = sp + {1 + num_locals}')
            
            # Restore the stack before returning to the callee.
            self.emit('r1 = mem[1 + bp]')
            self.emit('bp = mem[bp]')
            self.emit('ip = r1')

            # signal that a return statement has been processed 
            # so the function processing doesn't emit the default 
            # return instructions 
            return True 

        # For if statement
        elif s_type == 'If':
            cond = s['condition']

            # Safety-check for relational condition 
            # Note: In practice, it's possible to have a non-relational condition, 
            # but this is not part of the scope of the grammar, so we don't consider
            # or implement those cases. The checking for conditional relation is only 
            # placed to prevent invalid conditions from being processed, although this
            # is highly unlikely. 
            if cond['type'] == 'BinaryOp' and cond['op'] in ['<', '>', '<=', '>=', '==', '!=']:
                left = self.expr(cond['left'], in_function, params_map, locals_map)
                right = self.expr(cond['right'], in_function, params_map, locals_map)
                # invert condition
                inv = self.invert_op(cond['op'])

                # Always create a new destination temp to store the resulting boolean
                r = self.new_temp(in_function)
                self.emit(f'{r} = {left} {inv} {right}')

                # free temps
                if left.startswith('r') or left in self.temp_globals:
                    self.free_temp(in_function, left)
                if right.startswith('r') or right in self.temp_globals:
                    self.free_temp(in_function, right)

                # create labels
                else_label = self.new_label('ELSE')
                end_label = self.new_label('ENDIF')

                # If the inverted condition is true, skip THEN & go to ELSE
                self.emit(f'if {r}: ip = {else_label}')

                # free r since it's no longer needed 
                self.free_temp(in_function, r)

                # process the THEN block
                for sub_s in s['then']:
                    self.stmt(sub_s, in_function, params_map, locals_map)

                # Only jump to an ENDIF location if there's an ELSE statement 
                # in the whole IF statement
                if s.get('else', []) != []: 
                    self.emit(f'ip = {end_label}')

                # ELSE label
                self.emit_label(else_label)

                # process the ELSE block
                for sub_s in s.get('else', []):
                    self.stmt(sub_s, in_function, params_map, locals_map)

                # ENDIF label
                self.emit_label(end_label)

                return False
        
        # For while statement
        if s_type == 'While':
            # create labels 
            start_label = self.new_label('WHILESTART')
            body_label = self.new_label('WHILEBODY')
            end_label = self.new_label('ENDWHILE')

            # WHILESTART label
            self.emit_label(start_label)

            cond = s['condition']

            # Similar to if statement, check the condition for safety.
            if cond['type'] == 'BinaryOp' and cond['op'] in ['<', '>', '<=', '>=', '==', '!=']:
                left = self.expr(cond['left'], in_function, params_map, locals_map)
                right = self.expr(cond['right'], in_function, params_map, locals_map)
                # invert condition
                inv = self.invert_op(cond['op'])

                # Always create a new destination temp to store the resulting boolean
                r = self.new_temp(in_function)
                self.emit(f'{r} = {left} {inv} {right}')

                # free temps
                if left.startswith('r') or left in self.temp_globals:
                    self.free_temp(in_function, left)
                if right.startswith('r') or right in self.temp_globals:
                    self.free_temp(in_function, right)

                # If the inverted condition is true, exit the while loop.
                self.emit(f'if {r}: ip = {end_label}')

                # free r since it's no longer needed 
                self.free_temp(in_function, r)

                # WHILEBODY label
                self.emit_label(body_label)

                # process the WHILEBODY block
                for sub_s in s['body']:
                    self.stmt(sub_s, in_function, params_map, locals_map)

                # jump back to WHILESTART
                self.emit(f'ip = {start_label}')

                # ENDWHILE label
                self.emit_label(end_label)

                return False

        # raise an exception if the statement wasn't processed as part of any cases above
        raise Exception('Unhandled statement: ' + str(s_type))

    '''--------------------- Scan Locals in Functions ---------------------'''
    
    # Only specifically used for functions
    # This is done before generating TAC for function body 

    def scan_locals(self, params, body):
        """Identify all local variables that must be allocated stack slots."""
        
        # Use sets so that adding an element that's already in the set 
        # won't result to any changes 
        locals_set = set()

        def peek_stmt(s):
            s_type = s['type']
            if s_type == 'Assignment':
                s_target = s['target'] 
                if s_target not in params:
                    locals_set.add(s_target)

            # For both If and While, there are no local variable declaration in condition statements
            elif s_type == 'If':
                # there is at least 1 valid statement in the then part 
                for sub_s in s['then']:
                    peek_stmt(sub_s)
                # It's possible for else to not contain any statements
                for sub_s in s.get('else', []):
                    peek_stmt(sub_s)
            elif s_type == 'While':
                for sub_s in s['body']:
                    peek_stmt(sub_s)
            
            elif s_type == 'Return':
                pass
            elif s_type == 'Print':
                pass

        for s in body:
            peek_stmt(s)

        # Convert set to list and return it
        return list(locals_set)

    '''--------------------- Process the Function Body ---------------------'''

    def func_body(self, body, in_function, params_map, locals_map):
        """
        Process each statement in the function body.
        It returns True if a Return statement was processed in the stmt function.
        """
        returned = False 
        for s in body:
            ret_here = self.stmt(s, in_function, params_map, locals_map)
            if ret_here:
                returned = True
        return returned 

    '''--------------------- Process Functions ---------------------'''

    def func(self, f):
        """
        Generate instructions for a function.
        """
        name = f['name']
        params = f['params']
        body = f['body']

        # Function label
        f_label = f'FUNC_{name}'
        self.emit_label(f_label)

        # Setting up the new stack frame for the callee. 
        self.emit('sp = sp - 1')
        self.emit('mem[sp] = bp')
        self.emit('bp = sp')

        # Find the local variables
        locals_list = self.scan_locals(params, body)

        # params start at 2+i because bp + 1 is allocated for the return address of the function
        # params is located before bp
        params_map = {p: 2+i for i, p in enumerate(params)}
        # locals is at negative offset from bp (after bp)
        locals_map = {l: -(i+1) for i, l in enumerate(locals_list)}

        # Allocate space for locals only if they exist
        if len(locals_list) > 0:
            self.emit(f'sp = sp - {len(locals_list)}')

        # In func_body, in_function = True
        returned = self.func_body(body, True, params_map, locals_map)

        # Default return
        # If no return is explicitly specified, then emit these instructions.
        if returned == False:
            self.emit('ac = 0')
            # pop saved bp + locals
            num_locals = len(locals_list)
            self.emit(f'sp = sp + {1 + num_locals}')
            self.emit('r1 = mem[1 + bp]')
            self.emit('bp = mem[bp]')
            self.emit('ip = r1')

    '''--------------------- Start Program ---------------------'''
    
    # This will be called first in the main program after creating an 
    # instance of ICG.

    def start_program(self):
        """Initiate the creation of the TAC instructions."""
        # initial jump to main (main_label will be substituted in finalize)
        self.emit(f'ip = {self.main_label}')
        
        # process functions first 
        #
        # self.ast.get('functions', []) 
        #   -> returns a list of function content
        #   -> if there are no functions defined, return an empty list
        for f in self.ast.get('functions', []):
            # per function processing
            self.func(f)
        
        # emit the label (main label) to know where main starts
        self.emit_label(self.main_label)
        
        # process the main program statements 
        for s in self.ast.get('statements', []):
            # for self.stmt, 
            #   in_function = False; 
            #   params & locals map are just empty dictionaries {}
            self.stmt(s, False, {}, {})

        # emit halt to signify end of instructions
        self.emit('halt')

    '''--------------------- Finalize the Instructions ---------------------'''

    def finalize(self, out_filename):
        """
        Replace labels and GLOBAL placeholders with numeric indices (essentially backpatching), 
        and write to file.
        """
        # Assign global addresses immediately after code
        # Note that the instructions follow a 0-based indexing.
        code_len = len(self.instructions)
        for i, name in enumerate(self.globals_list):
            self.globals_map[name] = code_len + i
        
        # Precompile replacement patterns for globals and labels
        # GLOBAL_x -> numeric locations
        global_keys = [f'GLOBAL_{re.escape(n)}' for n in self.globals_list]
        label_keys = [re.escape(k) for k in self.labels.keys()]
        globals_pattern = re.compile(r"\b(?:" + "|".join(global_keys) + r")\b") if global_keys else None
        labels_pattern = re.compile(r"\b(?:" + "|".join(label_keys) + r")\b") if label_keys else None

        # Whenever regex finds a match, replace_globals and replace_labels are run to replace 
        # the names with numeric indices.
        def replace_globals(matchobj):
            token = matchobj.group(0)
            name = token[len('GLOBAL_'):]
            return str(self.globals_map[name])

        def replace_labels(matchobj):
            token = matchobj.group(0)
            return str(self.labels[token])

        lines = []
        for i, code in enumerate(self.instructions):
            line = code
            # replace GLOBAL_ occurrences
            if globals_pattern is not None:
                line = globals_pattern.sub(replace_globals, line)
             # replace labels
            if labels_pattern is not None:
                line = labels_pattern.sub(replace_labels, line)
            
            lines.append(line)
        
        # Write the output 
        #
        # Note that while globals occupy slots (i.e., in memory indices) after all the 
        # instructions and are referenced from those locations, they don't have any 
        # initializer lines in the list of instructions.
        with open(out_filename, 'w') as f:
            for line in lines:
                f.write(line + '\n')

        print('Successfully generated TAC in', out_filename)

def main():

    # open input file to be scanned
    if len(sys.argv) != 2:
        print("Usage: python c2tac.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Create scanner and scan file
    scanner = Scanner(input_file)
    tokens = scanner.scan_file()

    # Convert tokens to JSON format
    tokens = [token.to_dict() for token in tokens]

    parser = Parser(tokens)
    ast = parser.parse_program()

    # generate TAC
    icg = IntermediateCodeGenerator(ast)
    icg.start_program()

    # finalize and create the output file 
    # Note: The input_file must end with '.smc'.  
    out_file = input_file[:-4] + '.tac'
    icg.finalize(out_file)

if __name__ == "__main__":
    main()