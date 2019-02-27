
from __future__ import print_function

import os
import types
import pickle
import marshal
try:
    import copy_reg as copyreg
    STD_TYPES = [k for k,v in pickle.Pickler.dispatch.items() if v.__name__ != "save_global"]
except ImportError:
    import copyreg
    STD_TYPES = [k for k,v in pickle._Pickler.dispatch.items() if v.__name__ != "save_global"]

SEQ_TYPES = (list, tuple, set)
FUNC_TYPES = (types.FunctionType, types.MethodType, types.LambdaType, types.BuiltinFunctionType)

def setup(pickler=None, depth=1): # Prepare traceback pickle functionality
    """
        Prep traceback for pickling. Run this to allow pickling of traceback types.
        pickler :
            * If set to None. tracebacks are pickled in conservative mode. Classes are mocked, and objects replaced
              with representations, such that the traceback can be inspected regardless of environment.
            * If set to a pickler, objects will first be tested to see if they can be pickled by the pickler,
              and if so, their original form will remain untouched. This has the advantage of including real functional
              objects in the traceback, at the cost of requiring the original environment to unpickle.
        depth   :
            * How far to fan out from the traceback before returning representations of everything.
              The higher the value, the more you can inspect at the cost of extra pickle size.
              A value of -1 means no limit. Fan out forever and grab everything.
    """
    def _prepare_traceback(trace):
        files = _snapshot_source_files(trace) # Take a snapshot of all the source files
        trace = _clean(trace, pickler, depth) # Make traceback pickle friendly
        return _restore_traceback, (trace, files)
    copyreg.pickle(types.TracebackType, _prepare_traceback)


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
    return scoped_call(FunctionType, code, {"__builtins__": _from_import("types", "__builtins__")})

_mock = _class("mock", dct={
    "__init__": _savePickle(lambda s, d: s.__dict__.update(d)),
    "__class__": _savePickle(lambda s: s.mock), # pretend to be this
    "__repr__": _savePickle(lambda s: s.repr)}) # and look like this

@_savePickle
def _restore_traceback(trace, files):
    """ Restore traceback from pickle """
    print("LOADSTRACE", trace, type(trace), trace.__dict__)
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

def _clean(obj, pickler, depth, seen=None):
    """ Clean up pickleable stuff """
    depth -= 1
    if seen is None:
        seen = {}

    if type(obj) is types.TracebackType:
        print("TRACE", obj, obj in seen) # other mock being restored first breaking new mock?

    try: # If we have processed node, skip
        return seen[obj]
    except (KeyError, TypeError):
        pass

    obj_type = type(obj)

    if depth == -1: # We have reached our limit. Just make a basic representation
        print("MAX REACHED", obj_type, obj)
        result = repr(obj)

    elif obj_type == types.TracebackType:
        dct = {"repr": repr(obj), "mock": _from_import("types", "TracebackType")}
        seen[obj] = result = _call(_mock, dct) # Preload to stop recursive cycles
        dct.update((at, getattr(obj, at)) for at in dir(obj) if at.startswith("tb_"))
        dct["tb_frame"] = _clean(obj.tb_frame, pickler, depth+1, seen)
        dct["tb_next"] = _clean(obj.tb_next, pickler, depth+1, seen)

    elif obj_type == types.FrameType:
        dct = {"repr": repr(obj), "mock": _from_import("types", "FrameType")}
        seen[obj] = result = _call(_mock, dct) # Preload to stop recursive cycles
        dct.update((at, getattr(obj, at)) for at in dir(obj) if at.startswith("f_"))
        dct["f_builtins"] = _from_import("types", "__builtins__") # Load builtins at unpickle time
        dct["f_code"] = _clean(obj.f_code, pickler, depth+1, seen)
        dct["f_back"] = _clean(obj.f_back, pickler, depth+1, seen)
        dct["f_globals"] = {k: repr(v) for k, v in obj.f_globals.items() if k != "__builtins__"}
        dct["f_locals"] = {k: _clean(v, pickler, depth, seen) for k,v in obj.f_locals.items()}

    elif obj_type == types.CodeType:
        dct = {"repr": repr(obj), "mock": _from_import("types", "CodeType")}
        seen[obj] = result = _call(_mock, dct) # Preload to stop recursive cycles
        dct.update((at, getattr(obj, at)) for at in dir(obj) if at.startswith("co_"))
        dct["co_consts"] = _clean(obj.co_consts, pickler, depth+2, seen)
        dct["co_filename"] = os.path.abspath(obj.co_filename)

    elif obj_type in SEQ_TYPES:
        result = obj_type(_clean(o, pickler, depth, seen) for o in obj)

    elif obj_type == dict:
        result = {_clean(k, pickler, depth, seen): _clean(v, pickler, depth, seen) for k, v in obj.items()}

    elif pickler:
        try: # Try to see if we can just pickle straight up
            pickle.loads(pickle.dumps(obj))
            result = obj
        except Exception: # Otherwise all we can do is a representation of the object
            result = repr(obj)

    elif obj_type in FUNC_TYPES:
        result = _stub_function

    elif obj_type in STD_TYPES:
        result = obj

    elif obj_type == types.ModuleType:
        if not hasattr(obj, "__file__") or obj.__file__.startswith(os.path.dirname(types.__file__)):
            result = _import(obj.__name__) # Standard library stuff. Safe to import this.

    else:
        # try: # Create a mock object as a fake representation of the original for inspection
        #     dct ={"repr": repr(obj), "mock": object}
        #     seen[obj] = result = _call(_mock, dct) # Preload to stop recursive cycles
        #     dct.update((at, _clean(getattr(obj, at), pickler, depth, seen)) for at in dir(obj) if not at.startswith("__"))
        # except Exception as err:
        #     print("ERROR!!", err)
        #     result = repr(obj)
        result = repr(obj)

    try:
        seen[obj] = result
    except TypeError:
        pass
    return result


if __name__ == '__main__':
    class Tester(object):
        def makeBroke(self):
            raise RuntimeError()

    try:
        t = Tester()
        t.makeBroke()
    except Exception:
        import sys
        import pdb
        exc = sys.exc_info()
        setup() # Prep traceback functionality
        print("oldtrace", exc)
        trace = pickle.dumps(exc)
        newtrace = pickle.loads(trace)
        print("newtrace", newtrace)
        pdb.post_mortem(newtrace[2])
