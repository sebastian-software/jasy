#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

"""
This class is responsible for resolving if-conditions based on permutation data
Not all if blocks are being able to be resolved that way though as some use
variables etc. which are not available before actual full processing of the content.
"""

import jasy.style.process.Operation as Operation
import jasy.style.Util as Util
import jasy.core.Console as Console


class ResolverError(Exception):
    def __init__(self, message, node=None):
        if node:
            Exception.__init__(self, "Resolver Error: %s in node \"%s\" in file \"%s\" at line %s!" % (message, node.type, node.getFileName(), node.line))
        else:
            Exception.__init__(self, "Resolver Error: %s!" % message)


def patch(tree, permutation):
    __recurser(tree, permutation)



#
# Implementation
#

def __recurser(node, permutation, inCondition=False):

    # Support block commands
    # These come with their own node.type
    if node.type == "if":

        # Pre-process condition
        # We manually process each child in for if-types
        __recurser(node.condition, permutation, True)

        # Cast condition to Python boolean type
        resultValue = None
        try:
            resultValue = Operation.castToBool(node.condition)
        except Operation.OperationError as ex:
            Console.debug("Walked into unprocessed condition. Waiting for actual execution. Message: %s", ex)

        if not resultValue is None:

            # Process relevant part of the sub tree
            if resultValue is True:
                # Fix missing processing of result node
                __recurser(node.thenPart, permutation)

                # Finally replace if-node with result node
                node.parent.replace(node, node.thenPart)

            elif resultValue is False and hasattr(node, "elsePart"):
                # Fix missing processing of result node
                __recurser(node.elsePart, permutation)

                # Finally replace if-node with result node
                node.parent.replace(node, node.elsePart)

            else:
                # Cleanup original if-node
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

        repl = Util.castNativeToNode(permutation.get(node.value))
        node.parent.replace(node, repl)


    # Support inline @field() commands
    elif node.type == "command" and node.name == "field":
        if len(node.params) == 0:
            raise ResolverError("Missing parameter to insert field via @field.", node)

        identifierNode = node.params[0]
        if identifierNode.type != "identifier":
            raise ResolverError("Invalid parameter to @field call: %s" % identifierNode.type, identifierNode)

        identifier = identifierNode.value
        if not permutation.has(identifier):
            raise ResolverError("Could not find field with the name %s" % identifier, identifierNode)

        repl = Util.castNativeToNode(permutation.get(identifier))
        node.parent.replace(node, repl)


    # Support typical operators
    elif node.type in Util.ALL_OPERATORS:
        repl = Operation.compute(node)
        if repl is not None:
            node.parent.replace(node, repl)

