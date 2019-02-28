This began as a simple fork of the original pydump and I feel it still holds true to the
originals intentions. But since, it has been rewritten and taken a different strategy.

The original readme is below. Its sentiment still holds true.


Python post-mortem debugging
============================

Pydump writes the traceback of an exception into a file and
can later load it in a Python debugger. It works with the built-in
pdb and with other popular debuggers (pudb, ipdb, pdbpp, web_pdb, wdb).


Why I wrote this?
=================

I spent way too much time trying to discern details about bugs from
logs that don't have enough information in them. Wouldn't it be nice
to be able to open a debugger and load the entire stack of the crashed
process into it and look around like you would if it crashed on your own
machine?

Possible uses
=============

This project (or approach) might be useful in multiprocessing environments
running many unattended processes. The most common case for me is on
production web servers that I can't really stop and debug. For each
exception caught, I write a dump file and I can debug each issue on
my own time, on my own box, even if I don't have the source, since
the relevant source is stored in the dump file.
