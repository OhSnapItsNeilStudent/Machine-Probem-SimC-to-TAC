ip = 47
sp = sp - 1
mem[sp] = bp
bp = sp
sp = sp - 1
r1 = mem[2 + bp]
r1 = r1 % 2
mem[-1 + bp] = r1
r1 = mem[-1 + bp] != 0
if r1: ip = 16
ac = 1
sp = sp + 2
r1 = mem[1 + bp]
bp = mem[bp]
ip = r1
ip = 21
ac = 0
sp = sp + 2
r1 = mem[1 + bp]
bp = mem[bp]
ip = r1
ac = 0
sp = sp + 2
r1 = mem[1 + bp]
bp = mem[bp]
ip = r1
sp = sp - 1
mem[sp] = bp
bp = sp
sp = sp - 2
mem[-2 + bp] = 0
mem[-1 + bp] = mem[2 + bp]
r1 = mem[-1 + bp] > mem[3 + bp]
if r1: ip = 42
r1 = mem[-2 + bp]
r2 = mem[-1 + bp]
r1 = r1 + r2
mem[-2 + bp] = r1
r1 = mem[-1 + bp]
r1 = r1 + 1
mem[-1 + bp] = r1
ip = 32
ac = mem[-2 + bp]
sp = sp + 3
r1 = mem[1 + bp]
bp = mem[bp]
ip = r1
mem[75] = iread()
mem[76] = mem[75] <= 0
if mem[76]: ip = 73
sp = sp - 1
mem[sp] = mem[75]
sp = sp - 1
mem[sp] = 55
ip = 1
mem[77] = ac
sp = sp + 2
mem[76] = mem[77] != 1
if mem[76]: ip = 61
print(100)
ip = 62
print(200)
sp = sp - 1
mem[sp] = 1
sp = sp - 1
mem[sp] = mem[75]
sp = sp - 1
mem[sp] = 69
ip = 26
mem[78] = ac
sp = sp + 3
print(mem[78])
ip = 74
print(0)
halt
