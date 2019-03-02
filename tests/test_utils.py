
import os
import unittest
from utils import get_traces, normalize_trace

class TestUtils(unittest.TestCase):

    def test_detect_traceback(self):
        test_string = """
package__ None
__spec__ None
keepTrace <module 'keepTrace' from 'd:\\documents\\test\\pydump\\keepTrace.py'>
os <module 'os' from 'C:\\Program Files\\Python36\\lib\\os.py'>
pickle <module 'pickle' from 'C:\\Program Files\\Python36\\lib\\pickle.py'>
sys <module 'sys' (built-in)>
traceback <module 'traceback' from 'C:\\Program Files\\Python36\\lib\\traceback.py'>
unittest <module 'unittest' from 'C:\\Program Files\\Python36\\lib\\unittest\\__init__.py'>
D:\Documents\TEST\pydump\tests\test_pickle.py
Traceback (most recent call last):
  File "tests\test_pickle.py", line 24, in test_roundtrip
    error()
  File "tests\test_pickle.py", line 21, in error
    raise RuntimeError()
RuntimeError
D:\Documents\TEST\pydump
"""
        result = ["""Traceback (most recent call last):
  File "tests\test_pickle.py", line 24, in test_roundtrip
    error()
  File "tests\test_pickle.py", line 21, in error
    raise RuntimeError()
RuntimeError"""]

        self.assertEqual(list(get_traces(test_string)), result)

    def test_normalize_traceback(self):
        test_string_base = """
Traceback (most recent call last):
  File "{0}", line 24, in test_roundtrip
    error()
  File "{0}", line 21, in error
    raise RuntimeError()
RuntimeError"""
        test_string = test_string_base.format(__file__)
        result = test_string_base.format(os.path.realpath(__file__))
        self.assertEqual(normalize_trace(test_string), result)


if __name__ == '__main__':
    unittest.main()
