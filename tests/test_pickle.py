import sys
import os
import os.path
import unittest
import traceback
try:
    import cPickle as pickle
except ImportError:
    import pickle

import keepTrace

def error():
    raise RuntimeError()

def recurse():
    recurse()

def syntax():
    eval("for this is")

class TestPickle(unittest.TestCase):

    def assertTrace(self, exc):
        restored = pickle.loads(pickle.dumps(exc))
        source_trace = "".join(traceback.format_exception(*exc)).replace(__file__, os.path.abspath(__file__))
        expect_trace = "".join(traceback.format_exception(*restored))
        self.assertEqual(source_trace, expect_trace)

    def test_roundtrip(self):
        keepTrace.init()
        try:
            error()
        except RuntimeError:
            self.assertTrace(sys.exc_info())

    def test_roundtrip_infinite_depth(self):
        keepTrace.init(depth=-1)
        try:
            error()
        except RuntimeError:
            self.assertTrace(sys.exc_info())

    def test_roundtrip_pickler(self):
        keepTrace.init(pickler=pickle)
        try:
            error()
        except RuntimeError:
            self.assertTrace(sys.exc_info())

    def test_roundtrip_full(self):
        keepTrace.init(pickle, -1)
        try:
            error()
        except RuntimeError:
            self.assertTrace(sys.exc_info())

    def test_roundtrip_no_source(self):
        keepTrace.init(include_source=False)
        try:
            error()
        except RuntimeError:
            self.assertTrace(sys.exc_info())

    def test_recursion(self):
        keepTrace.init()
        try:
            recurse()
        except RecursionError:
            self.assertTrace(sys.exc_info())

    def test_syntax(self):
        keepTrace.init()
        try:
            syntax()
        except SyntaxError:
            self.assertTrace(sys.exc_info())



if __name__ == '__main__':
    unittest.main()