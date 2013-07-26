#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013 Sebastian Werner
#

import jasy.style.parse.Node as Node
import jasy.style.parse.ScopeScanner as ScopeScanner
import jasy.core.Console as Console

__all__ = ["cleanup", "Error"]


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
    x = 0
    cleaned = False
    
    while True:
        x = x + 1
        Console.debug("Removing unused variables [Iteration: %s]...", x)
        Console.indent()

        if __cleanup(node):
            ScopeScanner.scan(node)
            cleaned = True
            Console.outdent()
        else:
            Console.outdent()
            break
        
    return cleaned



#
# Implementation
#

def __cleanup(node):
    """ The scanner part which looks for scopes with unused variables/params """
    
    cleaned = False

    for child in list(node):
        if child != None and __cleanup(child):
            cleaned = True

    # Process any selector separately.
    # Variables defined in there do not affect the outside
    if node.type == "selector":
        rules = node.rules
        if rules.scope.unused:
            if __recurser(node.rules, rules.scope.unused):
                cleaned = True

    # Process global style sheet node
    elif node.type == "sheet" and not hasattr(node, "parent"):
        if node.scope.unused:
            if __recurser(node, node.scope.unused):
                cleaned = True            

    return cleaned
            
            
            
def __recurser(node, unused):
    """ 
    The cleanup part which always processes one scope and cleans up params and
    variable definitions which are unused
    """
    
    retval = False
    
    # Process children, but ignore all selector blocks as these should be processed separately
    if node.type != "selector":
        for child in reversed(node):
            # None children are allowed sometimes e.g. during array_init like [1,2,,,7,8]
            if child != None:
                if __recurser(child, unused):
                    retval = True
                    
    if node.type == "mixin":
        # Mixin with actual users aka extending customers
        if getattr(node, "selector", None):
            pass

        # Remove full unused functions (when not in top-level scope)
        elif node.name in unused:
            Console.debug("Removing unused mixin %s at line %s" % (node.name, node.line))
            node.parent.remove(node)
            retval = True

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
                        retval = True
                    else:
                        break

    elif node.type == "declaration":
        if node.name in unused:
            if hasattr(node, "initializer"):
                init = node.initializer
                if init.type in ("null", "this", "true", "false", "identifier", "number", "string", "regexp"):
                    Console.debug("Removing unused primitive variable %s at line %s" % (node.name, node.line))
                    node.parent.remove(node)
                    retval = True
                    
                else:
                    Console.debug("Could not automatically remove unused variable %s at line %s without possible side-effects" % (node.name, node.line))
                
            else:
                node.parent.remove(node)
                retval = True

    return retval

