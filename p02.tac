ip = 1
mem[11] = iread()
mem[12] = mem[11] <= 0
if mem[12]: ip = 6
print(1)
ip = 7
print(0)
mem[12] = mem[11] != 5
if mem[12]: ip = 10
print(100)
halt
