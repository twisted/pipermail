#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sucking out and dumping information out of the sea of objects
"""

import os, sys, re, gc, weakref

exc = [
  "function",
  "type",
  "list",
  "dict",
  "tuple",
  "wrapper_descriptor",
  "module",
  "method_descriptor",
  "member_descriptor",
  "instancemethod",
  "builtin_function_or_method",
  "frame",
  "classmethod",
  "classmethod_descriptor",
  "_Environ",
  "MemoryError",
  "_Printer",
  "_Helper",
  "getset_descriptor",
  "weakreaf"
]

inc = [
]

prev = {}

def dumpObjects(delta=True, limit=0, include=inc, exclude=[]):
  global prev
  if include != [] and exclude != []:
    print 'cannot use include and exclude at the same time'
    return
  print 'working with:'
  print '   delta: ', delta
  print '   limit: ', limit
  print ' include: ', include
  print ' exclude: ', exclude
  objects = {}
  gc.collect()
  oo = gc.get_objects()
  for o in oo:
    if getattr(o, "__class__", None):
      name = o.__class__.__name__
      if ((exclude == [] and include == [])       or \
          (exclude != [] and name not in exclude) or \
          (include != [] and name in include)):
        objects[name] = objects.get(name, 0) + 1
##    if more:
##      print o
  pk = prev.keys()
  pk.sort()
  names = objects.keys()
  names.sort()
  for name in names:
    if limit == 0 or objects[name] > limit:
      if not prev.has_key(name):
        prev[name] = objects[name]
      dt = objects[name] - prev[name]
      if delta or dt != 0:
        print '%0.6d -- %0.6d -- ' % (dt, objects[name]),  name
      prev[name] = objects[name]

def getObjects(oname):
  """
  gets an object list with all the named objects out of the sea of
  gc'ed objects
  """
  olist = []
  objects = {}
  gc.collect()
  oo = gc.get_objects()
  for o in oo:
    if getattr(o, "__class__", None):
      name = o.__class__.__name__
      if (name == oname):
        olist.append(o)
  return olist


