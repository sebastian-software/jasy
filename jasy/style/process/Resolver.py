#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.style.parse.Node as Node
import jasy.style.Util as Util
import jasy.core.Console as Console 


class ResolverError(Exception):
    def __init__(self, message, node=None):
        if node:
            Exception.__init__(self, "Resolver Error: %s in node \"%s\" in file \"%s\" at line %s!" % (message, node.type, node.getFileName(), node.line))
        else:
            Exception.__init__(self, "Resolver Error: %s!" % message)


def process(tree, permutation):
    __recurser(tree, permutation)





#
# Implementation
#

def __transform(value, name=None):

    if value is True:
        node = Node.Node(type="true")
    elif value is False:
        node = Node.Node(type="false")
    elif isinstance(value, str):
        node = Node.Node(type="string")
        node.value = value
    elif isinstance(value, (float, int)):
        node = Node.Node(type="number")
        node.value = value
    else:
        raise ResolverError("Could not transform field %s=%s to style value" % (name, value))

    return node


def __recurser(node, permutation, inCondition=False):

    # Process children first (resolve logic is inner-out)
    for child in reversed(node):
        if child is not None:
            __recurser(child, permutation, inCondition or getattr(child, "rel", None) == "condition")


    # Replace identifiers with their actual value
    if inCondition:
        if node.type == "identifier":
            if not permutation.has(node.value):
                raise ResolverError("Could not find field %s" % node.value, node)

            repl = __transform(permutation.get(node.value), node.value)
            node.parent.replace(node, repl)


    # Support block commands
    # These come with their own node.type
    if node.type == "if":
        check = __checkCondition(node.condition)

        if check is None:
            raise ResolverError("Invalid state in condition", node)

        if check:
            node.parent.insertAllReplace(node, node.thenPart)
        elif hasattr(node, "elsePart"):
            node.parent.insertAllReplace(node, node.elsePart)
        else:
            node.parent.remove(node)


    # Support inline commands
    # These are just attached to a node.type command
    elif node.type == "command":
        if node.name == "field":
            if len(node.params) == 0:
                raise ResolverError("Missing parameter to insert field via @field.", node)

            identifierNode = node.params[0]
            if identifierNode.type != "identifier":
                raise ResolverError("Invalid parameter to @field call: %s" % identifierNode.type, identifierNode)

            identifier = identifierNode.value
            if not permutation.has(identifier):
                raise ResolverError("Could not find field with the name %s" % identifier, identifierNode)

            repl = __transform(permutation.get(identifier), identifierNode)
            node.parent.replace(node, repl)

        else:
            raise ResolverError("Unsupported inline command %s" % node.name, node)


def __checkCondition(node):
    """
    Checks a comparison for equality. Returns None when
    both, truely and falsy could not be deteted.
    """
    
    if node.type == "false":
        return False
    elif node.type == "true":
        return True
        
    elif node.type == "eq":
        return __compareNodes(node[0], node[1])
    elif node.type == "ne":
        return __invertResult(__compareNodes(node[0], node[1]))
        
    elif node.type == "not":
        return __invertResult(__checkCondition(node[0]))
        
    elif node.type == "and":
        first = __checkCondition(node[0])
        if first != None and not first:
            return False

        second = __checkCondition(node[1])
        if second != None and not second:
            return False
            
        if first and second:
            return True

    elif node.type == "or":
        first = __checkCondition(node[0])
        second = __checkCondition(node[1])
        if first != None and second != None:
            return first or second

    return None


def __invertResult(result):
    """
    Used to support the NOT operator.
    """
    
    if type(result) == bool:
        return not result
        
    return result


def __negateType(node):
    """
    Negates the value inside a not-type
    """

    child = node[0]
    
    if child.type == "false":
        return "true"
    elif child.type == "true":
        return "false"
    elif child.type == "number":
        if child.value == 0:
            return "true"
        else:
            return "false"
    elif child.type == "string":
        if len(child.value) > 0:
            return "false"
        else:
            return "true"
    else:
        return None


def __compareNodes(a, b):
    """
    This method compares two nodes from the tree regarding equality.
    It supports boolean, string and number type compares
    """

    firstType = a.type
    if firstType == "not":
        firstType = __negateType(a)

    secondType = b.type
    if secondType == "not":
        secondType = __negateType(b)
    
    if firstType == secondType:
        if firstType in ("string", "number"):
            return a.value == b.value
        elif firstType == "true":
            return True
        elif secondType == "false":
            return False    
            
    elif firstType in ("true", "false") and secondType in ("true", "false"):
        return False

    return None


