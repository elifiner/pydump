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
        import sys, pdb, pydump
        try:
            import cPickle as pickle
        except ImportError:
            import pickle

        pydump.setup()
        trace = pickle.dumps(sys.exc_info()[2])
        pdb.post_mortem(pickle.loads(trace))
