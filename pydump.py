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
from __future__ import print_function
import os
import sys
import types
import datetime
try:
    import cPickle as pickle
except ImportError:
    import pickle


BUILTIN = set((str, int, float, bytes, bytearray,
               type(None),
               datetime.date, datetime.time, datetime.datetime, datetime.timedelta))
try:
    import __builtin__ as builtins
    BUILTIN.add(unicode)
    BUILTIN.add(long)
except ImportError:
    import builtins


__version__ = "2.0.0"


class Fake(object):
    """ Fake a different class when unpickled """

    mock = NotImplemented

    @property
    def __class__(self):
        return self.__dict__.get("__mock__") or type(self)

    def __setstate__(self, state):
        state["__mock__"] = self.mock
        self.__dict__ = state


class FakeClass(Fake):

    mock = type

    def __init__(self, repr, vars):
        self.__repr = repr
        self.__dict__.update(vars)

    def __repr__(self):
        return self.__repr


class FakeCode(Fake):

    mock = types.CodeType

    def __init__(self, code):
        self.co_filename = os.path.abspath(code.co_filename)
        self.co_name = code.co_name
        self.co_argcount = code.co_argcount
        self.co_consts = tuple(
            FakeCode(c) if hasattr(c, "co_filename") else c for c in code.co_consts
        )
        self.co_firstlineno = code.co_firstlineno
        self.co_lnotab = code.co_lnotab
        self.co_varnames = code.co_varnames
        self.co_flags = code.co_flags


class FakeFrame(Fake):

    mock = types.FrameType

    def __init__(self, frame, cleaner):
        self.f_code = FakeCode(frame.f_code)
        self.f_locals = cleaner.dict(frame.f_locals)
        self.f_globals = cleaner.dict(frame.f_globals)
        self.f_lineno = frame.f_lineno
        self.f_back = FakeFrame(frame.f_back, cleaner) if frame.f_back else None

        if "self" in self.f_locals:
            self.f_locals["self"] = cleaner.obj(frame.f_locals["self"])


class FakeTraceback(Fake):

    mock = types.TracebackType

    def __init__(self, traceback, cleaner):
        self.tb_frame = FakeFrame(traceback.tb_frame, cleaner)
        self.tb_lineno = traceback.tb_lineno
        self.tb_next = FakeTraceback(traceback.tb_next, cleaner) if traceback.tb_next else None
        self.tb_lasti = 0


class Traceback(FakeTraceback):
    """
    The root of the traceback. Main entry point.
    Perform some extra steps to contain traceback essential additional info.

    Example usage:
        try:
            raise SomeError()
        except Exception:
            trace = Traceback()
            with open(filepath) as f:
                pickle.dump(trace, f)

        ~~~~~~ some time later ~~~~~~

        with open(filepath) as f:
            trace = pickle.load(f)
            pdb.post_mortem(trace)
    """

    def __init__(self, traceback=None, pickler=pickle, full=False):
        """ Walk through the traceback and sanitize non-pickleable things """
        if not traceback: # If no traceback given, get recent exception
            traceback = sys.exc_info()[2]
        cleaner = Cleaner(pickler, full)
        super(Traceback, self).__init__(traceback, cleaner)
        self.files = self._snapshot_source_files() # Snapshot source files

    def __setstate__(self, state):
        """
        Restore traceback.
        Also apply some utility functionality to make it usable for immediate post mortem
        """
        super(Traceback, self).__setstate__(state)
        self._restore_builtins()
        self._load_source_files()

    def _restore_builtins(traceback):
        while traceback:
            frame = traceback.tb_frame
            while frame:
                frame.f_globals["__builtins__"] = builtins
                frame = frame.f_back
            traceback = traceback.tb_next

    def _snapshot_source_files(traceback):
        files = {}
        while traceback:
            frame = traceback.tb_frame
            while frame:
                filename = os.path.abspath(frame.f_code.co_filename)
                if filename not in files:
                    try:
                        files[filename] = open(filename).read()
                    except IOError:
                        files[
                            filename
                        ] = "couldn't locate '%s' during dump" % frame.f_code.co_filename
                frame = frame.f_back
            traceback = traceback.tb_next
        return files

    def _load_source_files(self):
        """ Add files to the debuggers cache, recorded at the time of pickle """
        import linecache
        for name, data in self.files.items():
            lines = [line + "\n" for line in data.splitlines()]
            linecache.cache[name] = (len(data), None, lines, name)


class Cleaner(object):
    """ Sanitize and copy the data in the traceback to ensure a reliable pickle/unpickle """

    def __init__(self, pickler, full):
        self.pickler = pickler
        self.full = full # Attempt to pickle as much as possible.
        # This requires that objects exist in the environment when unpickling

    @staticmethod
    def repr(obj):
        try:
            return repr(obj)
        except Exception as err:
            return "[repr error]: " + str(err)

    def obj(self, obj):
        try:
            return FakeClass(self.repr(obj), self.dict(obj.__dict__))
        except:
            return self(obj)

    def dict(self, obj):
        return dict((self(k), self(v)) for k, v in obj.items())

    def seq(self, obj):
        return (self(i) for i in obj)

    def __call__(self, obj):
        # Standard built in types. Safe.
        obj_type = type(obj)
        if obj_type in BUILTIN:
            return obj

        # Standard container types
        if obj_type is tuple:
            return tuple(self.seq(obj))

        if obj_type is list:
            return list(self.seq(obj))

        if obj_type is set:
            return set(self.seq(obj))

        if obj_type is dict:
            return self.dict(obj)

        # We have something else. This may require an import on unpickle.
        # If we are pickling everything attempt to pickle this.
        # Otherwise we can play it safe and only keep a representation.
        if self.full:
            try:
                self.pickler.loads(self.pickler.dumps(obj))
                return obj
            except Exception:
                pass
        return self.repr(obj)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="%s v%s: post-mortem debugging for Python programs"
        % (sys.executable, __version__)
    )
    debugger_group = parser.add_mutually_exclusive_group(required=False)
    debugger_group.add_argument(
        "--pdb",
        action="store_const",
        const="pdb",
        dest="debugger",
        help="Use builtin pdb or pdb++",
    )
    debugger_group.add_argument(
        "--pudb",
        action="store_const",
        const="pudb",
        dest="debugger",
        help="Use pudb visual debugger",
    )
    debugger_group.add_argument(
        "--ipdb",
        action="store_const",
        const="ipdb",
        dest="debugger",
        help="Use ipdb IPython debugger",
    )
    debugger_group.add_argument(
        "--wdb",
        action="store_const",
        const="wdb",
        dest="debugger",
        help="Use wdb debugger",
    )
    debugger_group.add_argument(
        "--web_pdb",
        action="store_const",
        const="web_pdb",
        dest="debugger",
        help="Use web_pdb debugger",
    )
    parser.add_argument("filename", help="dumped file")
    args = parser.parse_args()
    if not args.debugger:
        args.debugger = "pdb"

    print("Starting %s..." % args.debugger, file=sys.stderr)
    dbg = __import__(args.debugger, fromlist=[""])
    with open(args.filename, "rb") as f:
        trace = pickle.load(f)
        dbg.post_mortem(trace)

if __name__ == "__main__":
    sys.exit(main() or 0)
