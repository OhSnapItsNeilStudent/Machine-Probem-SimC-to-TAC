# README - SimC to Three-Address Code Translator

### Nics De Vega (ID: 211951)
### Christianneil Emmanuel Ocampo (ID: 214293)
### Jenica Alea Vizmanos (ID: 216351)

#### November 25, 2025
#### CSCI 202 WX2

#### Sources: 
- https://www.w3schools.com/python/python_regex.asp
- https://docs.python.org/3/library/re.html


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

### Phase 3: Intermediate Code Generation
- Converts the AST into Three-Address Code (TAC) instructions suitable for execution using `tsim.py`.
- **Symbol Table Management**
  - Tracks **global variables**, **temporary globals**, function **parameters**, and local variables.
  - Global variables are stored in memory after TAC instructions and referenced via placeholders like `mem[GLOBAL_x]`.
  - Local variables and function parameters are mapped relative to `bp` (base pointer) for stack-based addressing.
- **Temporary Storage**
  - **Functions**: Uses 16 general-purpose registers (`r1`–`r16`) in LIFO order for intermediate results.
  - **Main program**: Uses memory-based temporary globals for storing intermediate expression results.
  - Temporaries are allocated and freed systematically to avoid memory/register conflicts.
- **Expression Handling**
  - Handles constants, variables, unary/binary operations, and function calls.
  - Binary operations uses the location of the left operand to store the result. 
  - Right-hand side constants in binary operations are used inline when possible.
  - Negation is the only valid unary operation that would create a temporary storage for the result.
- **Control Flow Translation**
  - `if` and `while` statements are translated into conditional TAC jumps.
    - For `if` statements, it's processed such that there's at least 1 valid statement in the THEN block. 
  - Relational operators (for conditional statements) are inverted to simplify jump logic (`>` → `<=`, `==` → `!=`, etc.). 
  - Generates labels for ELSE, ENDIF, WHILESTART, WHILEBODY, and ENDWHILE, with proper backpatching.
- **Function Calls**
  - Push arguments in **right-to-left order** onto the stack so that it matches the order of paramter mapping where the nearest parameter to `bp` is the leftmost parameter. 
  - Save return address, jump to function label.
  - On return, store result in `ac` (accumulator) and clean up stack.
  - Handles `iread()` separately as a special built-in function.
- **Backpatching and Finalization**
  - Labels and `GLOBAL_x` placeholders are resolved to numeric instruction indices or memory addresses after TAC emission.
  - Global variables are assigned sequential memory addresses immediately following TAC instructions.
  - Final TAC is written to file with all placeholders replaced by concrete numeric locations.

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

### 4. IntermediateCodeGenerator Class
**Purpose**: Generates Three-Address Code (TAC) from the Abstract Syntax Tree (AST) produced by the parser. It handles both the main program and user-defined functions, manages registers, global memory, and control flow.

**Key Attributes**:
- `ast`: Abstract Syntax Tree (AST) from the parser  
- `instructions`: List of emitted TAC instructions  
- `labels`: Maps label names to instruction indices for backpatching  
- `globals_list` / `globals_map`: Tracks global variable names and their assigned memory indices  
- `temp_globals` / `free_temp_globals`: Pool of temporary globals for main program expression evaluation  
- `regs` / `free_regs`: Pool of 16 general-purpose registers for function computations  
- `label_count`, `return_count`, `global_temp_count`: Counters for generating unique labels and temporary variables  
- `main_label`: Label marking for the start of the main program  

**Key Methods**:
- **Emit Instructions**
  - `emit(code)`: Append a TAC instruction and returns its index  
  - `emit_label(name)`: Record a label as mapping to the next instruction index
- **Globals & Temporary Variables**
  - `add_global(name)`: Register a new global variable  
  - `get_global_addr(name)`: Get memory placeholder `mem[GLOBAL_{name}]`  
  - `new_global_temp_addr()`: Allocate a temporary global memory slot  
  - `free_global_temp(temp)`: Free a temporary global to reuse later on
- **Register Management**
  - `alloc_reg()`: Allocate a free register 
  - `free_reg(r)`: Return a register to the pool, effectively marking it as a free to use register 
- **Expression Handling**
  - `expr(e, in_function, params_map, locals_map, target_address='')`: Recursively generate TAC and return memory/register/constants/none for specific expressions. It also includes handling temporary registers and memory allocation.  
- **Statement Handling**
  - `invert_op(op)`: Inverts relational operators for generating conditional jumps.  
  - `stmt(s, in_function, params_map, locals_map)`: Generates TAC for assignments, print statements, if-else blocks, while loops, and return statements.  
- **Function Processing**
  - `scan_locals(params, body)`: Identify all local variables that need stack allocation  
  - `func_body(body, in_function, params_map, locals_map)`: Process statements in a function body  
  - `func(f)`: Generate TAC for a function, including stack frame setup, local allocation, parameter mapping, and default return handling  
- **Program Entry & Finalization**
  - `start_program()`: Processes functions first, then main program statements, and a final `halt` instruction  
  - `finalize(out_filename)`: Performs backpatching to replace labels and `GLOBAL_` placeholders with numeric memory locations, and writes the final TAC to a `.tac` file  

---

