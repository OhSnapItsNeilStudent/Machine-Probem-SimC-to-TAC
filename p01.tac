ip = 1
mem[14] = 10
mem[15] = 20
mem[17] = mem[14]
mem[18] = mem[15]
mem[17] = mem[17] + mem[18]
mem[16] = mem[17]
print(mem[16])
mem[17] = mem[16]
mem[17] = mem[17] * 2
mem[17] = mem[17] - 5
mem[19] = mem[17]
print(mem[19])
halt
