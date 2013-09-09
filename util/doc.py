#!/usr/bin/env python3

#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2012-2013 Sebastian Werner
#

# Import standard library stuff
import sys, os.path, logging, tempfile, re

# Version check
if sys.version_info[0] < 3:
    sys.stderr.write("Jasy requires Python 3!\n")
    sys.exit(1)

# Include local Jasy into Python library path
basedir = os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(sys.argv[0]), os.pardir)))
if os.path.exists(os.path.join(basedir, "jasy")):
    sys.path.insert(0, basedir)

import jasy
from jasy.core.Util import executeCommand
from jasy.core.File import rmdir, mkdir, exists

version = re.compile("[0-9]\.[0-9]+").match(jasy.__version__).group(0)
release = jasy.__version__

print("Running Doc Generator for Jasy %s (%s)" % (version, release))
print("From: %s" % basedir)
print("Dist: %s" % os.path.abspath("docs"))




#
# GENERATE API INDEXES
#

srcfolder = os.path.join(basedir, "jasy")

print("Generating API indexes...")

cmd = ["sphinx-apidoc", "--full", "--maxdepth", "4", "--output-dir", "docs", "-V", str(version), "-R", str(release), "-A", "Sebastian Werner", "-H", "Jasy – Web Tooling Framework", srcfolder]
executeCommand(cmd, "Could not generate indexies")


#
# UPDATING CONFIG FILE
#

print("Updating configuration...")

configContent = open(os.path.join("docs", "conf.py"), "r").read()
patches = {
    "#sys.path.insert(0, os.path.abspath('.'))" : "sys.path.insert(0, '%s')" % basedir,
    "extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']" : "extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode', 'sphinx.ext.coverage', 'sphinx.ext.viewcode', 'sphinx.ext.todo']",
    "#html_short_title = None" : "html_short_title = 'Jasy %s'" % release,
    "html_theme = 'default'" : "html_theme = 'nature'"
}

for patchKey in patches:
    configContent = configContent.replace(patchKey, patches[patchKey])

open(os.path.join("docs", "conf.py"), "w").write(configContent)

print("Done")

