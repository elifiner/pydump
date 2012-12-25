Python post-mortem debugging
============================

Pydump writes the traceback of an exception into a file and 
can later load it in a Python debugger. It works with the built-in 
pdb and with other popular debuggers (pudb, ipdb and pdbpp).

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
exception caught, I write a small pydump file and I can debug each
issue on my own time, on my own box (provided the source is located
in the same place as on the production box).

Future enhancements
===================

* Support more depths for local and global variables (right now I only store the repr)
