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
    
supported = set(("tokens", "tree", "compress", "optimize"))
job = sys.argv[1]
if not job in supported:
    sys.stderr.write("Invalid job %s\n" % job)
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG, format="%(message)s")

import jasy

import jasy.style.Engine as Engine
import jasy.style.output.Formatting as Formatting


for fname in sys.argv[2:]:
    text = open(fname, encoding="utf-8").read()
    
    print(">>> File: %s" % fname, file=sys.stderr)
    
    if job == "optimize":    
        tree = Engine.getTree(text, fname)
        tree = Engine.reduceTree(tree)
        print(Engine.compressTree(tree))

    elif job == "compress":    
        formatting = Formatting.Formatting("blocks", "whitespace", "statements", "indent")
        tree = Engine.getTree(text, fname)
        tree = Engine.reduceTree(tree)
        print(Engine.compressTree(tree, formatting))
        
    elif job == "tree":
        print(Engine.getTree(text, fname).toXml())

    elif job == "tokens":
        Engine.printTokens(text, fname)

