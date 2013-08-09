#!/usr/bin/env python3

#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

# Import standard library stuff
import sys, os.path, json, logging

# Version check
if sys.version_info[0] < 3:
    sys.stderr.write("Jasy requires Python 3!\n")
    sys.exit(1)

# Include local Jasy into Python library path
basedir = os.path.join(os.path.dirname(sys.argv[0]), os.pardir)
if os.path.exists(os.path.join(basedir, "jasy")):
    sys.path.insert(0, basedir)
                
if len(sys.argv) == 1:
    sys.stderr.write("Missing job name\n")
    sys.exit(1)
    
supported = set(("tokens", "tree", "compress"))
job = sys.argv[1]
if not job in supported:
    sys.stderr.write("Invalid job %s\n" % job)
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG, format="%(message)s")

import jasy

from jasy.style.parse.Parser import parse
from jasy.style.parse.ScopeScanner import scan
from jasy.style.output.Compressor import Compressor
from jasy.core.Permutation import Permutation

for fname in sys.argv[2:]:
    text = open(fname, encoding="utf-8").read()
    root = parse(text, fname)
    variables = scan(root)
    
    print(">>> File: %s" % fname)
    
    if job == "compress":
        print(Compressor().compress(root))
        
    elif job == "tree":
        print(root.toXml())

    elif job == "tokens":
        print("TODO")

