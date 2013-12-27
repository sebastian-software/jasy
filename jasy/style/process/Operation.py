#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.style.Util as Util
import jasy.style.parse.Node as Node


class OperationError(Exception):
    def __init__(self, message, node):
        Exception.__init__(self, "Variable Error: %s for node type=%s in %s at line %s!" % (message, node.type, node.getFileName(), node.line))


def compute(first, second, parent=None, operator=None):

    # Fill gaps in empty arguments
    if parent is None and first.parent is second.parent:
        parent = first.parent

    if parent and operator is None:
        operator = parent.type

    if parent is None or operator is None:
        raise OperationError("Missing arguments for compute()", first)

    # Support for default set operator "?=" when variable was not defined before
    if first is None and operator == "questionmark":
        return second

    # Solve inner operations first
    if first.type in Util.ALL_OPERATORS:
        repl = compute(first[0], first[1], first, first.type)
        if repl is None:
            return
        else:
            first = repl

    if second.type in Util.ALL_OPERATORS:
        repl = compute(second[0], second[1], second, second.type)
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

            if operator in Util.COMPARE_OPERATORS:
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
                    raise OperationError("Unsupported unit combination for number comparison", parent)


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
                    raise OperationError("Unsupported number operation", parent)


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
                raise OperationError("Could not compute result from numbers of different units: %s vs %s" % (first.unit, second.unit), parent)

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
                raise OperationError("Unsupported string operation", parent)

        elif first.type == "list":
            if len(first) == len(second):
                repl = Node.Node(type="list")
                for pos, child in enumerate(first):
                    childRepl = compute(child, second[pos], parent, operator)
                    if childRepl is not None:
                        repl.append(childRepl)

                return repl

            else:
                raise OperationError("For list operations both lists have to have the same length!", parent)

        else:
            raise OperationError("Unsupported operation on %s" % first.type, parent)


    elif first.type == "list" and second.type != "list":
        repl = Node.Node(type="list")
        for child in first:
            childRepl = compute(child, second, parent, operator)
            if childRepl is not None:
                repl.append(childRepl)

        return repl


    elif first.type != "list" and second.type == "list":
        repl = Node.Node(type="list")
        for child in second:
            childRepl = compute(first, child, parent, operator)
            if childRepl is not None:
                repl.append(childRepl)

        return repl


    elif first.type == "string" or second.type == "string":
        repl = Node.Node(type="string")

        if operator == "plus":
            repl.value = str(first.value) + str(second.value)
            return repl
        else:
            raise OperationError("Unsupported string operation", parent)


    # Just handle when not both are null - equal condition is already done before
    elif first.type == "null" or second.type == "null":
        if operator == "eq":
            return Node.Node(type="false")
        elif operator == "ne":
            return Node.Node(type="true")
        elif operator in Util.MATH_OPERATORS:
            return Node.Node(type="null")
        else:
            raise OperationError("Unsupported operation on null type", parent)


    else:
        raise OperationError("Different types in operation: %s vs %s" % (first.type, second.type), parent)