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

from typing import List, Dict


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
        """Parse relational operations (>, <, >=, <=, ==, !=)."""
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
            op_tok = self.advance()
            op = op_tok['value']
            right = self.parse_factor()
            left = {'type': 'BinaryOp', 'op': op, 'left': left, 'right': right}
        return left

    def parse_factor(self):
        '''Parse multiplication, division, and modulo operations.'''
        left = self.parse_primary()
        while self.peek()['type'] in ('MUL', 'DIV', 'MOD'):
            op_tok = self.advance()
            op = op_tok['value']
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
            raise ParserError(f"Unexpected token in expression at pos {self.pos}: {tok}")
