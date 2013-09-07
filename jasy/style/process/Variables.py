#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import copy, re
import jasy.style.parse.Node as Node
import jasy.core.Console as Console


RE_INLINE_VARIABLE = re.compile("\$\{([a-zA-Z0-9\-_\.]+)\}")


class VariableError(Exception):
    def __init__(self, message, node):
        Exception.__init__(self, "Variable Error: %s for node type=%s in %s at line %s!" % (message, node.type, node.getFileName(), node.line))


def compute(tree):
    Console.info("Resolving variables...")
    Console.indent()

    __computeRecurser(tree, None, {})

    Console.outdent()


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

    # Compare operation types
    if first.type == second.type:
        # print("Same type: %s" % first.type)

        if first.type == "number":
            firstUnit = getattr(first, "unit", None)
            secondUnit = getattr(second, "unit", None)

            if firstUnit == secondUnit or firstUnit is None or secondUnit is None:
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
                elif operator == "questionmark":
                    return first
                else:
                    raise VariableError("Unsupported number operation", parent)

                return repl

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
                    raise VariableError("Could not compute mixed percent operations for operators other than \"*\" and \"/\"", node)

            else:
                raise VariableError("Could not compute result from numbers of different units: %s vs %s" % (first.unit, second.unit), parent)

        elif first.type == "string":
            repl = Node.Node(type="string")

            if operator == "plus":
                repl.value = first.value + second.value
                return repl
            else:
                raise VariableError("Unsupported string operation", parent)

        elif first.type == "list":
            if len(first) == len(second):
                repl = Node.Node(type="list")
                for pos, child in enumerate(first):
                    childRepl = __computeOperation(child, second[pos], parent, operator, values)
                    if childRepl is None:
                        raise VariableError("Got no valid return value to replace operation", child)

                    repl.append(childRepl)

                return repl                

            else:
                raise VariableError("For list operations both lists have to have the same length!", parent)

        else:
            raise VariableError("Unsupported operation", parent)


    elif first.type == "list" and second.type != "list":
        repl = Node.Node(type="list")
        for child in first:
            childRepl = __computeOperation(child, second, parent, operator, values)
            if childRepl is None:
                raise VariableError("Got no valid return value to replace operation", child)

            repl.append(childRepl)

        return repl
 

    elif first.type != "list" and second.type == "list":
        repl = Node.Node(type="list")
        for child in second:
            childRepl = __computeOperation(first, child, parent, operator, values)
            if childRepl is None:
                raise VariableError("Got no valid return value to replace operation", child)

            repl.append(childRepl)

        return repl


    elif first.type == "string" or second.type == "string":
        repl = Node.Node(type="string")

        if operator == "plus":
            repl.value = str(first.value) + str(second.value)
            return repl
        else:
            raise VariableError("Unsupported string operation", parent)

    else:
        raise VariableError("Different types in operation: %s vs %s" % (first.type, second.type), parent)



def __computeRecurser(node, scope, values):

    # Update scope of new block starts
    if hasattr(node, "scope"):
        scope = node.scope
        values = copy.copy(values)

        # Reset all local variables to None
        # which enforces not to keep values from outer scope
        for name in scope.modified:
            values[name] = None

    # Worked on copy to prevent issues during length changes (due removing declarations, etc.)
    for child in list(node):
        if child is not None:
            __computeRecurser(child, scope, values)

    # Support typical operators
    if node.type in ("plus", "minus", "mul", "div", "mod"):
        repl = __processOperator(node, values)
        if repl:
            node.parent.replace(node, repl)
        else:
            raise VariableError("Got no valid return value to replace operation", node)


    # Not operator support
    elif node.type == "not":
        child = node[0]
        if child.type == "true":
            child.type = "false"
        elif child.type == "false":
            child.type = "true"
        else:
            raise VariableError("Could not apply not operator to non boolean variable", node)

        node.parent.replace(node, child)


    # Update values of variable
    elif (node.type == "declaration" and hasattr(node, "initializer")) or node.type == "assign":
        
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
            if repl:
                values[name] = repl
            else:
                raise VariableError("Got no valid return value to replace operation", node)

        else:        
            # Update internal variable mapping
            values[name] = init

        # Remove declaration node from tree
        node.parent.remove(node)


    # Replace variable with actual value
    elif node.type == "variable" and not (node.parent.type == "assign" and node.parent[0] is node):
        name = node.name
        if not name in values:
            raise VariableError("Could not resolve variable %s! Missing value!" % name, node)

        value = values[name]
        if value is None:
            raise VariableError("Could not resolve variable %s! Value is none!" % name, node)

        Console.debug("Resolving variable: %s at line %s with %s from %s", name, node.line, values[name].type, values[name].line)
        node.parent.replace(node, copy.deepcopy(values[name]))


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



