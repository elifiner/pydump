"""
The MIT License (MIT)
Copyright (C) 2012 Eli Finer <eli.finer@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
import sys
import pickle
import linecache

__version__ = "1.0.1"
__all__ = ['save_dump', 'load_dump', '__version__']

DUMP_VERSION = 1

def save_dump(filename, tb=None):
    """
    Saves a Python traceback in a pickled file. This function will usually be called from
    an except block to allow post-mortem debugging of a failed process.

    The saved file can be loaded with load_dumpwhich creates a fake traceback
    object that can be passed to any reasonable Python debugger.

    The simplest way to do that is to run:

       $ pydump.py my_dump_file.pydump
    """
    if not tb:
        tb = sys.exc_info()[2]
    fake_tb = FakeTraceback(tb)
    dump = {
        'traceback':fake_tb,
        'files':_get_traceback_files(fake_tb),
        'dump_version' : DUMP_VERSION
    }
    pickle.dump(dump, open(filename, 'wb'))

def load_dump(filename):
    # ugly hack to handle running non-install pydump
    if 'pydump.pydump' not in sys.modules:
        sys.modules['pydump.pydump'] = sys.modules[__name__]
    return pickle.load(open(filename, 'rb'))

class FakeClass(object):
    def __init__(self, repr, vars):
        self.__repr = repr
        self.__dict__.update(vars)

    def __repr__(self):
        return self.__repr

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
        self.co_varnames = code.co_varnames

class FakeFrame(object):
    def __init__(self, frame):
        self.f_code = FakeCode(frame.f_code)
        self.f_locals = _flat_dict(frame.f_locals)
        self.f_globals = _flat_dict(frame.f_globals)
        self.f_lineno = frame.f_lineno
        self.f_back = FakeFrame(frame.f_back) if frame.f_back else None

        # add current class memebers
        if 'self' in frame.f_locals:
            obj = frame.f_locals['self']
            self.f_locals['self'] = FakeClass(_safe_repr(obj), _flat_dict(obj.__dict__))

class FakeTraceback(object):
    def __init__(self, traceback):
        self.tb_frame = FakeFrame(traceback.tb_frame)
        self.tb_lineno = traceback.tb_lineno
        self.tb_next = FakeTraceback(traceback.tb_next) if traceback.tb_next else None
        self.tb_lasti = 0

def _get_traceback_files(traceback):
    files = {}
    while traceback:
        frame = traceback.tb_frame
        while frame:
            filename = os.path.abspath(frame.f_code.co_filename)
            try:
                files[filename] = open(filename).read()
            except IOError:
                files[filename] = "couldn't locate '%s' during dump" % frame.f_code.co_filename
            frame = frame.f_back
        traceback = traceback.tb_next
    return files

def _safe_repr(v):
    try:
        if isinstance(v, str):
            return v
        else:
            return repr(v)
    except Exception, e:
        return "error: " + str(e)

def _flat_dict(d):
    return dict(zip(d.keys(), [_safe_repr(v) for v in d.values()]))
