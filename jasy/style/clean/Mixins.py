#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import copy
import jasy.core.Console as Console


def processMixins(tree):

    Console.info("Merging mixins with each other...")
    Console.indent()
    modified = __process(tree, scanMixins=True)
    Console.outdent()

    return modified


def processSelectors(tree):

    Console.info("Merging mixins into selectors")
    Console.indent()
    modified = __process(tree, scanMixins=False)
    Console.outdent()

    return modified




def __findSelector(node):
    if node.type == "selector":
        return node

    if hasattr(node, "parent"):
        result = __findSelector(node.parent)
        if result:
            return result

    return None



def __process(node, scanMixins=False, active=None):
    """
    Recursively processes the given node.

    - scanMixins: Whether mixins or selectors should be processed (phase1 vs. phase2)
    - active: Whether replacements should happen
    """

    if active is None:
        active = not scanMixins

    for child in reversed(node):
        if child is not None:
            if child.type == "mixin":
                if scanMixins:
                    __process(child, scanMixins=scanMixins, active=True)

            else:
                # Only process non mixin childs
                __process(child, scanMixins=scanMixins, active=active)


    if active and node.type == "call":
        name = node.name

        # selector = __findSelector(node)
        mixin = __findMixin(node.parent, name)
        replacements = __resolveMixin(mixin, node.params)

        Console.info("Replacing call %s at line %s with mixin from line %s" % (name, node.line, replacements.line))

        # Reverse inject all children of that block
        # at the same position as the original call
        parent = node.parent
        pos = parent.index(node)
        for child in reversed(replacements):
            parent.insert(pos, child)

        # Finally remove original node
        parent.remove(node)

        return True



def __findMixin(node, name):
    """
    Reverse scanning loop-engine for figuring out first position of given mixin
    """

    for child in reversed(node):
        if child is not None:
            if child.type == "mixin" and child.name == name:
                return child

    return __findMixin(node.parent, name)



def __resolveMixin(mixin, params):
    """
    Returns a clone of the given mixin and applies optional parameters to it
    """

    # Map all parameters to a variables dict for easy lookup
    variables = {}
    for pos, param in enumerate(params):
        variables[mixin.params[pos].name] = param

    clone = copy.deepcopy(mixin.rules)

    if variables:
        __resolveRecurser(clone, variables)

    return clone


def __resolveRecurser(node, variables):
    """

    """

    for child in node:
        if child is not None:
            __resolveRecurser(child, variables)

    if node.type == "variable" and node.name in variables:
        node.parent.replace(node, copy.deepcopy(variables[node.name]))


