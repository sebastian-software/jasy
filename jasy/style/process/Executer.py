#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

"""

"""

import copy, re
import jasy.style.parse.Node as Node
import jasy.core.Console as Console


RE_INLINE_VARIABLE = re.compile("\$\{([a-zA-Z0-9\-_\.]+)\}")

MATH_OPERATORS = ("plus", "minus", "mul", "div", "mod")
COMPARE_OPERATORS = ("eq", "ne", "gt", "lt", "ge", "le")

ALL_OPERATORS = MATH_OPERATORS + COMPARE_OPERATORS


def process(tree):
    __recurser(tree, {})


def __recurser(node, values):
    print("PROCESS: %s from %s" % (node.type, node.line))




    # Replace variable with actual value
    if node.type == "variable" and not (node.parent.type == "assign" and node.parent[0] is node):
        name = node.name
        if not name in values:
            raise VariableError("Could not resolve variable %s! Missing value!" % name, node)

        value = values[name]
        if value is None:
            raise VariableError("Could not resolve variable %s! Value is none!" % name, node)

        Console.debug("Resolving variable: %s at line %s with %s from %s", name, node.line, values[name].type, values[name].line)
        node.parent.replace(node, copy.deepcopy(values[name]))




    for child in list(node):
        # Ignore non-children... through possible interactive structure changes
        if child and child.parent is node:
            __recurser(child, values)

    # Update values of variable
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
                raise VariableError("Assign operator is not supported as left hand variable is missing: %s" % name, node)

            repl = __computeOperation(values[name], init, node, node.assignOp, values)
            if repl is not None:
                values[name] = repl

        else:
            # Update internal variable mapping
            Console.debug("Update value of %s to %s" % (name, init))
            values[name] = init

        # Remove declaration node from tree
        node.parent.remove(node)



    elif node.type in ("property", "selector") and getattr(node, "dynamic", False):
        def replacer(matchObj):
            name = matchObj.group(1)

            if not name in values:
                raise VariableError("Could not resolve variable %s! Missing value!" % name, node)

            value = values[name]
            if value is None:
                raise VariableError("Could not resolve variable %s! Value is none!" % name, node)

            if value.type == "identifier":
                return value.value
            elif value.type == "string":
                return value.value
            elif value.type == "number":
                return "%s%s" % (value.value, getattr(value, "unit", ""))
            else:
                raise VariableError("Could not replace property inline variable with value of type: %s" % value.type, node)

        # Fix all selectors
        if node.type == "selector":
            selectors = node.name
            for pos, selector in enumerate(selectors):
                selectors[pos] = RE_INLINE_VARIABLE.sub(replacer, selector)

        else:
            node.name = RE_INLINE_VARIABLE.sub(replacer, node.name)

