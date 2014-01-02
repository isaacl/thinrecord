import subprocess
import sys
import timeit

thin_types = [
    ('collections', 'namedtuple'),
    ('thinrecord', 'thinrecord')
]

print 'Performance (average us per run):'
for t in thin_types:
  print t[1], timeit.timeit('r(1); r(1).a; r.__dict__', 'from %s import %s as R; r=R("R", "a")' % t)

print 'object', timeit.timeit('r(1); r(1).a; r.__dict__', 'class r(object):\n  def __init__(self, a):\n    self.a = a')

print '\bMemory usage: 10^6 objects in MB'
for args in thin_types + [['object']]:
  print args[-1], subprocess.check_output(['python', '_memory_tester.py'] + list(args)),
