import sys, os
sys.path.append(os.path.split(__file__)[0]+'/..')

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
        import pydump
        pydump.save_traceback('crash.dump')
