ip = 1
mem[37] = 5
mem[38] = 3
mem[39] = 2
mem[41] = mem[38]
mem[42] = mem[39]
mem[41] = mem[41] * mem[42]
mem[42] = mem[37]
mem[42] = mem[42] + mem[41]
mem[40] = mem[42]
print(mem[40])
mem[42] = mem[37]
mem[41] = mem[38]
mem[42] = mem[42] + mem[41]
mem[41] = mem[39]
mem[42] = mem[42] * mem[41]
mem[43] = mem[42]
print(mem[43])
mem[42] = mem[37]
mem[41] = mem[38]
mem[42] = mem[42] % mem[41]
mem[44] = mem[42]
print(mem[44])
mem[42] = mem[37]
mem[41] = mem[38]
mem[42] = mem[42] * mem[41]
mem[41] = mem[39]
mem[46] = mem[39]
mem[41] = mem[41] / mem[46]
mem[42] = mem[42] + mem[41]
mem[41] = mem[38]
mem[46] = mem[39]
mem[41] = mem[41] % mem[46]
mem[42] = mem[42] - mem[41]
mem[45] = mem[42]
print(mem[45])
halt
