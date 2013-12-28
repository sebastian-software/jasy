#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.style.Util as Util
import jasy.style.parse.Node as Node


class OperationError(Exception):
    def __init__(self, message, node):
        Exception.__init__(self, "Variable Error: %s for node type=%s in %s at line %s!" % (message, node.type, node.getFileName(), node.line))


def castToBool(node):
    """
    Returns the boolean Python representation for the given Node
    """

    if node.type == "false" or node.type == "null":
        return False
    elif node.type == "true":
        return True
    elif node.type == "number":
        return node.value != 0
    elif node.type == "string":
        return len(node.value) > 0
    else:
        raise OperationError("Could not cast node to boolean value", node)


def compute(node, first=None, second=None, operator=None, session=None):
    """
    Recursively processes given operation node.
    Consumes optional hints for the first/second child of an operation as
    well as the operator itself (in cases where it could not be figured out
    automatically). The session is useful for supporting commands
    inside of operations.
    """

    # Fill gaps in empty arguments
    if operator is None:
        operator = node.type

    # Fill missing first/second param
    if first is None and len(node) >= 1:
        first = node[0]

    if second is None and len(node) >= 2:
        second = node[1]

    # Error handling
    if node is None or operator is None:
        raise OperationError("Missing arguments for operation compute()", node)

    # Solve inner operations first
    if first is not None:
        if first.type in Util.ALL_OPERATORS:
            first = compute(first, session=session)
        elif first.type == "command":
            first = Util.executeCommand(first, session)

    if second is not None:
        if second.type in Util.ALL_OPERATORS:
            second = compute(second, session=session)
        elif second.type == "command":
            second = Util.executeCommand(second, session)

    # Support for not-/and-/or-operator
    if operator == "not":
        return Util.castNativeToNode(not castToBool(first))
    elif operator == "and":
        return Util.castNativeToNode(castToBool(first) and castToBool(second))
    elif operator == "or":
        return Util.castNativeToNode(castToBool(first) or castToBool(second))

    # Support for default set operator "?=" when variable was not defined before
    elif operator == "questionmark" and first is None:
        return second


    # Ignore when not yet processed
    if first.type in ("command", "variable") or second.type in ("command", "variable"):
        return

    # Compare operation types
    elif first.type == second.type:
        if first.type in ("true", "false", "null"):
            if operator in ("eq", "ge", "le"):
                return Util.castNativeToNode(True)
            else:
                return Util.castNativeToNode(False)

        elif first.type == "number":
            firstUnit = getattr(first, "unit", None)
            secondUnit = getattr(second, "unit", None)

            if operator in Util.COMPARE_OPERATORS:
                if firstUnit == secondUnit or firstUnit is None or secondUnit is None:
                    if operator == "eq":
                        return Util.castNativeToNode(first.value == second.value)
                    elif operator == "ne":
                        return Util.castNativeToNode(first.value != second.value)
                    elif operator == "gt":
                        return Util.castNativeToNode(first.value > second.value)
                    elif operator == "lt":
                        return Util.castNativeToNode(first.value < second.value)
                    elif operator == "ge":
                        return Util.castNativeToNode(first.value >= second.value)
                    elif operator == "le":
                        return Util.castNativeToNode(first.value <= second.value)

                else:
                    raise OperationError("Unsupported unit combination for number comparison", node)


            elif firstUnit == secondUnit or firstUnit is None or secondUnit is None:
                if operator in Util.MATH_OPERATORS:
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
                    raise OperationError("Unsupported number operation", node)


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
                    raise OperationError("Could not compute mixed percent operations for operators other than \"*\" and \"/\"", node)

            else:
                raise OperationError("Could not compute result from numbers of different units: %s vs %s" % (first.unit, second.unit), node)


        elif first.type == "string":
            if operator == "plus":
                repl = Node.Node(type="string")
                repl.value = first.value + second.value
                return repl

            elif operator == "eq":
                return Util.castNativeToNode(first.value == second.value)
            elif operator == "ne":
                return Util.castNativeToNode(first.value != second.value)
            else:
                raise OperationError("Unsupported string operation", node)


        elif first.type == "list":
            if len(first) == len(second):
                repl = Node.Node(type="list")
                for pos, child in enumerate(first):
                    childRepl = compute(node, first=child, second=second[pos], session=session)
                    if childRepl is not None:
                        repl.append(childRepl)

                return repl

            else:
                raise OperationError("For list operations both lists have to have the same length!", node)


        else:
            raise OperationError("Unsupported operation on %s" % first.type, node)


    elif first.type == "true" and second.type == "false":
        return Util.castNativeToNode(False)


    elif first.type == "false" and second.type == "true":
        return Util.castNativeToNode(False)


    elif first.type == "list" and second.type != "list":
        repl = Node.Node(type="list")
        for child in first:
            childRepl = compute(node, first=child, second=second, session=session)
            if childRepl is not None:
                repl.append(childRepl)

        return repl


    elif first.type != "list" and second.type == "list":
        repl = Node.Node(type="list")
        for child in second:
            childRepl = compute(node, first=first, second=child, session=session)
            if childRepl is not None:
                repl.append(childRepl)

        return repl


    elif first.type == "string" or second.type == "string":
        repl = Node.Node(type="string")

        if operator == "plus":
            repl.value = str(first.value) + str(second.value)
            return repl
        else:
            raise OperationError("Unsupported string operation", node)


    # Just handle when not both are null - equal condition is already done before
    elif first.type == "null" or second.type == "null":
        if operator == "eq":
            return Util.castNativeToNode(False)
        elif operator == "ne":
            return Util.castNativeToNode(True)
        elif operator in Util.MATH_OPERATORS:
            return Util.castNativeToNode(None)
        else:
            raise OperationError("Unsupported operation on null type", node)


    else:
        raise OperationError("Different types in operation: %s vs %s" % (first.type, second.type), node)

