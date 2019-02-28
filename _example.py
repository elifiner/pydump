#!/usr/bin/env python

"""
    Run for an example. Causing an exception. Catching. Pickling. Unpickling. Debugging.
"""

if __name__ == '__main__':

    def foo():
        foovar = 7
        bar()

    def bar():
        barvar = "hello"
        list_sample = [1,2,3,4]
        dict_sample = {'a':1, 'b':2}
        baz()

    def baz():
        momo = Momo()
        momo.raiser()

    class Momo(object):
        def __init__(self):
            self.momodata = "Some data"

        def raiser(self):
            raise Exception("BOOM!")

    try:
        foo()
    except:
        import sys, pdb, pydump
        try: # Use cPickle if in python 2. Python 2 standard pickle has a bug with referencing.
            import cPickle as pickle
        except ImportError:
            import pickle

        pydump.setup() # Initialize traceback functionality with default settings.
        trace = pickle.dumps(sys.exc_info()[2]) # Dump error traceback
        pdb.post_mortem(pickle.loads(trace)) # Restore traceback and debug.
