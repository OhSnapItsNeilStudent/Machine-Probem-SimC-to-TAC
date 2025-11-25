ip = 1
mem[22] = 0
mem[23] = 0
mem[24] = mem[22] >= 3
if mem[24]: ip = 19
mem[25] = 0
mem[24] = mem[25] >= 2
if mem[24]: ip = 15
mem[24] = mem[23]
mem[24] = mem[24] + 1
mem[23] = mem[24]
mem[24] = mem[25]
mem[24] = mem[24] + 1
mem[25] = mem[24]
ip = 6
mem[24] = mem[22]
mem[24] = mem[24] + 1
mem[22] = mem[24]
ip = 3
print(mem[23])
print(mem[22])
halt
