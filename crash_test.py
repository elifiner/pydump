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
        filename = __file__ + '.dump'
        print "Exception caught, writing %s" % filename
        pydump.save_dump(filename)
        print "Run 'pydump %s' to debug" % (filename)
