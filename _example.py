#!/usr/bin/env python

# MIT License
#
# Copyright (c) 2019 Jason Dixon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
