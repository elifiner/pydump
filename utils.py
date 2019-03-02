# General traceback utilities
from __future__ import print_function

import re
import os.path

def get_traces(string):
    """ Find all tracebacks in the provided string (as formatted by the traceback module). """
    buff = []
    for line in string.splitlines():
        if not buff and line != "Traceback (most recent call last):":
            continue
        buff.append(line)
        if len(buff) > 1 and not line.startswith("  "):
            yield "\n".join(buff)
            buff = []

def normalize_trace(trace_string):
    """ Make traceback paths absolute if applicable """
    def abspath(match):
        path = os.path.realpath(match.group(1))
        return match.group(0)[:match.start(1)-match.start(0)] + path + match.group(0)[match.end(1)-match.start(0):] if os.path.isfile(path) else match.group(0)
    return re.sub(r"\s*File \"([^\"]+)\", line \d+, in \w+", abspath, trace_string)
