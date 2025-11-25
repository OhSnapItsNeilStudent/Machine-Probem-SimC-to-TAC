'''
===========================================================
SimC Intermediate Code Generator (ICG)
===========================================================

This intermediate code generator takes an Abstract Syntax 
Tree (AST), which is formatted like a JSON file, and produces 
the corresponding Three-Address Code (TAC) instructions.

'''

import re

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
        
        # For UnaryOp
        if e_type == 'UnaryOp':
            op = e['op']
            operand = self.expr(e['operand'], in_function, params_map, locals_map)

            # Only - sign is considered a valid unary operator
            if op == '-': 
                r = self.new_temp(in_function)
                self.emit(f'{r} = {op} {operand}')
                return r
            else:
                raise Exception('Unknown unary operator: ' + op)

        # For function calls
        if e_type == 'FuncCall':
            # iread case
            if e['name'] == 'iread':
                r = self.new_temp(in_function)
                self.emit(f'{r} = iread()')
                return r
            
            # Otherwise, 
            #   push args from right-to-left (so that the leftmost arg will 
            #   be at position bp+2, following the parameters mapping), 
            #   push return address, go to function (ip = func_label)
            else:
                # Setup arguments
                args_list = e.get('args', [])
                for arg in reversed(args_list):
                    op = self.expr(arg, in_function, params_map, locals_map)
                    self.emit("sp = sp - 1")
                    self.emit(f"mem[sp] = {op}")
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
