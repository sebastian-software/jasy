#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013 Sebastian Werner
#

import jasy.style.parse.Node as Node
import jasy.style.parse.ScopeScanner as ScopeScanner
import jasy.core.Console as Console


#
# Public API
#

class Error(Exception):
    def __init__(self, name, line):
        self.__name = name
        self.__line = line

    def __str__(self):
        return "Unallowed private field access to %s at line %s!" % (self.__name, self.__line)



def cleanup(node):
    """
    """

    if not hasattr(node, "variables"):
        ScopeScanner.scan(node)

    # Re cleanup until nothing to remove is found
    iteration = 0
    cleaned = False

    Console.debug("Removing unused variables...")
    Console.indent()

    while True:
        iteration += 1

        modified = __cleanup(node)
        if modified > 0:
            Console.debug("Removed %s unused variables", modified)
            ScopeScanner.scan(node)
            cleaned = True
        else:
            break

    Console.outdent()

    return cleaned



#
# Implementation
#

def __cleanup(node):
    """ The scanner part which looks for scopes with unused variables/params """

    cleaned = 0

    for child in list(node):
        if child != None:
            cleaned += __cleanup(child)

    # Process any selector separately.
    # Variables defined in there do not affect the outside
    if node.type == "selector":
        rules = node.rules
        if rules.scope.unused:
            cleaned += __recurser(node.rules, rules.scope.unused)

    # Process global style sheet node
    elif node.type == "sheet" and not hasattr(node, "parent"):
        if node.scope.unused:
            cleaned += __recurser(node, node.scope.unused)

    return cleaned



def __recurser(node, unused):
    """
    The cleanup part which always processes one scope and cleans up params and
    variable definitions which are unused
    """

    modified = 0

    # Process children, but ignore all selector blocks as these should be processed separately
    if node.type != "selector":
        for child in reversed(node):
            # None children are allowed sometimes e.g. during array_init like [1,2,,,7,8]
            if child != None:
                modified += __recurser(child, unused)

    if node.type == "mixin":
        # Mixin with actual users aka extending customers
        if getattr(node, "selector", None):
            pass

        # Remove full unused functions (when not in top-level scope)
        elif node.name in unused:
            Console.debug("Removing unused mixin %s at line %s" % (node.name, node.line))
            node.parent.remove(node)
            modified += 1

        else:
            # Remove unused parameters
            params = getattr(node.parent, "params", None)
            if params:
                # Start from back, as we can only remove params as long
                # as there is not a required one after the current one
                for variable in reversed(params):
                    if variable.name in unused:
                        Console.debug("Removing unused parameter '%s' in line %s", variable.name, variable.line)
                        params.remove(variable)
                        modified += 1
                    else:
                        break

    elif node.type == "declaration":
        if node.name in unused:
            if hasattr(node, "initializer"):
                init = node.initializer
                if init.type in ("null", "this", "true", "false", "identifier", "number", "string"):
                    Console.debug("Removing unused primitive variable %s at line %s" % (node.name, node.line))
                    node.parent.remove(node)
                    modified += 1

                else:
                    Console.debug("Could not automatically remove unused variable %s at line %s without possible side-effects" % (node.name, node.line))

            else:
                node.parent.remove(node)
                modified += 1

    return modified

