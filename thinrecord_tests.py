from thinrecord import thinrecord, NO_DEFAULT
import unittest
import pickle


# Pickle is picky: class must be top-level and name must match variable.
PickleRecord = thinrecord('PickleRecord', 'x y z')
R_MIXER = lambda *args, **kwargs: thinrecord('P', *args, **kwargs)
class thinrecord_unittests(unittest.TestCase):

  def test_base_methods(self):
    p1 = R_MIXER('x y')(10, 20)
    self.assertEqual(p1.x, 10)
    self.assertEqual(p1[0], 10)
    self.assertEqual(vars(p1), {'x': 10, 'y': 20})
    self.assertEqual(p1._items(), [('x', 10), ('y', 20)])
    self.assertEqual(len(p1), 2)

    # Verify class preserves ordering
    vs = 'djvexlbuicagqmnozhyftswrpk'
    vals = [(c, 10) for c in vs]
    self.assertEqual(thinrecord('P', list(vs))(**dict(vals))._items(), vals)

    p = R_MIXER('P x')(1, '2')
    self.assertEqual(repr(p), "P(P=1, x='2')")
    self.assertEqual(str(p), "P(P=1, x='2')")
    self.assertTrue(getattr(p, '_source', None))
    self.assertEqual(p._fields, ('P', 'x'))

    pr = PickleRecord(10, 20, 30)
    for protocol in -1, 0, 1, 2:
      self.assertEqual(pr, pickle.loads(pickle.dumps(pr, protocol)))

  def test_parsing(self):
    p1 = R_MIXER('x,y')(10, 20)
    self.assertEqual(list(p1), [10, 20])

    p2 = R_MIXER(['x', 'y'])(10, 20)
    self.assertEqual(list(p2), [10, 20])

    p3 = R_MIXER(['x_', 'y1'])(10, 20)
    self.assertEqual(list(p3), [10, 20])

    self.assertEqual(list(R_MIXER([])()), [])

  def test_equality(self):
    P = R_MIXER('x y')
    p1 = P(10, 20)
    p2 = P(10, 20)
    p3 = R_MIXER('x y')(10, 20)
    self.assertNotEqual(p1, P(10, 30))
    self.assertEqual(p1, p1)
    self.assertEqual(p1, p2)
    self.assertNotEqual(p1, p3)

    # Verify eq and ne are consistent.
    self.assertNotEqual(p1 == p1, p1 != p1)
    self.assertNotEqual(p1 == p2, p1 != p2)
    self.assertNotEqual(p1 == p3, p1 != p3)

  def test_bad_names(self):
    self.assertRaises(ValueError, thinrecord, 'P*', '')
    self.assertRaises(ValueError, R_MIXER, '#')
    self.assertRaises(ValueError, R_MIXER, '1')
    self.assertRaises(ValueError, R_MIXER, 'x y x')
    self.assertRaises(ValueError, R_MIXER, 'for')
    self.assertRaises(ValueError, R_MIXER, '_fields')
    self.assertRaises(ValueError, R_MIXER, [''])
    self.assertRaises(ValueError, thinrecord, '', 'x')
    self.assertRaises(ValueError, R_MIXER, [('x', 3, 4)])
    self.assertRaises(ValueError, R_MIXER, [('x',)])
    self.assertRaises(ValueError, thinrecord, '', [None])

    self.assertFalse(thinrecord('_', '')())
  def test_defaults(self):
    self.assertEqual(list(R_MIXER([('x', 3)])()), [3])
    self.assertEqual(list(R_MIXER('x', default=3)()), [3])
    self.assertEqual(list(R_MIXER('x', default=None)()), [None])
    self.assertRaises(TypeError, R_MIXER('x'))
    self.assertEqual(list(R_MIXER([('x', 2), 'y'], default=3)(4)), [4, 3])
    self.assertEqual(list(R_MIXER([('x', 2)], default=3)()), [2])
    self.assertEqual(list(R_MIXER('x', default=3)(4)), [4])
    self.assertEqual(list(R_MIXER([('x', 2)], default=3)(4)), [4])
    self.assertRaises(TypeError, R_MIXER([('x', NO_DEFAULT)], default=3))
    self.assertEqual(list(R_MIXER(['x', ('y', 10), 'z'], -1)(z=0)), [-1, 10, 0])

  def test_extra_args(self):
    self.assertEqual(list(R_MIXER('x')(x=3, y=4)), [3])
    self.assertRaises(TypeError, R_MIXER('', ignore_extra_kwargs=False), y=4)


unittest.main()
