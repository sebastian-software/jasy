#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import copy, re

import jasy.style.parse.Node as Node
import jasy.style.process.Operation as Operation
import jasy.style.Util as Util
import jasy.core.Console as Console


class ExecuterError(Exception):
    def __init__(self, message, node):
        Exception.__init__(self, "Variable Error: %s for node type=%s in %s at line %s!" % (message, node.type, node.getFileName(), node.line))


def process(tree, profile):
    __recurser(tree, tree.scope, {}, profile)





#
# Implementation
#

RE_INLINE_VARIABLE = re.compile("\$\{([a-zA-Z0-9\-_\.]+)\}")

def __recurser(node, scope, values, profile):
    # Replace variable with actual value
    if node.type == "variable" and not (node.parent.type == "assign" and node.parent[0] is node):
        name = node.name
        if not name in values:
            raise ExecuterError("Could not resolve variable %s! Missing value!" % name, node)

        value = values[name]
        if value is None:
            raise ExecuterError("Could not resolve variable %s! Value is none!" % name, node)

        Console.debug("Resolving variable: %s at line %s with %s from %s", name, node.line, values[name].type, values[name].line)
        node.parent.replace(node, copy.deepcopy(values[name]))


    # Decide which sub tree of an if-condition is relevant based on current variable situation
    elif node.type == "if":

        Console.debug("Processing if-condition at %s", node.line)

        # Pre-process condition
        # We manually process each child in for if-types
        __recurser(node.condition, scope, values, profile)

        # Cast condition to Python boolean type
        resultValue = Operation.castToBool(node.condition)

        # Process relevant part of the sub tree
        if resultValue is True:
            # Fix missing processing of result node
            __recurser(node.thenPart, scope, values, profile)

            # Finally replace if-node with result node
            node.parent.replace(node, node.thenPart)

        elif resultValue is False and hasattr(node, "elsePart"):
            # Fix missing processing of result node
            __recurser(node.elsePart, scope, values, profile)

            # Finally replace if-node with result node
            node.parent.replace(node, node.elsePart)

        else:
            # Cleanup original if-node
            node.parent.remove(node)

        # Nothing to do here as content is already processed
        return


    # Update scope of new block starts
    if hasattr(node, "scope"):
        relation = getattr(node, "rel", None)

        # Conditional blocks are not exactly blocks in this variable resolution engine
        if not relation in ("thenPart", "elsePart"):
            scope = node.scope
            values = copy.copy(values)
            node.values = values

            # Reset all local variables to None
            # which enforces not to keep values from outer scope
            for name in scope.modified:
                values[name] = None


    # Process children / content
    for child in list(node):
        # Ignore non-children... through possible interactive structure changes
        if child and child.parent is node:
            __recurser(child, scope, values, profile)


    # Update values of variables
    # This happens after processing children to possibly reduce child structure to an easy to assign (aka preprocessed value)
    if (node.type == "declaration" and hasattr(node, "initializer")) or node.type == "assign":

        if node.type == "declaration":
            name = node.name
            init = node.initializer
            Console.debug("Found declaration of %s at line %s", name, node.line)

        else:
            name = node[0].name
            init = node[1]
            Console.debug("Found assignment of %s at line %s", name, node.line)

        # Modify value instead of replace when assign operator is set
        if hasattr(node, "assignOp") and node.assignOp is not None:
            if not name in values:
                raise ExecuterError("Assign operator is not supported as left hand variable is missing: %s" % name, node)

            repl = Operation.compute(node, values[name], init, node.assignOp)
            if repl is not None:
                values[name] = repl

        else:
            # Update internal variable mapping
            # Console.debug("Update value of %s to %s" % (name, init))
            values[name] = init

        # Remove declaration node from tree
        node.parent.remove(node)


    # Support for variables inside property names or selectors
    elif node.type in ("property", "selector") and getattr(node, "dynamic", False):
        def replacer(matchObj):
            name = matchObj.group(1)

            if not name in values:
                raise ExecuterError("Could not resolve variable %s! Missing value!" % name, node)

            value = values[name]
            if value is None:
                raise ExecuterError("Could not resolve variable %s! Value is none!" % name, node)

            if value.type == "identifier":
                return value.value
            elif value.type == "string":
                return value.value
            elif value.type == "number":
                return "%s%s" % (value.value, getattr(value, "unit", ""))
            else:
                raise ExecuterError("Could not replace property inline variable with value of type: %s" % value.type, node)

        # Fix all selectors
        if node.type == "selector":
            selectors = node.name
            for pos, selector in enumerate(selectors):
                selectors[pos] = RE_INLINE_VARIABLE.sub(replacer, selector)

        else:
            node.name = RE_INLINE_VARIABLE.sub(replacer, node.name)


    # Execute system commands
    elif node.type == "command":
        repl = Util.executeCommand(node, profile)
        if not repl is node:
            node.parent.replace(node, repl)


    # Support typical operators
    elif node.type in Util.ALL_OPERATORS:
        repl = Operation.compute(node)
        if repl is not None:
            node.parent.replace(node, repl)

