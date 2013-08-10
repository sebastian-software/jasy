#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import copy, random, string

import jasy.core.Console as Console
import jasy.style.parse.Node as Node
import jasy.style.Util as Util


def processExtends(tree):
    """
    Processes all requests for mixin extends
    """

    Console.info("Processing extend requests...")
    Console.indent()
    modified = __extend(tree)
    Console.info("Processed %s selectors", modified)
    Console.outdent()

    return modified



def processMixins(tree):
    """
    Processes all mixin includes inside mixins 
    """

    Console.info("Merging mixins with each other...")
    Console.indent()
    modified = __process(tree, scanMixins=True)
    Console.info("Merged %s mixins", modified)
    Console.outdent()

    return modified



def processSelectors(tree):
    """
    Processes all mixin includes inside selectors
    """

    Console.info("Merging mixins into selectors")
    Console.indent()
    modified = __process(tree, scanMixins=False)
    Console.info("Merged %s mixins", modified)
    Console.outdent()

    return modified



def isExtendCall(node):
    return (node.type == "call" and (not hasattr(node, "params") or len(node.params) == 0)) or (node.type == "variable" and node.parent.type == "block")



def isMixinCall(node):
    return (node.type == "call" or (node.type == "variable" and node.parent.type == "block"))



def __extend(node, scanMixins=False):
    """
    Finds extend requests for mixins aka 

    - mixins calls without params
    - simple variables in a block

    For all found extend requests it detects the flattened selector and appends 
    the selector section of the extendable mixin accordingly. After that it 
    removes the original mixin request.
    """

    modified = 0

    for child in reversed(node):
        # Ignore all mixin declarations. Can't operate inside them.
        # For these things to work we have to wait for the include mechanics to resolve them first 
        # (which actually just remove these mixin declarations though)
        if child is not None and (scanMixins or child.type != "mixin"):
            modified += __extend(child)

    if isExtendCall(node):

        name = node.name

        Console.debug("Extend request to mixin %s at: %s", name, node.line)
        Console.indent()

        mixin = __findMixin(node.parent, name)
        if not mixin:
            raise Exception("Could not find mixin %s as required by extend request at line %s" % (node.name, node.line))

        Console.debug("Found matching mixin declaration at line: %s", mixin.line)

        selector = Util.combineSelector(node.parent)
        Console.debug("Extending selector of mixin by: %s", selector)

        if hasattr(mixin, "selector"):
            # We iterate from in inverse mode, so add new selectors to the front
            mixin.selector[0:0] = selector

        else:
            mixin.selector = selector

        node.parent.remove(node)
        Console.outdent()

        modified += 1

    return modified



def __process(node, scanMixins=False, active=None):
    """
    Recursively processes the given node.

    - scanMixins: Whether mixins or selectors should be processed (phase1 vs. phase2)
    - active: Whether replacements should happen
    """

    modified = 0

    if active is None:
        active = not scanMixins

    for child in reversed(node):
        if child is not None:
            if child.type == "mixin":
                if scanMixins:
                    modified += __process(child, scanMixins=scanMixins, active=True)

            else:
                # Only process non mixin childs
                modified += __process(child, scanMixins=scanMixins, active=active)

    if active and isMixinCall(node) and not isExtendCall(node):
        name = node.name

        mixin = __findMixin(node.parent, name)
        replacements = __resolveMixin(mixin, getattr(node, "params", None))

        Console.debug("Replacing call %s at line %s with mixin from line %s" % (name, node.line, replacements.line))

        # Reverse inject all children of that block
        # at the same position as the original call
        parent = node.parent
        pos = parent.index(node)
        for child in reversed(replacements):
            parent.insert(pos, child)

        # Finally remove original node
        parent.remove(node)

        modified += 1

    return modified



def __findMixin(node, name):
    """
    Reverse scanning loop-engine for figuring out first position of given mixin
    """

    for child in reversed(node):
        if child is not None:
            # Sheets are just fragments with a special origin, 
            # but otherwise the content is valid on the same level
            # as other siblings of the sheet.
            if child.type == "sheet":
                for subChild in reversed(child):
                    if subChild is not None:
                        if subChild.type == "mixin" and subChild.name == name:
                            return subChild

            elif child.type == "mixin" and child.name == name:
                return child

    parent = getattr(node, "parent", None)
    if parent:
        return __findMixin(parent, name)
    else:
        return None



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
            Console.debug("Renaming variable: %s to %s at line %s", node.name, variables[node.name], node.line)

        node.name = variables[node.name]

    # Access variable
    elif node.type == "variable" and node.name in variables:
        node.name = variables[node.name]        

