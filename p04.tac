ip = 14
sp = sp - 1
mem[sp] = bp
bp = sp
sp = sp - 1
r1 = mem[2 + bp]
r2 = mem[3 + bp]
r1 = r1 + r2
mem[-1 + bp] = r1
ac = mem[-1 + bp]
sp = sp + 2
r1 = mem[1 + bp]
bp = mem[bp]
ip = r1
mem[27] = 15
mem[28] = 25
sp = sp - 1
mem[sp] = mem[27]
sp = sp - 1
mem[sp] = mem[28]
sp = sp - 1
mem[sp] = 23
ip = 1
mem[29] = ac
sp = sp + 3
print(mem[29])
halt
