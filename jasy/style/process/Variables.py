#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import copy, re
import jasy.style.parse.Node as Node
import jasy.core.Console as Console



class VariableError(Exception):
    def __init__(self, message, node):
        Exception.__init__(self, "Variable Error: %s for node type=%s in %s at line %s!" % (message, node.type, node.getFileName(), node.line))


def compute(tree):
    Console.info("Resolving variables...")
    Console.indent()

    retval = __computeRecurser(tree, None, {})

    Console.outdent()

    return retval





def __computeRecurser(node, scope, values):

    remaining = False

    # Update scope of new block starts
    if hasattr(node, "scope"):
        scope = node.scope
        values = copy.copy(values)
        node.values = values

        # Reset all local variables to None
        # which enforces not to keep values from outer scope
        for name in scope.modified:
            values[name] = None


