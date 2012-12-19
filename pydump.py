import sys
import pickle

def flat_dict(d):
    return dict(zip(d.keys(), [repr(v) for v in d.values()]))

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
        # self.co_cellvars = code.co_cellvars
        # self.co_code = code.co_code
        # self.co_flags = code.co_flags
        # self.co_freevars = code.co_freevars
        # self.co_names = code.co_names
        # self.co_nlocals = code.co_nlocals
        # self.co_stacksize = code.co_stacksize
        # self.co_varnames = code.co_varnames

class FakeFrame(object):
    def __init__(self, frame):
        self.f_code = FakeCode(frame.f_code)
        self.f_locals = flat_dict(frame.f_locals)
        self.f_globals = flat_dict(frame.f_globals)
        self.f_lineno = frame.f_lineno
        self.f_back = FakeFrame(frame.f_back) if frame.f_back else None
        # self.f_lasti = frame.f_lasti
        # self.f_builtins = frame.f_builtins
        # self.f_exc_traceback = frame.f_exc_traceback
        # self.f_exc_type = frame.f_exc_type
        # self.f_exc_value = frame.f_exc_value
        # self.f_restricted = frame.f_restricted
        # self.f_trace = frame.f_trace

class FakeTraceback(object):
    def __init__(self, traceback):
        self.tb_frame = FakeFrame(traceback.tb_frame)
        self.tb_lineno = traceback.tb_lineno
        self.tb_next = FakeTraceback(traceback.tb_next) if traceback.tb_next else None
        self.tb_lasti = 0

if __name__ == '__main__':
    def foo():
        foovar = 7
        bar()

    def bar():
        barvar = "hello"
        baz()

    def baz():
        raise Exception("BOOM!")

    try:
        foo()
    except:
        _, _, tb = sys.exc_info()
        ftb = FakeTraceback(tb)

    pickle.dump(ftb, open('pycore.dump', 'wb'))
