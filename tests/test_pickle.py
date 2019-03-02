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


class TestPickle(unittest.TestCase):

    def test_roundtrip(self):
        sys.modules[__name__].__file__ = os.path.abspath(sys.modules[__name__].__file__)
        keepTrace.init()

        def error():
            raise RuntimeError()

        try:
            error()
        except RuntimeError:
            exc = sys.exc_info()
            exc_trace = traceback.format_exception(*exc)

            data = pickle.dumps(exc)
            exc_restored = pickle.loads(data)
            restored_trace = traceback.format_exception(*exc_restored)

            print(exc_trace)
            print(restored_trace)


if __name__ == '__main__':
    unittest.main()
