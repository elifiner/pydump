
keepTrace
=========

This project provides the ability to pickle traceback objects.
Specifically including enough details about the exception to be able to restore
and debug the traceback at a later date.

``` python
try:
    some_bad_code()
except Exception:
    import sys, pickle, keepTrace
    keepTrace.init() # Can be initialized at any point before pickle
    with open(some_path, "wb") as f:
        pickle.dump(sys.exc_info(), f)
```

...sometime later...

``` python
import pickle, pdb
with open(some_path, "rb") as f:
  trace = pickle.load(f)
pdb.post_mortem(trace[2])
```

The details of where and how you chose to save the pickle remain with the reader.
The pickle process has been designed in such a way that this module is not required
to unpickle the traceback.


Usage. 1. 2. 3.
=====

There are three things to know to get up and running.

###1) Initialize

To be able to pickle tracebacks you first need to run the "init" function. This can happen anytime
before pickle. You can even have it trigger on startup if you wish.

``` python
import keepTrace
keepTrace.init()
```

###2) Pickler

Init takes two arguments. Pickler and Depth.
If you supply a pickler, it will use it to determine if an object can or cannot be pickled by that pickler.
In general, use the pickler you plan on later pickling the tracebacks with. ie: pickle, cloudpickle, dill.

If the pickler fails to pickle an object, a fallback is provided.

If no pickler is used (default), then everything will go to the fallback. This means you can unpickle without the
original environment, but all objects will be replaced by mocks and stubs.

``` python
import keepTrace, pickle
keepTrace.init(pickler=pickle)
```

###3) Depth

Init takes two arguments. Pickler and Depth.
Depth controls how far beyond the traceback the pickle will reach. ie: objects within attributes, within classes within objects...
Objects at the edge of the pickle depth will be replaced by their representations.

Use a shallow depth to keep pickles lighter. Use a higher depth if you wish to inspect further and / or wish to have more functional objects (pickled objects with representations inside them will fail to work for obvious reasons).

Setting depth to -1 will make depth infinite.

``` python
import keepTrace
keepTrace.init(depth=5)
```

Setting depth to infinite, and using a heavy-duty pickler (dill) will lead to very detailed and interractive debugging.
This is not however a core dump. So do not expect everything to function as though it were a live session.

``` python
import keepTrace, dill
keepTrace.init(pickler=dill, depth=-1)
```

By default the pickles are very conservative. Everything will be mocked and stubbed. You will not need anything other than an
unpickler to view and debug the traceback, but you will not be able to run any functions etc.


=================

An original message from pydump. The inspiration and initially the origin of this project.



##Why I wrote this?

I spent way too much time trying to discern details about bugs from
logs that don't have enough information in them. Wouldn't it be nice
to be able to open a debugger and load the entire stack of the crashed
process into it and look around like you would if it crashed on your own
machine?

##Possible uses

This project (or approach) might be useful in multiprocessing environments
running many unattended processes. The most common case for me is on
production web servers that I can't really stop and debug. For each
exception caught, I write a dump file and I can debug each issue on
my own time, on my own box, even if I don't have the source, since
the relevant source is stored in the dump file.
