#!/usr/bin/env python
import sys
import pickle

def save_traceback(filename, tb=None):
    """
    Saves a Python traceback in a pickled file. This function will usually be called from
    an except block to allow post-mortem debugging of a failed process.

    The saved file can be loaded with load_traceback which creates a fake traceback
    object that can be passed to any reasonable Python debugger.

    The simplest way to do that is to run:

       $ pydump.py my_dump_file.pydump
    """
    if not tb:
        tb = sys.exc_info()[2]
    ftb = FakeTraceback(tb)
    pickle.dump(ftb, open(filename, 'wb'))

def load_traceback(filename):
    return pickle.load(open(filename, 'rb'))

class FakeCode(object):
    def __init__(self, code):
        self.co_filename = code.co_filename
        self.co_name = code.co_name
        self.co_argcount = code.co_argcount
        self.co_consts = tuple(
            FakeCode(c) if hasattr(c, 'co_filename') else c 
            for c in code.co_consts
        )
        self.co_firstlineno = code.co_firstlineno
        self.co_lnotab = code.co_lnotab

class FakeFrame(object):
    def __init__(self, frame):
        self.f_code = FakeCode(frame.f_code)
        self.f_locals = _flat_dict(frame.f_locals)
        self.f_globals = _flat_dict(frame.f_globals)
        self.f_lineno = frame.f_lineno
        self.f_back = FakeFrame(frame.f_back) if frame.f_back else None

class FakeTraceback(object):
    def __init__(self, traceback):
        self.tb_frame = FakeFrame(traceback.tb_frame)
        self.tb_lineno = traceback.tb_lineno
        self.tb_next = FakeTraceback(traceback.tb_next) if traceback.tb_next else None
        self.tb_lasti = 0

def _flat_dict(d):
    return dict(zip(d.keys(), [repr(v) for v in d.values()]))

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(usage="%prog <dump>", description="Opens a *.pydump file for post-mortem debugging")
    parser.add_option("--pdb",  action="append_const", const="pdb",  dest="debuggers", help="Use builtin pdb or pdb++")
    parser.add_option("--pudb", action="append_const", const="pudb", dest="debuggers", help="Use pudb visual debugger")
    parser.add_option("--ipdb", action="append_const", const="ipdb", dest="debuggers", help="Use ipdb IPython debugger")
    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.error('missing arguments')

    tb = load_traceback(args[0])

    if not options.debuggers:
        options.debuggers = ["pudb", "ipdb", "pdb"]

    for debugger in options.debuggers:
        try:
            dbg = __import__(debugger)
        except ImportError, e:
            print >>sys.stderr, str(e)
            continue
        else:
            print >>sys.stderr, "Starting debugger %s..." % debugger
            if debugger == "pudb":
                dbg.post_mortem((None, None, tb))
            else:
                dbg.post_mortem(tb)
            break
