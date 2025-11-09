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