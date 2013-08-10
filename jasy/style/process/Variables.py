
import copy
import jasy.style.parse.Node as Node
import jasy.core.Console as Console


class VariableError(Exception):
    def __init__(self, message, node):
        Exception.__init__(self, "Variable Error: %s for node type=%s in %s at line %s" % (message, node.type, node.getFileName(), node.line))


def compute(tree):
    Console.info("Resolving variables...")
    Console.indent()

    __computeRecurser(tree, None, {})

    Console.outdent()


def __computeOperation(node, values):
    Console.debug("Computing operation: %s", node.type)

    # Resolve first child of operation
    first = node[0]
    if first.type == "variable":
        first = values[first.name]

    # Resolve second child of operation
    second = node[1]
    if second.type == "variable":
        second = values[second.name]

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

                if node.type == "plus":
                    repl.value = first.value + second.value
                elif node.type == "minus":
                    repl.value = first.value - second.value
                elif node.type == "mul":
                    repl.value = first.value * second.value
                elif node.type == "div":
                    repl.value = first.value / second.value
                elif node.type == "mod":
                    repl.value = first.value % second.value
                else:
                    raise VariableError("Unsupported number operation", node)

                return repl

            else:
                raise VariableError("Could not compute result from numbers of different units: %s vs %s" % (first.unit, second.unit), node)

        elif first.type == "string":
            repl = Node.Node(type="string")

            if node.type == "plus":
                repl.value = first.value + second.value
            else:
                raise VariableError("Unsupported string operation", node)

        else:
            raise VariableError("Unsupported operation", node)

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
        repl = __computeOperation(node, values)
        if repl:
            node.parent.replace(node, repl)
        else:
            Console.error("Got no valid return value to replace operation at line: %s", node.line)

    # Update values of variable
    elif node.type == "declaration" and hasattr(node, "initializer"):
        Console.debug("Found declaration of %s at line %s", node.name, node.line)
        
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
            Console.warn("Could not resolve %s at line %s", name, node.line)
            return

        Console.debug("Resolving variable: %s at line %s with %s from %s", name, node.line, values[name].type, values[name].line)
        node.parent.replace(node, copy.deepcopy(values[name]))


