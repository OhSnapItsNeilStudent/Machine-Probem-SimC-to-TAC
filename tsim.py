#!/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
#
# filename: tsim.py
# asioson@ateneo.edu
# this is an implementation of a simulator of a very simple
# three address code. the virtual machine uses the following
# global variables:
#    mem : the array representing the memory
#    sp  : stack pointer (set to the size of mem)
#    bp  : base pointer
#    ip  : instruction pointer
#    ac  : accumulator
# as such the names mem, sp, bp, ip, ac are reserved words
# and cannot be used as variable names.  names that matches
# the regular expression t[0-9][0-9]* are also reserved
# words ans will be used as global temporary variable names.

import sys
import fileinput

def iread():
  return int(input())

class VM:
  def __init__(self, max = 100):
    global mem
    self.MAX = max
    mem = self.MAX * [None]
    self.csize = 0
  
  def load(self, tac):
    global mem
    if self.csize < self.MAX:
      mem[self.csize] = tac
      self.csize += 1
    else:
      print('code runoff', file=sys.stderr)

  def show(self):
    global mem
    for i in range(self.csize):
      print(i,':',mem[i])

  def run(self):
    global mem, ip, sp, bp, ac, r1, r2, r3, r4, r5, r6, r7, iread
    ip, sp, bp, ac = 0, self.MAX, 0, 0
    r1, r2, r3, r4, r5, r6, r7 = 0, 0, 0, 0, 0, 0, 0
    while True:
      cmd = mem[ip].split('#')[0].strip()
      if cmd == 'halt': break
      old_ip = ip
      exec(cmd, globals())
      if old_ip == ip:
        ip += 1


def main():
  doRun = True
  if (len(sys.argv) < 2) or (len(sys.argv) > 3):
    print('usage: '+sys.argv[0]+' file.tac [-s]')
  else:
    filename = sys.argv[1]
    if len(sys.argv) == 3:
      doRun = (sys.argv[2] != '-s')
    vm = VM(1024)
    try:
      for line in fileinput.input(files=filename):
        vm.load(line.strip())
      if doRun:
        vm.run()
      else:
        vm.show()
    except:
      print('(stopped)', ip, mem[ip], file=sys.stderr)
      print('ip',ip,'bp',bp,'sp',sp,'ac',ac,'', end='')
      print('r1',r1,'r2',r2,'r3',r3,'r4',r4,'r5',r5,'r6',r6,'r7',r7)
      print('mem[sp:]',mem[sp:])
      print('error: cannot run '+filename, file=sys.stderr)

if __name__ == "__main__":
  main()
