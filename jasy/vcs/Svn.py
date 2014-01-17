#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import os.path, re, urllib.parse, shutil, yaml

from jasy.core.Util import executeCommand
import jasy.core.Console as Console

def getRevision(path=None):
	"""Returns the last revision/hash of the svn."""

	return executeCommand("svnversion", "Could not figure out SVN revision. Is there a valid SVN repository?", path=path)


def getBranch(path=None):
	"""Returns the current branch name"""

	info = getInfo(path)
	parsedUrl = urllib.parse.urlparse(info["URL"])
	pathSplits = parsedUrl.path.split("/")

	isTag = False
	isBranch = False

	for split in pathSplits:
		if isBranch or isTag or split == "trunk":
			return split
		elif split == "branches":
			isBranch = True
		elif split == "tags":
			isTag = True

	return None


def getInfo(path=None):
	textResult = executeCommand("svn info", "Could not figure out SVN info. Is there a valid SVN repository?", path=path)
	parsedResult = yaml.load(textResult)

	return parsedResult