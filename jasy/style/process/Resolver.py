#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

"""
This class is responsible for resolving if-conditions based on permutation data
Not all if blocks are being able to be resolved that way though as some use
variables etc. which are not available before actual full processing of the content.
"""

import jasy.style.parse.Node as Node
import jasy.style.process.Operation as Operation
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

    # Support block commands
    # These come with their own node.type
    if node.type == "if":
        __recurser(node.condition, permutation, True)

        resultValue = Operation.castToBool(node.condition)
        if resultValue:
            __recurser(node.thenPart, permutation)
            node.parent.insertAllReplace(node, node.thenPart)
        elif hasattr(node, "elsePart"):
            __recurser(node.elsePart, permutation)
            node.parent.insertAllReplace(node, node.elsePart)
        else:
            node.parent.remove(node)

        # All done including child nodes
        return


    # Process children first (resolve logic is inner-out)
    for child in list(node):
        if child is not None:
            __recurser(child, permutation, inCondition)


    # Inside of conditions replace identifiers with their actual value (from current permutation)
    if inCondition and node.type == "identifier":
        if not permutation.has(node.value):
            raise ResolverError("Could not find field %s" % node.value, node)

        repl = __transform(permutation.get(node.value), node.value)
        node.parent.replace(node, repl)


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


    # Support typical operators
    elif node.type in Util.ALL_OPERATORS:
        repl = Operation.compute(node)
        if repl is not None:
            node.parent.replace(node, repl)

