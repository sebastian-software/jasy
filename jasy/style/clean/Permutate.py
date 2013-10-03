#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.style.parse.Parser as Parser
import jasy.core.Console as Console


def __translateToValue(code):
    """ Returns the code equivalent of the stored value for the given key """
    
    if code is None:
        pass
    elif code is True:
        code = "true"
    elif code is False:
        code = "false"
    elif type(code) is str and code.startswith("{") and code.endswith("}"):
        pass
    elif type(code) is str and code.startswith("[") and code.endswith("]"):
        pass
    else:
        code = "\"%s\"" % code
        
    return code


def patch(node, permutation):
    """ Replaces all occourences with incoming values """

    modified = False
    
    if node.type == "identifier":
        name = node.value
        replacement = __translateToValue(permutation.get(name))

        if replacement:
            Console.debug("Found permutation query (%s => %s) in line %s", name, replacement, node.line)
            replacementNode = Parser.parseExpression(replacement)
            node.parent.replace(node, replacementNode)
            modified = True
         
    # Process children
    for child in reversed(node):
        if child != None:
            if patch(child, permutation):
                modified = True

    return modified

