#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import copy, random, string
import jasy.core.Console as Console
import jasy.style.parse.Node as Node


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

    # Generate random prefix for variables and parameters
    chars = string.ascii_letters + string.digits
    prefix = ''.join(random.sample(chars*6, 6))

    # Data base of all local variable and parameter name mappings
    variables = {}

    # Generate full recursive clone of mixin rules
    clone = copy.deepcopy(mixin.rules)

    if hasattr(mixin, "params"):
        for pos, param in enumerate(mixin.params):
            variables[param.name] = "%s-%s" % (prefix, param.name)
            Console.info("Renaming variable: %s to %s", param.name, variables[param.name])

            # We have to copy over the parameter value as a local variable declaration
            paramAsDeclaration = Node.Node(type="declaration")
            paramAsDeclaration.name = variables[param.name]

            # Copy over actual param value
            if len(params) > pos:
                paramAsDeclaration.append(copy.deepcopy(params[pos]), "initializer")

            clone.insert(0, paramAsDeclaration)

    __renameRecurser(clone, variables, prefix)

    return clone


def __renameRecurser(node, variables, prefix):
    """

    """

    for child in node:
        if child is not None:
            __renameRecurser(child, variables, prefix)

    if node.type == "variable":
        # Dynamic assignment
        if not node.name in variables:
            Console.info("Renaming variable: %s to %s", node.name, variables[node.name])
            variables[node.name] = "%s-%s" % (prefix, node.name)

        node.name = variables[node.name]


