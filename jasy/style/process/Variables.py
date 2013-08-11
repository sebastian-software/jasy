
import copy
import jasy.style.parse.Node as Node
import jasy.core.Console as Console


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

    # Compare operation types
    if first.type == second.type:
        # Console.debug("Same type: %s", first.type)

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
                else:
                    raise VariableError("Unsupported number operation", parent)

                return repl

            else:
                raise VariableError("Could not compute result from numbers of different units: %s vs %s" % (first.unit, second.unit), parent)

        elif first.type == "string":
            repl = Node.Node(type="string")

            if operator == "plus":
                repl.value = first.value + second.value
                return repl
            else:
                raise VariableError("Unsupported string operation", parent)

        else:
            raise VariableError("Unsupported operation", parent)

    else:
        Console.debug("TODO: Different type: %s vs %s", first.type, second.type)



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
            raise VariableError("Got no valid return value to replace operation.", node)

    # Update values of variable
    elif node.type == "declaration" and hasattr(node, "initializer"):
        Console.debug("Found declaration of %s at line %s", node.name, node.line)

        # Modify value instead of replace when assign operator is set
        if hasattr(node, "assignOp") and node.assignOp is not None:
            if not node.name in values:
                raise VariableError("Assign operator is not supported as left hand variable is missing: %s" % node.name, node)

            repl = __computeOperation(values[node.name], node.initializer, node, node.assignOp, values)
            if repl:
                values[node.name] = repl
            else:
                raise VariableError("Got no valid return value to replace operation.", node)

        else:        
            # Update internal variable mapping
            values[node.name] = node.initializer

        # Remove declaration node from tree
        node.parent.remove(node)

    # Replace variable with actual value
    elif node.type == "variable":
        name = node.name
        if not name in values:
            raise VariableError("Could not resolve variable %s" % name, node)

        value = values[name]
        if value is None:
            raise VariableError("Could not resolve variable %s" % name, node)

        Console.debug("Resolving variable: %s at line %s with %s from %s", name, node.line, values[name].type, values[name].line)
        node.parent.replace(node, copy.deepcopy(values[name]))


