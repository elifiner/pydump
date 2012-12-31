if __name__ == '__main__':
    def foo():
        foovar = 7
        bar()

    def bar():
        barvar = "hello"
        list_sample = [1,2,3,4]
        dict_sample = {'a':1, 'b':2}
        baz()

    def baz():
        momo = Momo()
        momo.raiser()

    class Momo(object):
        def __init__(self):
            self.momodata = "Some data"

        def raiser(self):
            raise Exception("BOOM!")

    try:
        foo()
    except:
        import pydump
        filename = __file__ + '.dump'
        print "Exception caught, writing %s" % filename
        pydump.save_dump(filename)
        print "Run 'pydump %s' to debug" % (filename)
