# README - SimC to Three-Address Code Translator

### Nics De Vega (211951)
### Christianneil Emmanuel Ocampo (214293)
### Jenica Alea Vizmanos (216351)

## General Description

This Python program implements a compiler translator that converts source programs written in SimC (a simplified C-like language) into Three-Address Code (TAC). The translator performs lexical analysis using a 30-state DFA, syntax analysis using recursive descent parsing to build an Abstract Syntax Tree, and intermediate code generation (in progress) to produce TAC instructions compatible with a virtual machine simulator.

The implementation uses standard compiler construction techniques: a DFA-based scanner for tokenization, a recursive descent parser for syntax validation and AST generation, and a planned code generator that will emit three-address instructions following a specific instruction set and memory model with register-based architecture.

---

## Design Approach

### Phase 1: Lexical Analysis (Scanner)
- Implements a **30-state Deterministic Finite Automaton (DFA)** for token recognition
- Uses `State` class to represent each DFA state with transition dictionaries and state properties
- Handles single and two-character operators using checkpoint states with lookahead and pushback mechanism
- Processes comments (// style) through ignore states that consume characters until newline
- Recognizes keywords, identifiers, integers, operators, and delimiters
- Tracks line numbers for error reporting

### Phase 2: Syntax Analysis (Parser)
- Uses **recursive descent parsing** with each grammar rule as a separate method
- Builds an **Abstract Syntax Tree (AST)** in hierarchical dictionary format
- Implements operator precedence through multi-level parsing:
  - `parse_relational()`: Relational operators (>, <, >=, <=, ==, !=)
  - `parse_term()`: Addition/subtraction
  - `parse_factor()`: Multiplication/division/modulo
  - `parse_primary()`: Literals, variables, function calls, parenthesized expressions
- Uses predictive parsing with `peek()` and `match()` operations

### Phase 3: Intermediate Code Generation *(In Progress)*
- **Symbol Table**: Will track global/local variables, functions, and parameters with memory locations
- **Memory Model**: Linear array (mem[]) partitioned into TAC instructions, global variables, and stack frames
- **Register Management**: 16 general-purpose registers (r1-r16) with planned reuse mechanism
- **Control Flow**: Standard translation using conditional/unconditional jumps with backpatching
- **Function Calls**: Activation records following calling convention in specification

---

## Python Classes Developed

### 1. Token Class
**Purpose**: Represents individual lexical tokens

**Attributes**:
- `type`: Token category (ID, INT, WHILE, IF, LPAREN, etc.)
- `value`: Literal string value
- `line_num`: Line number for error reporting

**Methods**:
- `to_dict()`: Converts token to dictionary format for JSON output

### 2. State Class
**Purpose**: Represents a single state in the scanner's DFA

**Key Methods**:
- `setDict(inputDict)`: Sets transition dictionary for the state
- `setEndState(endState, tokenType)`: Marks state as end state with token type
- `setCheckpointState(checkpointState)`: Marks state as checkpoint for lookahead
- `setPushBackState(pushBackState, tokenType)`: Marks state as pushback state
- `setIgnoreState(ignoreState)`: Marks state to ignore characters (for comments)
- `setErrorState(errorState, errorMsg)`: Marks state as error state
- `getNewState(key)`: Returns next state based on input character

### 3. Scanner Class
**Purpose**: Tokenizes SimC source code using 30-state DFA

**Key Attributes**:
- `input_path`: Path to input file
- `input_stream`: Contents of input file
- `line_num`: Current line number
- `states`: List of State objects representing the DFA
- `tokens`: List of generated tokens
- `keywords`: Dictionary mapping keyword strings to token types

**Key Methods**:
- `scan_file()`: Scans entire file and returns list of tokens
- `get_token()`: Gets next token from input stream using DFA transitions

**DFA Design** (via `create_scanner_dfa()` function): 30 states including:
- State 0: Start state
- States 1-6: Direct recognition for delimiters (parentheses, braces, semicolon, comma)
- States 7-11: Arithmetic operators (+, -, *, /, %)
- States 12-13: Assignment and equality (=, ==)
- States 14-15: Not equal (!=)
- States 16-17: Less than operators (<, <=)
- States 18-19: Greater than operators (>, >=)
- States 20-21: Integer literal recognition with accumulation and pushback
- States 22-23: Identifier/keyword recognition with accumulation and pushback
- State 24: EOF
- State 25: Error state
- State 26: Comment ignore state
- States 27-29: Pushback states for division, assignment, and comparison operators

### 4. Parser Class
**Purpose**: Validates syntax and builds Abstract Syntax Tree

**Key Attributes**:
- `tokens`: List of token dictionaries from scanner
- `pos`: Current position in token list

**Key Methods**:
- `peek()`: Returns current token without consuming it
- `advance()`: Consumes and returns current token
- `match(expected_type)`: Ensures next token matches expected type or raises error
- `parse_program()`: Entry point, returns Program node with functions and statements
- `parse_function()`: Parses function definitions with parameters
- `parse_block()`: Parses statement blocks enclosed in braces
- `parse_statement()`: Dispatches to appropriate statement parser
- `parse_if()`: Parses if-else conditionals
- `parse_while()`: Parses while loops
- `parse_return()`: Parses return statements
- `parse_print()`: Parses print statements
- `parse_assignment()`: Parses variable assignments and iread() calls
- `parse_function_call()`: Parses function call expressions
- `parse_expression()`: Entry point for expression parsing
- `parse_relational()`: Parses relational operators (>, <, >=, <=, ==, !=)
- `parse_term()`: Parses addition and subtraction
- `parse_factor()`: Parses multiplication, division, and modulo
- `parse_primary()`: Parses literals, identifiers, function calls, and parenthesized expressions
- `_is_function_def()`: Lookahead helper to detect function definitions
- `_is_func_call()`: Lookahead helper to detect function calls

---

## Classes Based from Demo Programs
- Add here


### Original Implementations
- 30-state DFA specifically designed for SimC requirements (complete implementation in `create_scanner_dfa()`)
- Complete SimC grammar implementation for all language constructs

---

## Distribution of Work

| Team Member | Primary Responsibilities | Contributions |
|-------------|-------------------------|---------------|
| **Nics** | Scanner Implementation | 30-state DFA design via `create_scanner_dfa()`, State class implementation, token recognition logic including checkpoint/pushback mechanism, comment handling through ignore states, keyword identification, error detection, test case development (p01-p10.smc) |
| **Neil** | Parser Implementation | Recursive descent parser with all grammar rules, AST node structure, operator precedence through `parse_relational()`, `parse_term()`, `parse_factor()`, `parse_primary()` hierarchy, syntax error reporting via ParserError, JSON AST output. |
| **Jenica** | Integration & Code Generation | End-to-end integration of scanner, parser, and IGC in c2tac.py, code generator architecture, main driver program coordination |

---

## File Contents

- **c2tac.py**: Main translator program integrating scanner, parser, and intermediate code generator
- **p01.smc - p10.smc**: Ten test input files covering various SimC language features
- **p01.tac - p10.tac**: Corresponding TAC output files for each test case

### Test Case Coverage
The 10 test cases demonstrate:
- p01.smc - Simple arithmetic operations
- p02.smc - If-else conditionals with iread()
- p03.smc - While loop
- p04.smc - Simple function with parameters
- p05.smc - Nested if-else statements
- p06.smc - Multiple functions calling each other
- p07.smc - All relational operators
- p08.smc - Complex expressions with precedence
- p09.smc - Nested while loops
- p10.smc - Comprehensive test with isEven and sumRange functions

---

## Challenges Encountered and Solutions

### Challenge 1: <Name>
**Problem**: Insert Problem

**Solution**: Insert Solution

---

## How to Run

```bash
python3 c2tac.py prog.smc
```

This command:
1. Reads the SimC source file `prog.smc`
2. Tokenizes the source code (Scanner phase)
3. Parses tokens and builds AST (Parser phase)
4. Generates Three-Address Code (Code Generator phase)
5. Outputs final TAC to `prog.tac`

**File Naming Convention**: Input `<file_name>.smc` → Output `<file_name>.tac`

**Example**:

```bash
python3 c2tac.py p01.smc  # Generates p01.tac
```
