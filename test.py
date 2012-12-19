import pickle
from pydump import *

if __name__ == '__main__':
    tb = pickle.load(open('pycore.dump'))
    import pdb
    pdb.post_mortem(tb)