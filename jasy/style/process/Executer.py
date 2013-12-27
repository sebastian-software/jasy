#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import copy, re
import jasy.style.parse.Node as Node
import jasy.core.Console as Console


RE_INLINE_VARIABLE = re.compile("\$\{([a-zA-Z0-9\-_\.]+)\}")

MATH_OPERATORS = ("plus", "minus", "mul", "div", "mod")
COMPARE_OPERATORS = ("eq", "ne", "gt", "lt", "ge", "le")

ALL_OPERATORS = MATH_OPERATORS + COMPARE_OPERATORS


builtin = set([
    # Colors
    "rgb",
    "rgba",
    "hsl",
    "hsb",

    # URLs
    "url",

    # Webfonts
    "format",

    # Transforms
    "matrix",
    "translate",
    "translateX",
    "translateY",
    "scale",
    "scaleX",
    "scaleY",
    "rotate",
    "skewX",
    "skewY",

    # 3D Transforms
    "matrix3d",
    "translate3d",
    "translateZ",
    "scale3d",
    "scaleZ",
    "rotate3d",
    "rotateX",
    "rotateY",
    "rotateZ",
    "perspective",

    # Gradients
    "linear-gradient",
    "radial-gradient",
    "repeating-linear-gradient",
    "repeating-radial-gradient",

    # Transitions
    "steps"
])


class ExecuterError(Exception):
    def __init__(self, message, node):
        Exception.__init__(self, "Variable Error: %s for node type=%s in %s at line %s!" % (message, node.type, node.getFileName(), node.line))




def process(tree, session):
    __recurser(tree, tree.scope, {}, session)


def __recurser(node, scope, values, session):
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

        Console.info("Processing if-condition at %s", node.line)

        # Pre-process condition
        # We manually process each child in for if-types
        __recurser(node.condition, scope, values, session)

        # Named child "condition" might be replaced so assign variable not before
        conditionNode = node.condition

        if conditionNode.type == "true":
            resultValue = True
        elif conditionNode.type == "false" or conditionNode.type == "null":
            resultValue = False
        elif conditionNode.type in ("number", "string"):
            resultValue = bool(node.condition.value)
        else:
            raise Exception("Unresolved if-block with condition: %s" % conditionNode)

        # Process relevant part of the sub tree
        resultNode = None
        if resultValue is True:
            resultNode = node.thenPart
        elif resultValue is False and hasattr(node, "elsePart"):
            resultNode = node.elsePart

        if resultNode:
            # Fix missing processing of result node
            __recurser(resultNode, scope, values, session)

            # Finally replace if-node with result node
            node.parent.insertAllReplace(node, resultNode)

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
            __recurser(child, scope, values, session)


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

            repl = __computeOperation(values[name], init, node, node.assignOp, values)
            if repl is not None:
                values[name] = repl

        else:
            # Update internal variable mapping
            Console.debug("Update value of %s to %s" % (name, init))
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


    elif node.type == "system":
        command = node.name

        # Filter all built-in commands and all vendor prefixed ones
        if command in builtin or command.startswith("-"):
            return

        params = []
        for param in node.params:
            if param.type == "unary_minus":
                value = -param[0].value
            else:
                value = param.value

            params.append(value)

        # print("Looking for command: %s(%s)" % (command, ", ".join([str(param) for param in params])))
        result, restype = session.executeCommand(command, params)

        if restype == "px":
            repl = Node.Node(type="number")
            repl.value = result
            repl.unit = restype

        elif restype == "url":
            repl = Node.Node(type="identifier")
            repl.value = "url(%s)" % result

        elif restype == "number":
            repl = Node.Node(type="number")
            repl.value = result

        else:
            repl = Node.Node(type="identifier")
            repl.value = result

        node.parent.replace(node, repl)


    # Support typical operators
    elif node.type in ALL_OPERATORS:
        repl = __processOperator(node, values)
        if repl is not None:
            node.parent.replace(node, repl)


    # Not operator support
    elif node.type == "not":
        child = node[0]
        if child.type == "true":
            child.type = "false"
        elif child.type == "false" or child.type == "null":
            child.type = "true"
        else:
            raise ExecuterError("Could not apply not operator to non boolean variable", node)

        node.parent.replace(node, child)






def __processOperator(node, values):
    Console.debug("Process operator: %s", node.type)

    # Resolve first child of operation
    first = node[0]
    if first.type == "variable":
        first = values[first.name]

    # Resolve second child of operation
    second = node[1]
    if second.type == "variable":
        second = values[second.name]

    return __computeOperation(first, second, node, node.type, values)


