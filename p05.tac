ip = 1
mem[17] = iread()
mem[18] = mem[17] < 0
if mem[18]: ip = 10
mem[18] = mem[17] > 10
if mem[18]: ip = 8
print(1)
ip = 9
print(2)
ip = 16
mem[18] = 0 - 10
mem[19] = mem[17] < mem[18]
if mem[19]: ip = 15
print(3)
ip = 16
print(4)
halt
