#!/usr/bin/env python

"""
    Run for an example. Causing an exception. Catching. Pickling. Unpickling. Debugging.
"""

from __future__ import print_function

if __name__ == '__main__':

    import sys, pdb, traceback, keepTrace
    try: # Use cPickle if in python 2. Python 2 standard pickle has a bug with referencing.
        import cPickle as pickle
    except ImportError:
        import pickle

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

        # Initialize traceback functionality with default settings.
        keepTrace.init() # This can happen at any time before pickle. Could be a startup thing.

        data = pickle.dumps(sys.exc_info()) # Dump error traceback

        #############################################
        ############### Sometime Later ##############
        #############################################

        exc = pickle.loads(data) # Restore traceback

        print("="*34)
        traceback.print_exception(*exc) # Visualize stacktrace
        print("="*34)
        pdb.post_mortem(exc[2]) # launch debugger
