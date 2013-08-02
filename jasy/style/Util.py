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

    current = node
    while current:
        if current.type == "selector":
            selector.append(current.name)
        elif current.type == "mixin":
            selector.append(current.selector)

        current = getattr(current, "parent", None)

    result = []
    for item in itertools.product(*reversed(selector)):
        combined = ""
        for part in item:
            if combined:
                if "&" in part:
                    combined = part.replace("&", combined)
                else:
                    combined = "%s %s" % (combined, part)
            else:
                if "&" in part:
                    raise Exception("Can't merge selector %s - parent missing - at line %s!" % (part, node.line))
                else:
                    combined = part

        result.append(combined)

    return result

