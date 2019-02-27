
from __future__ import print_function

import os
import types
import pickle
import marshal
try:
    import copy_reg as copyreg
    STD_TYPES = pickle.Pickler.dispatch.keys()
except ImportError:
    import copyreg
    STD_TYPES = pickle._Pickler.dispatch.keys()

SEQ_TYPES = (list, tuple, set)
FUNC_TYPES = (types.FunctionType, types.MethodType, types.LambdaType, types.BuiltinFunctionType, types.BuiltinMethodType)

class _call(object):
    """ Basic building block in pickle """
    def __reduce__(self):
        return self.func, self.args
    def __init__(self, func, *args):
        self.__dict__.update(locals())
    def __call__(self):
        self.func(*(arg() if isinstance(arg, Call) else arg for arg in self.args))

class _import(_call):
    def __init__(self, name):
        super(_import, self).__init__(__import__, name, [""])

class _from_import(_call):
    def __init__(self, module, name):
        super(_from_import, self).__init__(getattr, _import(module), name)

class _class(_call):
    def __init__(self, name, inherits=(object,), dct=None):
        super(_class, self).__init__(type, name, inherits, dct or {})

def _savePickle(func):
    """ Save function directly in pickle """
    typeMap = {types.FunctionType: "FunctionType", types.LambdaType: "LambdaType"}
    funcType = typeMap.get(type(func))
    FunctionType = _from_import("types", funcType)
    code = _call(marshal.loads, marshal.dumps(func.__code__))
    scoped_call = type(func.__name__, (_call, ), {"__call__": lambda _, *a, **k: func(*a, **k)})
    return scoped_call(FunctionType, code, {"__builtins__": _import("__builtin__")})

_mock = _class("mock", dct={
    "__init__": _savePickle(lambda s, d: s.__dict__.update(d)),
    "__class__": _savePickle(lambda s: s.mock), # pretend to be this
    "__repr__": _savePickle(lambda s: s.repr)}) # and look like this

def _prepare_traceback(trace):
    """ Prep traceback for pickling """
    files = _snapshot_source_files(trace) # Take a snapshot of all the source files
    trace = _clean(trace) # Make traceback pickle friendly
    return _restore_traceback, (trace, files)

@_savePickle
def _restore_traceback(trace, files):
    """ Restore traceback from pickle """
    import linecache # Add source files to linecache for debugger to see them.
    for name, data in files.items():
        lines = [line + "\n" for line in data.splitlines()]
        linecache.cache[name] = (len(data), None, lines, name)
    return trace

def _snapshot_source_files(trace):
    """ Grab all source file information from traceback """
    files = {}
    while trace:
        frame = trace.tb_frame
        while frame:
            filename = os.path.abspath(frame.f_code.co_filename)
            if filename not in files:
                try:
                    with open(filename) as f:
                        files[filename] = f.read()
                except IOError:
                    files[filename] = "Couldn't locate '%s' during dump." % frame.f_code.co_filename
            frame = frame.f_back
        trace = trace.tb_next
    return files

@_savePickle
def _stub_function(*_, **__):
    """ Replacement for sanitized functions """
    raise UserWarning("This is a stub function. The original could not be serialized.")

def _clean(obj, depth=1, seen=None):
    """ Clean up pickleable stuff """
    if seen is None:
        seen = {}

    try: # If we have processed node, skip
        return seen[obj]
    except (KeyError, TypeError):
        pass

    obj_type = type(obj)

    if not depth:
        print("HIT MAX DEPTH", obj_type, obj)
        result = repr(obj)

    # try: # Try initially to see if we can just pickle straight up
    #     pickle.loads(pickle.dumps(obj))
    #     seen[obj] = result = obj
    # except Exception:
    #     pass

    elif obj_type == types.TracebackType:
        seen[obj] = result = _call(None) # Preload to stop recursive cycles
        dct ={"repr": repr(obj), "mock": _from_import("types", "TracebackType")}
        dct.update((at, getattr(obj, at)) for at in dir(obj) if at.startswith("tb_"))
        dct["tb_frame"] = _clean(obj.tb_frame, 1, seen)
        dct["tb_next"] = _clean(obj.tb_next, 1, seen)
        result.__init__(_mock, dct) # Update now we have the data

    elif obj_type == types.FrameType:
        seen[obj] = result = _call(None) # Preload to stop recursive cycles
        dct ={"repr": repr(obj), "mock": _from_import("types", "FrameType")}
        dct.update((at, getattr(obj, at)) for at in dir(obj) if at.startswith("f_"))
        dct["f_builtins"] = _import("__builtin__") # Load builtins at unpickle time
        dct["f_code"] = _clean(obj.f_code, 1, seen)
        dct["f_back"] = _clean(obj.f_back, 1, seen)
        dct["f_globals"] = {k: repr(v) for k, v in obj.f_globals.items() if k != "__builtins__"}
        dct["f_locals"] = {k: repr(v) for k, v in obj.f_locals.items()}
        result.__init__(_mock, dct) # Update with gathered data

    elif obj_type == types.CodeType:
        seen[obj] = result = _call(None) # Preload to stop recursive cycles
        dct ={"repr": repr(obj), "mock": _from_import("types", "CodeType")}
        dct.update((at, getattr(obj, at)) for at in dir(obj) if at.startswith("co_"))
        dct["co_consts"] = _clean(obj.co_consts, 1, seen)
        dct["co_filename"] = os.path.abspath(obj.co_filename)
        result.__init__(_mock, dct) # Update with gathered data

    elif obj_type in SEQ_TYPES:
        result = obj_type(_clean(o, depth, seen) for o in obj)

    elif obj_type == dict:
        result = {_clean(k, depth, seen): _clean(v, depth, seen) for k, v in obj.items()}

    elif obj_type in FUNC_TYPES:
        result = _stub_function

    elif obj_type == types.ClassType:
        # TODO: do something with this
        result = repr(obj)

    elif obj_type == types.InstanceType:
        # TODO: do something with this too!
        result = repr(obj)

    elif obj_type == type:
        result = repr(obj)

    elif obj_type in STD_TYPES:
        result = obj

    else:
        # TODO: Add in fake object before final repr fallback
        result = repr(obj)

    try:
        seen[obj] = result
    except TypeError:
        pass
    depth -= 1
    return result

# Set it up!
copyreg.pickle(types.TracebackType, _prepare_traceback)





if __name__ == '__main__':
    class Tester(object):
        def makeBroke(self):
            raise RuntimeError()

    try:
        t = Tester()
        t.makeBroke()
    except Exception:
        import sys
        exc = sys.exc_info()
        print(exc)
        trace = pickle.dumps(exc)
        import pdb
        newtrace = pickle.loads(trace)
        print("newtrace", newtrace)
        pdb.post_mortem(newtrace[2])
