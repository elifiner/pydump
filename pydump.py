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
import pdb
import pickle
import linecache

__version__ = "1.1.0"

DUMP_VERSION = 1

def save_dump(filename, tb=None):
    """
    Saves a Python traceback in a pickled file. This function will usually be called from
    an except block to allow post-mortem debugging of a failed process.

    The saved file can be loaded with load_dump which creates a fake traceback
    object that can be passed to any reasonable Python debugger.

    The simplest way to do that is to run:

       $ pydump.py my_dump_file.dump
    """
    if not tb:
        tb = sys.exc_info()[2]
    fake_tb = FakeTraceback(tb)
    dump = {
        'traceback':fake_tb,
        'files':_get_traceback_files(fake_tb),
        'dump_version' : DUMP_VERSION
    }
    try:
        pickle.dump(dump, open(filename, 'wb'))
    except:
        import pdb; pdb.post_mortem()

def load_dump(filename):
    # ugly hack to handle running non-install pydump
    if 'pydump.pydump' not in sys.modules:
        sys.modules['pydump.pydump'] = sys.modules[__name__]
    return pickle.load(open(filename, 'rb'))

def debug_dump(dump_filename, post_mortem_func=pdb.post_mortem):
    dump = load_dump(dump_filename)
    _cache_files(dump['files'])
    tb = dump['traceback']
    _old_checkcache = linecache.checkcache
    linecache.checkcache = lambda filename=None: None
    post_mortem_func(tb)
    linecache.checkcache = _old_checkcache

class FakeClass(object):
    def __init__(self, repr, vars):
        self.__repr = repr
        self.__dict__.update(vars)

    def __repr__(self):
        return self.__repr

class FakeCode(object):
    def __init__(self, code):
        self.co_filename = os.path.abspath(code.co_filename)
        self.co_name = code.co_name
        self.co_argcount = code.co_argcount
        self.co_consts = tuple(
            FakeCode(c) if hasattr(c, 'co_filename') else c 
            for c in code.co_consts
        )
        self.co_firstlineno = code.co_firstlineno
        self.co_lnotab = code.co_lnotab
        self.co_varnames = code.co_varnames
        self.co_flags = code.co_flags

class FakeFrame(object):
    def __init__(self, frame):
        self.f_code = FakeCode(frame.f_code)
        self.f_locals = _convert_dict(frame.f_locals)
        self.f_globals = _convert_dict(frame.f_globals)
        self.f_lineno = frame.f_lineno
        self.f_back = FakeFrame(frame.f_back) if frame.f_back else None

        if 'self' in self.f_locals:
            self.f_locals['self'] = _convert_obj(frame.f_locals['self'])

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
        return repr(v)
    except Exception, e:
        return "repr error: " + str(e)

def _convert_obj(obj):
    return FakeClass(_safe_repr(obj), _convert_dict(obj.__dict__))

def _convert_dict(v):
    return dict((_convert(k), _convert(i)) for (k, i) in v.items())

def _convert_seq(v):
    return (_convert(i) for i in v)

def _convert(v):
    from datetime import date, time, datetime, timedelta

    BUILTIN = (
        str, unicode,
        int, long, float,
        date, time, datetime, timedelta,
    )

    if v is None:
        return v

    if type(v) in BUILTIN:
        return v

    if type(v) is tuple:
        return tuple(_convert_seq(v))

    if type(v) is list:
        return list(_convert_seq(v))

    if type(v) is set:
        return set(_convert_seq(v))

    if type(v) is dict:
        return _convert_dict(v)

    return _safe_repr(v)

def _cache_files(files):
    for name, data in files.iteritems():
        lines = [line+'\n' for line in data.splitlines()]
        linecache.cache[name] = (len(data), None, lines, name)
