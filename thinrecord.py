"""A lightweight mutable container factory.

This is a lightweight struct that can be used when working with very
large numbers of objects. thinrecord instances do not carry around a
dict, and cannot define their own attributes. You can, however, add
methods to the class object and, with caveats, subclass the class to
add additional methods: http://stackoverflow.com/a/1816648/3109503
tl;dr subclasses must use __slots__, don't repeat variable names.

Based on collections.namedtuple, with inspiration and tests from:
  https://bitbucket.org/ericvsmith/recordtype
"""

__all__ = ['thinrecord']
__author__ = "Isaac Levy <ilevy@chromium.org>"
__version__ = "0.0.1"

import six as _six
import sys as _sys
from keyword import iskeyword as _iskeyword

NO_DEFAULT = object()

def _check_name(name):
  err_id = 'Type names and field names'
  if not isinstance(name, _six.string_types):
    raise ValueError('{} must be a string (type: {!r}): '
                     '{!r}'.format(err_id, type(name), name))
  if not name:
    raise ValueError('{} cannot be empty.'.format(err_id))
  if not all(c.isalnum() or c=='_' for c in name):
    raise ValueError('{} can only contain alphanumerics and underscores: '
                     '{!r}'.format(err_id, name))
  if _iskeyword(name):
    raise ValueError('{} cannot be a keyword: {!r}'.format(err_id, name))
  if name[0].isdigit():
    raise ValueError('{} cannot start with a number: '
                     '{!r}'.format(err_id, name))


def thinrecord(typename, fields, default=NO_DEFAULT,
                ignore_extra_kwargs=True):
  # field_names must be a string or an iterable, consisting of fieldname
  # strings or 2-tuples. Each 2-tuple is of the form (fieldname,
  # default).
  _check_name(typename)
  if isinstance(fields, _six.string_types):
    fields = fields.replace(',', ' ').split()
  field_defaults, field_names, fields_seen = {}, [], set()

  for field in fields:
    if isinstance(field, _six.string_types):
      field_name = field
      cur_default = default
    else:
      try:
        field_name, cur_default = field
      except TypeError:
        raise ValueError('Field must be string or iterable: {!r}'.format(field))

    _check_name(field_name)
    if field_name in ('_fields', '_items', '_update'):
      raise ValueError('field name conflicts with helper method: '
                       '{!r}'.format(field_name))
    if field_name in fields_seen:
      raise ValueError('Duplicate field name: {}'.format(field_name))
    fields_seen.add(field_name)
    field_names.append(field_name)
    if cur_default is not NO_DEFAULT:
      field_defaults[field_name] = cur_default

  # Create and fill-in the class template.
  default_name_prefix = '_default_val_for_'
  argtxt = ', '.join(field_names)  # "x, y, ..."
  quoted_argtxt = ', '.join("'{}'".format(f) for f in field_names)
  if len(field_names) == 1:
    quoted_argtxt += ','
  initargs = []
  for f_name in field_names:
    if f_name in field_defaults:
      initargs.append('{}={}'.format(f_name, default_name_prefix + f_name))
    else:
      initargs.append(f_name)
  if ignore_extra_kwargs:
    initargs.append('**_unused_kwargs')
  initargs = ', '.join(initargs)  # "x, y=_default_val_for_y, **_unused_kwargs"
  if field_names:
    initbody = '\n    '.join('self.{0} = {0}'.format(f) for f in field_names)
  else:
    initbody = 'pass'
  reprtxt = ', '.join('{}={{!r}}'.format(f) for f in field_names)
  template = '''
try:
  from collections import OrderedDict as _MaybeOrderedDict
except ImportError:
  _MaybeOrderedDict = dict

try:
  from __builtins__ import property as _property, list as _list, tuple as _tuple
except ImportError:
  _property, _tuple, _list = property, tuple, list


class {typename}(object):
  '{typename}({argtxt})'

  __slots__ = ({quoted_argtxt})

  _fields = __slots__

  def __init__(self, {initargs}):
    {initbody}

  def __len__(self):
    return {num_fields}

  def __iter__(self):
    """Iterate through values."""
    for var in self._fields:
      yield getattr(self, var)

  def _items(self):
    """A fresh list of pairs (key, val)."""
    return zip(self._fields, self)

  def _update(self, **kwargs):
    for k, v in kwargs:
      setattr(self, k, v)

  @_property
  def __dict__(self):
    return _MaybeOrderedDict(self._items())

  def __repr__(self):
    return '{typename}(' + '{reprtxt}'.format(*self) + ')'

  def __eq__(self, other):
    return isinstance(other, self.__class__) and _tuple(self) == _tuple(other)

  def __ne__(self, other):
    return not self.__eq__(other)

  def __lt__(self, other):
    if isinstance(other, self.__class__):
      return _tuple(self) < _tuple(other)
    raise TypeError('Unorderable types ({typename}, {{!s}})'.format(
                    other.__class__.__name__))

  def __ge__(self, other):
    return not self.__lt__(other)

  def __le__(self, other):
    if isinstance(other, self.__class__):
      return _tuple(self) <= _tuple(other)
    raise TypeError('Unorderable types ({typename}, {{!s}})'.format(
                    other.__class__.__name__))

  def __gt__(self, other):
    return not self.__le__(other)

  def __hash__(self):
    raise TypeError('Unhashable type: {typename}')

  def __getstate__(self):
    return _tuple(self)

  def __setstate__(self, state):
    self.__init__(*state)

  def __getitem__(self, idx):
    return _tuple(self)[idx]

  def __setitem__(self, idx, value):
    if isinstance(idx, slice):
      raise TypeError('{typename} does not support assignment by slice.')
    else:
      setattr(self, self._fields[idx], value)
'''.format(
    typename=typename,
    argtxt=argtxt,
    quoted_argtxt=quoted_argtxt,
    initargs=initargs,
    initbody=initbody,
    reprtxt=reprtxt,
    num_fields=len(field_names)) 

  # Execute the template string in a temporary namespace.
  namespace = {'__name__': 'thinrecord_' + typename}
  for name, default in _six.iteritems(field_defaults):
    namespace[default_name_prefix + name] = default
  _six.exec_(template, namespace)

  cls = namespace[typename]
  cls._source = template

  # For pickling to work, the __module__ variable needs to be set to
  #  the frame where the named tuple is created.  Bypass this step in
  #  enviroments where sys._getframe is not defined (Jython for
  #  example).
  if hasattr(_sys, '_getframe') and _sys.platform != 'cli':
    cls.__module__ = _sys._getframe(1).f_globals.get('__name__', '__main__')
  return cls
