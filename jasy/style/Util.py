#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import itertools
        
def assembleDot(node, result=None):
    """
    Joins a dot node (cascaded supported, too) into a single string like "foo.bar.Baz"
    """
    
    if result == None:
        result = []

    for child in node:
        if child.type == "identifier":
            result.append(child.value)
        elif child.type == "dot":
            assembleDot(child, result)
        else:
            return None

    return ".".join(result)



def combineSelector(node):
    """
    Figures out the fully qualified selector of the given Node
    """

    selector = []

    while node:
        if node.type == "selector":
            selector.append(node.name)
        elif node.type == "mixin":
            selector.append(node.selector)

        node = getattr(node, "parent", None)

    return [" ".join(item) for item in itertools.product(*reversed(selector))]