## Classes Based from Demo Programs
- We mainly took inspiration from the **CSCI 202 - L10 - Demo.ipynb** in terms of program structure (especially in doing the IntermediateCodeGenerator Class), such as in the order of processing statements or what to consider when a statement is processed. We also used this to understand how to break-down the problem into modular functions that work together to create the TAC.

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

### Challenge 1: Managing Lookahead and Pushback in the 30-State DFA  
**Problem:**  
Designing the scanner required handling operators that can be one- or two-character tokens (e.g., `=`, `==`, `<`, `<=`, `>`, `>=`, `!`, `!=`, `/`, `//`). Without lookahead, the DFA would prematurely finalize tokens or misinterpret multi-character operators. Implementing this cleanly without breaking the DFA flow was difficult.

**Solution:**  
We added *checkpoint states* with a pushback mechanism. When the DFA reaches a checkpoint, it examines the next input character:  
- If it forms a valid 2-character operator, the state transitions appropriately.  
- If not, the scanner pushes the character back and finalizes the 1-character token.  

This produced a robust scanning system where states can safely “peek” into the next character without losing input or creating ambiguous transitions.

### Challenge 2: Differentiating Keywords and Identifiers  
**Problem:**  
Identifiers and keywords share the same lexical structure (alphabetic sequences). The scanner's DFA recognized them using the same state, which initially made it difficult to label tokens correctly (e.g., deciding if `while` is the WHILE token or just an identifier).

**Solution:**  
All alphabetic sequences were first tokenized as ID tokens. After reaching a final state, the scanner checks the lexeme against a keyword dictionary. If it matches one of the SimC  reserved words, the token type is replaced with the correct keyword token (WHILE, IF, PRINT, RETURN, etc.). Otherwise, it remains an ID. This approach keeps the DFA simple while preserving full keyword recognition.

### Challenge 3: Enforcing Operator Precedence in Recursive Descent  
**Problem:**  
Recursive descent parsing becomes complex when operators have multiple layers of precedence (+ vs * vs relational operators). If not designed carefully, the parser may incorrectly associate expressions (e.g., parsing `a + b * c` as `(a + b) * c`).

**Solution:**  
We implemented a structured precedence hierarchy:

- `parse_relational()`  
- `parse_term()`  
- `parse_factor()`  
- `parse_primary()`

Each level calls the next lower-precedence function.  
This ensured correct left associativity and strict operator precedence following the SimC grammar, producing accurate AST structures for the code generator.

### Challenge 4: Detecting Function Calls vs Variable References  
**Problem:**  
When parsing an identifier, the parser must decide whether it is:  
- A plain variable (`x`)  
- A function call (`x(a, b)`)  

But lookahead is required because both begin with an identifier.

**Solution:**  
We implemented a lookahead helper `_is_func_call()`, which checks if the next token after an ID is a left parenthesis.  
- If yes → parse as a function call.  
- If no → parse as a variable.

This eliminated ambiguity without requiring token backtracking.

### Challenge 5: Allocating and De-allocating Temporary Storage (registers and global variables)
**Problem:**  
We struggled with identifying the underlying rules for when to allocate and de-allocate temporary storage such as the registers and temporary variables, and initially understanding on when to use registers or temporary variables.

**Solution:**  
We set a common rule, following the sample output, where registers are only used inside functions, and temporary variables are used in the main program. 

Then, we looked at the patterns wherein we found that binary operations in expressions generally use the left operand as the location of the result of the operation. We standardized this so that we don't need to always allocate temporary storage for the results of binary operations. We also optimized the code so that the righ operands do not needlessly consume temporary storage if they are just integers or are already allocated to a temporary storage. 

For the conditional statements in `if` statement and `while` loop, we always allocate new temporary variable or register (depending on where it's located) to store the result of the boolean expression. We then de-allocate those immediately after setting the condition for jumping instructions. In this way, the registers or temporary variables could be used again in the subsequent instructions. 

### Challenge 6: Coordinating Scanner–Parser–Codegen Interaction  
**Problem:**  
Although the scanner, parser, and code generator were implemented as separate components, they must behave as a unified pipeline. Early on, small inconsistencies caused major failures:  
- Scanner token types didn’t always match what the parser expected  
- Line numbering inconsistencies made debugging syntax errors hard  
- Lookahead semantics (checkpoint and pushback states) sometimes produced unexpected tokens  
- AST nodes varied in structure, making the code generator unable to rely on consistent fields  

These mismatches caused the parser to reject valid input, skip tokens, or enter infinite loops, and the code generator could not reliably map AST nodes to TAC instructions.

**Solution:**  
We standardized token naming, keyword mapping, and delimiter recognition in the scanner so the parser always receives a clean, predictable token stream. The parser’s `peek()`, `advance()`, and `match()` logic was adjusted to gracefully handle EOF tokens, invalid sequences, and lookahead-driven decisions (e.g., distinguishing identifiers vs. function calls).  

Finally, the AST structure was normalized across all construct types—expressions, statements, function definitions—allowing the intermediate code generator to traverse the AST without special-case handling.  

By aligning all three components—Scanner → Parser → Code Generator—we achieved a stable and cohesive pipeline where each phase produces output in exactly the format expected by the next.

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