def __computeOperation(first, second, parent, operator, values):

    # Support for default set operator "?=" when variable was not defined before
    if first is None and operator == "questionmark":
        return second

    # Solve inner operations first
    if first.type in ALL_OPERATORS:
        repl = __computeOperation(first[0], first[1], first, first.type, values)
        if repl is None:
            return
        else:
            first = repl

    if second.type in ALL_OPERATORS:
        repl = __computeOperation(second[0], second[1], second, second.type, values)
        if repl is None:
            return
        else:
            second = repl


    # Compare operation types
    if first.type == second.type:
        if first.type == "null":
            repl = Node.Node(type="true")
            return repl

        elif first.type == "number":
            firstUnit = getattr(first, "unit", None)
            secondUnit = getattr(second, "unit", None)

            if operator in COMPARE_OPERATORS:
                if firstUnit == secondUnit or firstUnit is None or secondUnit is None:
                    if operator == "eq":
                        if first.value == second.value:
                            return Node.Node(type="true")
                        else:
                            return Node.Node(type="false")

                    elif operator == "ne":
                        if first.value != second.value:
                            return Node.Node(type="true")
                        else:
                            return Node.Node(type="false")

                    elif operator == "gt":
                        if first.value > second.value:
                            return Node.Node(type="true")
                        else:
                            return Node.Node(type="false")

                    elif operator == "lt":
                        if first.value < second.value:
                            return Node.Node(type="true")
                        else:
                            return Node.Node(type="false")

                    elif operator == "ge":
                        if first.value >= second.value:
                            return Node.Node(type="true")
                        else:
                            return Node.Node(type="false")

                    elif operator == "le":
                        if first.value <= second.value:
                            return Node.Node(type="true")
                        else:
                            return Node.Node(type="false")

                else:
                    raise ExecuterError("Unsupported unit combination for number comparison", parent)


            elif firstUnit == secondUnit or firstUnit is None or secondUnit is None:
                if operator in MATH_OPERATORS:
                    repl = Node.Node(type="number")

                    if firstUnit is not None:
                        repl.unit = firstUnit
                    elif secondUnit is not None:
                        repl.unit = secondUnit

                    if operator == "plus":
                        repl.value = first.value + second.value
                    elif operator == "minus":
                        repl.value = first.value - second.value
                    elif operator == "mul":
                        repl.value = first.value * second.value
                    elif operator == "div":
                        repl.value = first.value / second.value
                    elif operator == "mod":
                        repl.value = first.value % second.value

                    return repl

                elif operator == "questionmark":
                    return first

                else:
                    raise ExecuterError("Unsupported number operation", parent)


            elif firstUnit == "%" or secondUnit == "%":

                if operator in ("mul", "div"):
                    repl = Node.Node(type="number")

                    if operator == "mul":
                        repl.value = first.value * second.value / 100
                    elif operator == "mul":
                        repl.value = first.value / second.value / 100

                    if firstUnit == "%":
                        repl.unit = secondUnit
                    else:
                        repl.unit = firstUnit

                    return repl

                else:
                    raise ExecuterError("Could not compute mixed percent operations for operators other than \"*\" and \"/\"", node)

            else:
                raise ExecuterError("Could not compute result from numbers of different units: %s vs %s" % (first.unit, second.unit), parent)

        elif first.type == "string":
            if operator == "plus":
                repl = Node.Node(type="string")
                repl.value = first.value + second.value
                return repl

            elif operator == "eq":
                if first.value == second.value:
                    return Node.Node(type="true")
                else:
                    return Node.Node(type="false")

            elif operator == "ne":
                if first.value != second.value:
                    return Node.Node(type="true")
                else:
                    return Node.Node(type="false")

            else:
                raise ExecuterError("Unsupported string operation", parent)

        elif first.type == "list":
            if len(first) == len(second):
                repl = Node.Node(type="list")
                for pos, child in enumerate(first):
                    childRepl = __computeOperation(child, second[pos], parent, operator, values)
                    if childRepl is not None:
                        repl.append(childRepl)

                return repl

            else:
                raise ExecuterError("For list operations both lists have to have the same length!", parent)

        # Wait for system calls executing first
        elif first.type == "system":
            return None

        else:
            raise ExecuterError("Unsupported operation on %s" % first.type, parent)


    elif first.type == "list" and second.type != "list":
        repl = Node.Node(type="list")
        for child in first:
            childRepl = __computeOperation(child, second, parent, operator, values)
            if childRepl is not None:
                repl.append(childRepl)

        return repl


    elif first.type != "list" and second.type == "list":
        repl = Node.Node(type="list")
        for child in second:
            childRepl = __computeOperation(first, child, parent, operator, values)
            if childRepl is not None:
                repl.append(childRepl)

        return repl


    elif first.type == "string" or second.type == "string":
        repl = Node.Node(type="string")

        if operator == "plus":
            repl.value = str(first.value) + str(second.value)
            return repl
        else:
            raise ExecuterError("Unsupported string operation", parent)


    # Waiting for system method execution
    elif first.type == "system" or second.type == "system":
        print("Waiting for system call...")
        return None


    # Just handle when not both are null - equal condition is already done before
    elif first.type == "null" or second.type == "null":
        if operator == "eq":
            return Node.Node(type="false")
        elif operator == "ne":
            return Node.Node(type="true")
        elif operator in MATH_OPERATORS:
            return Node.Node(type="null")
        else:
            raise ExecuterError("Unsupported operation on null type", parent)


    else:
        raise ExecuterError("Different types in operation: %s vs %s" % (first.type, second.type), parent)
