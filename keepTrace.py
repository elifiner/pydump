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

from __future__ import print_function

import os
import types
import pickle
import marshal
try: # Python 2
    import copy_reg as copyreg
    STD_TYPES = [k for k,v in pickle.Pickler.dispatch.items() if v.__name__ not in ("save_global", "save_inst")]
except ImportError:
    import copyreg
    STD_TYPES = [k for k,v in pickle._Pickler.dispatch.items() if v.__name__ not in ("save_global", "save_type")]

SEQ_TYPES = (list, tuple, set)
FUNC_TYPES = (types.FunctionType, types.MethodType, types.LambdaType, types.BuiltinFunctionType)

def init(pickler=None, depth=3, include_source=True): # Prepare traceback pickle functionality
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
    def prepare_traceback(trace):
        trace = _clean(trace, pickler, depth) # Make traceback pickle friendly
        if include_source:
            files = _snapshot_source_files(trace) # Take a snapshot of all the source files
            return restore_traceback, (trace, files)
        return _savePickle(lambda t: t), (trace, ) 

    @_savePickle
    def restore_traceback(trace, files):
        import linecache # Add source files to linecache for debugger to see them.
        for name, data in files.items():
            lines = [line + "\n" for line in data.splitlines()]
            linecache.cache[name] = (len(data), None, lines, name)
        return trace

    copyreg.pickle(types.TracebackType, prepare_traceback)

# There is a bug in python 2.* pickle (not cPickle) that struggles to handle
# recursive reduction objects. If using python 2.*, try to always pickle with cPickle
# to be safe.
class _call(object):
    """ Basic building block in pickle """
    def __reduce__(self):
        if self.func == _mock and not self.args[0]:
            raise RuntimeError("debug")
        return self.func, self.args
    def __init__(self, func, *args):
        self.__dict__.update(locals())
    def __call__(self):
        self.func(*(arg() if isinstance(arg, Call) else arg for arg in self.args))

class _import(_call):
    def __init__(self, name):
        super(_import, self).__init__(__import__, name)

class _from_import(_call):
    def __init__(self, module, name):
        super(_from_import, self).__init__(getattr, _import(module), name)

def _savePickle(func):
    """ Save function directly in pickle """
    typeMap = {types.FunctionType: "FunctionType", types.LambdaType: "LambdaType"}
    funcType = typeMap.get(type(func))
    FunctionType = _from_import("types", funcType)
    code = _call(marshal.loads, marshal.dumps(func.__code__))
    scoped_call = type(func.__name__, (_call, ), {"__call__": lambda _, *a, **k: func(*a, **k)})
    return scoped_call(FunctionType, code, {"__builtins__": _from_import("types", "__builtins__")})

_mock = _call(type, "mock", (object, ), {
    "__init__": _savePickle(lambda s, d: s.__setattr__("__dict__", d)), # We cannot lose reference to this dict.
    "__class__": _call(property, _savePickle(lambda s: s._mock)), # pretend to be this
    "__repr__": _savePickle(lambda s: s._repr)}) # and look like this

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
def _stub(*_, **__):
    """ Replacement for sanitized functions """
    raise UserWarning("This is a stub function. The original was not serialized.")

def _clean(obj, pickler, depth, seen=None):
    """ Clean up pickleable stuff """
    depth -= 1
    if seen is None:
        seen = {}

    obj_id = id(obj)
    if obj_id in seen: # If we have processed object, skip
        return seen[obj_id]

    try:
        obj_type = type(obj)
        if depth == -1: # We have reached our limit. Just make a basic representation
            seen[obj_id] = result = repr(obj)
            return result

        if obj_type == types.TracebackType:
            dct = {"_repr": repr(obj), "_mock": _from_import("types", "TracebackType")}
            seen[obj_id] = result = _call(_mock, dct) # Preload to stop recursive cycles
            dct.update((at, getattr(obj, at)) for at in dir(obj) if at.startswith("tb_"))
            dct["tb_frame"] = _clean(obj.tb_frame, pickler, depth+1, seen)
            dct["tb_next"] = _clean(obj.tb_next, pickler, depth+1, seen)
            return result

        if obj_type == types.FrameType:
            dct = {"_repr": repr(obj), "_mock": _from_import("types", "FrameType")}
            seen[obj_id] = result = _call(_mock, dct) # Preload to stop recursive cycles
            dct.update((at, getattr(obj, at)) for at in dir(obj) if at.startswith("f_"))
            dct["f_builtins"] = _from_import("types", "__builtins__") # Load builtins at unpickle time
            dct["f_code"] = _clean(obj.f_code, pickler, depth+1, seen)
            dct["f_back"] = _clean(obj.f_back, pickler, depth+1, seen)
            dct["f_globals"] = {k: _clean(v, pickler, depth, seen) for k, v in obj.f_globals.items() if not k.startswith("__")}
            dct["f_locals"] = {k: _clean(v, pickler, depth, seen) for k,v in obj.f_locals.items()}
            return result

        if obj_type == types.CodeType:
            dct = {"_repr": repr(obj), "_mock": _from_import("types", "CodeType")}
            seen[obj_id] = result = _call(_mock, dct) # Preload to stop recursive cycles
            dct.update((at, getattr(obj, at)) for at in dir(obj) if at.startswith("co_"))
            dct["co_consts"] = _clean(obj.co_consts, pickler, depth+2, seen)
            dct["co_filename"] = os.path.abspath(obj.co_filename)
            return result

        if obj_type in SEQ_TYPES:
            seen[obj_id] = result = obj_type(_clean(o, pickler, depth, seen) for o in obj)
            return result

        if obj_type == dict:
            seen[obj_id] = result = {_clean(k, pickler, depth, seen): _clean(v, pickler, depth, seen) for k, v in obj.items()}
            return result

        if pickler:
            try: # Try to see if we can just pickle straight up
                pickler.loads(pickler.dumps(obj))
                seen[obj_id] = result = obj
                return result
            except Exception: # Otherwise fallback to mocks/stubs
                pass

        if obj_type in FUNC_TYPES:
            seen[obj_id] = result = _stub
            return result

        if obj_type in STD_TYPES:
            seen[obj_id] = result = obj
            return result

        if obj_type == types.ModuleType:
            if not hasattr(obj, "__file__") or obj.__file__.startswith(os.path.dirname(types.__file__)):
                seen[obj_id] = result = _import(obj.__name__) # Standard library stuff. Safe to import this.
            else:
                seen[obj_id] = result = repr(obj) # Otherwise sanitize it!
            return result

        try: # Create a mock object as a fake representation of the original for inspection
            dct ={"_repr": repr(obj), "_mock": object}
            seen[obj_id] = result = _call(_mock, dct) # Preload to stop recursive cycles
            dct.update((at, _clean(getattr(obj, at), pickler, depth, seen)) for at in dir(obj) if not at.startswith("__"))
        except Exception as err: # Failing that, just get the representation of the thing...
            seen[obj_id] = result = repr(obj)
        return result
    except Exception as err:
        seen[obj_id] = result = "Failed to serialize object: %s" % err
        return result
