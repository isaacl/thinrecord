import sys
import resource
if sys.argv[1] != 'object':
  t = getattr(__import__(sys.argv[1], globals(), locals(), [sys.argv[2]], -1), sys.argv[2])
  T_cls = t('B', ['b'])
else:
  class B(object):
    def __init__(self, b):
      self.b = b
  T_cls= B
mem = lambda : resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
start = mem() 
L = [T_cls(i) for i in xrange(10**6)]
print (mem() - start + 0.) / 2**20
  
