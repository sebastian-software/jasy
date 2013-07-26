
import copy
import jasy.style.parse.Node as Node


def compute(tree):

    def __computeValue(node, values):
        print("Computing type: %s", node.type, node)

        if node.type in ("number", "string", "boolean"):
            return node

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
                        raise Exception("Unsupported math operation: %s at %s" % (node.type, node.line))



                    print("Number Artithmetic Result: ", repl)
                    return repl

            else:
                raise Exception("Could not compute result from numbers of different units: %s vs %s at line %s" % (first.unit, second.unit, node.line))

        else:
            print("Different type: %s vs %s" % (first.type, second.type))



        # Fallback logic
        return node


    def __computeRecurser(node, scope, values):
        if hasattr(node, "scope"):
            scope = node.scope
            values = copy.copy(values)

            # Reset all local variables to None
            # which enforces not to keep values from outer scope
            for name in scope.modified:
                values[name] = None


        if node.type == "declaration" and hasattr(node, "initializer"):
            values[node.name] = __computeValue(node.initializer, values)



        if node.type == "variable":
            name = node.name
            if not name in values:
                raise Exception("Could not resolve variable %s at line %s", name, node.line)

            value = values[name]
            if value is None:
                Console.warn("Could not resolve %s at line %s", name, node.line)

            node.parent.replace(node, copy.deepcopy(values[name]))




        for child in node:
            if child is not None:
                __computeRecurser(child, scope, values)



    __computeRecurser(tree, None, {})    