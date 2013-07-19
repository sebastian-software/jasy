#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import copy

def process(tree):
    __process(tree)




def __process(node):
    for child in reversed(node):
        if child is not None:
            __process(child)


    if node.type == "call":
        name = node.name

        print("FOUND CALL:")
        print(node)

        mixin = __finder(node.parent, name)

        print("FOUND MIXIN:")
        print(mixin)

        replacement = __resolve(mixin, node.params)

        print("REPLACEMENT:")
        print(replacement)

        # Reverse inject all children of that block
        # at the same position as the original call
        pos = node.index(call)
        for child in reversed(replacement):
            node.insert(child, pos)



def __finder(node, name):
    """
    Reverse scanning loop-engine for figuring out first position of given mixin
    """

    for child in reversed(node):
        if child is not None:
            if child.type == "mixin" and child.name == name:
                return child

    return __finder(node.parent, name)




def __resolve(mixin, params):

    # Map all parameters to a variables dict for easy lookup
    variables = {}
    for pos, param in enumerate(params):
        variables[mixin.params[pos].name] = param

    clone = copy.deepcopy(mixin.rules)

    if variables:
        __resolveRecurser(clone, variables)

    return clone




def __resolveRecurser(node, variables):

    for child in node:
        if child is not None:
            __resolveRecurser(child, variables)



    if node.type == "variable" and node.name in variables:
        node.parent.replace(node, copy.deepcopy(variables[node.name]))






