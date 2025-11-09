# SimC Scanner DFA (Deterministic Finite Automaton)


## HOW AND WHAT TO RUN

Use ```c2tac.py``` to have the combined scanner and parser code. Individual scanner and parser programs have already been merged there and ```main.py``` will not be executed anymore (based on machine problem specs).


```bash
python c2tac.py prog.smc
```

### Main Program Flow
1. Program reads ```prog.smc``` or other input file with ```.smc``` extension.
2. Scanner tokenizes the program. Output will be saved to ```scanner_output.txt``` (Optional, can be removed in final implementation)
3. Parser takes in tokens from scanner output. Output will be saved to ```parser_output.txt``` (Optional, can be removed in final implementation)
4. Main ICG program.

## State Diagram Overview

The SimC scanner uses a DFA with 30 states (q0 to q29).

## States and Their Purposes

### Start State
- **q0**: Start state - initial state for token recognition

### Delimiter States (Direct Recognition)
- **q1**: LPAREN - '('
- **q2**: RPAREN - ')'
- **q3**: LBRACE - '{'
- **q4**: RBRACE - '}'
- **q5**: SEMI - ';'
- **q6**: COMMA - ','

### Arithmetic Operator States
- **q7**: PLUS - '+'
- **q8**: MINUS - '-'
- **q9**: MUL - '*'
- **q10**: Division checkpoint (checks for comment)
- **q11**: MOD - '%'

### Comparison and Assignment States
- **q12**: Assignment/Equality checkpoint (= or ==)
- **q13**: EQ - '=='
- **q14**: Not checkpoint (!)
- **q15**: NEQ - '!='
- **q16**: Less than checkpoint (< or <=)
- **q17**: LE - '<='
- **q18**: Greater than checkpoint (> or >=)
- **q19**: GE - '>='

### Literal and Identifier States
- **q20**: Integer accumulation
- **q21**: Integer pushback
- **q22**: Identifier/Keyword accumulation
- **q23**: Identifier/Keyword pushback

### Special States
- **q24**: EOF - End of file
- **q25**: ERROR - Illegal character
- **q26**: COMMENT - Comment ignore state
- **q27**: DIV pushback - '/'
- **q28**: ASSIGN pushback - '='
- **q29**: Comparison pushback - '<' or '>'

## Transition Table

```
State | Input        | Next State | Action
------|-------------|------------|--------
q0    | whitespace  | q0         | Skip
q0    | \n          | q0         | Skip, increment line
q0    | (           | q1         | Create token
q0    | )           | q2         | Create token
q0    | {           | q3         | Create token
q0    | }           | q4         | Create token
q0    | ;           | q5         | Create token
q0    | ,           | q6         | Create token
q0    | +           | q7         | Create token
q0    | -           | q8         | Create token
q0    | *           | q9         | Create token
q0    | /           | q10        | Check ahead
q0    | %           | q11        | Create token
q0    | =           | q12        | Check ahead
q0    | !           | q14        | Check ahead
q0    | <           | q16        | Check ahead
q0    | >           | q18        | Check ahead
q0    | digit       | q20        | Accumulate
q0    | letter/_    | q22        | Accumulate
q0    | EOF         | q24        | End
q0    | other       | q25        | Error

q10   | /           | q26        | Enter comment
q10   | other       | q27        | Division

q12   | =           | q13        | Equality
q12   | other       | q28        | Assignment

q14   | =           | q15        | Not equal
q14   | other       | q25        | Error

q16   | =           | q17        | Less than or equal
q16   | other       | q29        | Less than

q18   | =           | q19        | Greater than or equal
q18   | other       | q29        | Greater than

q20   | digit       | q20        | Continue accumulating
q20   | other       | q21        | Pushback, create INT

q22   | letter/digit/_ | q22     | Continue accumulating
q22   | other       | q23        | Pushback, check keyword

q26   | \n          | q0         | End comment
q26   | EOF         | q0         | End comment
q26   | other       | q26        | Stay in comment
```

## Token Recognition Process

1. **Single Character Tokens**: Direct transition from q0 to end state
   - Examples: (, ), {, }, ;, ,, +, -, *, %

2. **Two Character Operators**: Use checkpoint states
   - `==`: q0 → q12 → q13
   - `!=`: q0 → q14 → q15
   - `<=`: q0 → q16 → q17
   - `>=`: q0 → q18 → q19
   - `//`: q0 → q10 → q26 (comment)

3. **Integers**: Accumulate digits
   - q0 → q20 → q20* → q21 (pushback)

4. **Identifiers/Keywords**: Accumulate letters/digits/_
   - q0 → q22 → q22* → q23 (pushback, then check if keyword)

5. **Comments**: Special ignore state
   - q0 → q10 → q26 → (consume until \n) → q0

## Keywords Recognition

After recognizing an identifier (at q23), check against keyword list:
- `if` → IF
- `else` → ELSE
- `while` → WHILE
- `return` → RETURN
- `print` → PRINT
- `iread` → IREAD

If not a keyword, token type remains ID.

## Implementation Details

### Checkpoint States
States q10, q12, q16, q18, q20, q22 are checkpoint states that save the current position for potential pushback.

### Pushback States
States q21, q23, q27, q28, q29 push back one character to the input stream before creating the token.

### Ignore State
State q26 consumes input without creating tokens (used for comments).

### Error State
State q25 reports lexical errors with the current line number.