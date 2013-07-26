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


    if active and node.type == "call" or (node.type == "variable" and node.parent.type == "block"):
        name = node.name

        mixin = __findMixin(node.parent, name)
        replacements = __resolveMixin(mixin, getattr(node, "params", None))

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
            # We have to copy over the parameter value as a local variable declaration
            paramAsDeclaration = Node.Node(type="declaration")
            paramAsDeclaration.name = param.name

            # Copy over actual param value
            if len(params) > pos:
                paramAsDeclaration.append(copy.deepcopy(params[pos]), "initializer")

            clone.insert(0, paramAsDeclaration)

    __renameRecurser(clone, variables, prefix)

    return clone



def __renameRecurser(node, variables, prefix):
    """
    Resursive engine to rename all local variables to prefixed ones for protecting
    the scope of the mixin vs. the place it is injected to.
    """

    for child in node:
        if child is not None:
            __renameRecurser(child, variables, prefix)

    # Set variable
    if node.type == "declaration":
        if not node.name in variables:
            variables[node.name] = "%s-%s" % (prefix, node.name)
            Console.info("Renaming variable: %s to %s at line %s", node.name, variables[node.name], node.line)

        node.name = variables[node.name]

    # Access variable
    elif node.type == "variable" and node.name in variables:
        node.name = variables[node.name]        


