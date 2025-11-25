ip = 1
mem[16] = 0
mem[17] = 0
mem[18] = mem[16] >= 5
if mem[18]: ip = 13
mem[18] = mem[17]
mem[19] = mem[16]
mem[18] = mem[18] + mem[19]
mem[17] = mem[18]
mem[18] = mem[16]
mem[18] = mem[18] + 1
mem[16] = mem[18]
ip = 3
print(mem[17])
print(mem[16])
halt
