ip = 1
mem[23] = 10
mem[24] = 20
mem[25] = 10
mem[26] = mem[23] >= mem[24]
if mem[26]: ip = 7
print(1)
mem[26] = mem[24] <= mem[23]
if mem[26]: ip = 10
print(2)
mem[26] = mem[23] > mem[25]
if mem[26]: ip = 13
print(3)
mem[26] = mem[24] < mem[23]
if mem[26]: ip = 16
print(4)
mem[26] = mem[23] != mem[25]
if mem[26]: ip = 19
print(5)
mem[26] = mem[23] == mem[24]
if mem[26]: ip = 22
print(6)
halt
