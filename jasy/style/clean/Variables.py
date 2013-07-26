
import copy
import jasy.style.parse.Node as Node
import jasy.core.Console as Console


def compute(tree):
    __computeRecurser(tree, None, {})    


def __computeValue(node, values):
    print("Computing type: %s", node.type, node)

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
        print("Same type: %s" % first.type)
        if first.type == "number":
            print(first, second)

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
                    raise Exception("Unsupported number operation: %s at %s" % (node.type, node.line))



                print("Number Artithmetic Result: ", repl)
                return repl

        elif first.type == "string":
            repl = Node.Node(type="string")

            if node.type == "plus":
                repl.value = first.value + second.value
            else:
                raise Exception("Unsupported string operation: %s at %s" % (node.type, node.line))

        else:
            raise Exception("Could not compute result from numbers of different units: %s vs %s at line %s" % (first.unit, second.unit, node.line))

    else:
        print("Different type: %s vs %s" % (first.type, second.type))



def __computeRecurser(node, scope, values):

    # Update scope of new block starts
    if hasattr(node, "scope"):
        print("New scope")
        
        scope = node.scope
        values = copy.copy(values)

        # Reset all local variables to None
        # which enforces not to keep values from outer scope
        for name in scope.modified:
            values[name] = None


    for child in node:
        if child is not None:
            __computeRecurser(child, scope, values)



    if node.type in ("plus", "minus", "mul", "div", "mod"):
        repl = __computeValue(node, values)
        if repl:
            print("Replacing with value!")
            node.parent.replace(node, repl)





    # Update values of variable
    if node.type == "declaration" and hasattr(node, "initializer"):
        print("Found declaration: %s = %s" % (node.name, node.initializer))
        values[node.name] = node.initializer


    # Replace variable with actual value
    if node.type == "variable":
        name = node.name
        if not name in values:
            raise Exception("Could not resolve variable %s at line %s", name, node.line)

        value = values[name]
        if value is None:
            Console.warn("Could not resolve %s at line %s", name, node.line)

        print("Resolve variable: %s to %s" % (name, values[name]))
        node.parent.replace(node, copy.deepcopy(values[name]))




