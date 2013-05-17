#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

def getRevision():
    """Returns the last revision/hash of the svn.""" 

    return executeCommand("svnversion", "Could not figure out git revision. Is there a valid Git repository?", path=path)  
