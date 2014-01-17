#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
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
    Console.debug("Processed %s selectors", modified)
    Console.outdent()

    return modified



def processMixins(tree):
    """
    Processes all mixin includes inside mixins
    """

    Console.info("Merging mixins with each other...")
    Console.indent()
    modified = __process(tree, scanMixins=True)
    Console.debug("Merged %s mixins", modified)
    Console.outdent()

    return modified



def processSelectors(tree):
    """
    Processes all mixin includes inside selectors
    """

    Console.info("Merging mixins into selectors")
    Console.indent()
    modified = __process(tree, scanMixins=False)
    Console.debug("Merged %s mixins", modified)
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

        selector, media = Util.combineSelector(node.parent, stop=mixin.parent)

        if media:
            Console.warn("Extending inside media query behaves like including (less efficient): %s + %s", media, ", ".join(selector))

            replacements = __resolveMixin(mixin, None)

            Console.debug("Replacing call %s at line %s with mixin from line %s" % (name, node.line, replacements.line))

            # Reverse inject all children of that block
            # at the same position as the original call
            parent = node.parent
            pos = parent.index(node)
            parent.insertAll(pos, replacements)

        else:
            Console.debug("Extending selector of mixin by: %s", ", ".join(selector))

            if hasattr(mixin, "selector"):
                # We iterate from in inverse mode, so add new selectors to the front
                mixin.selector[0:0] = selector

            else:
                mixin.selector = selector

            virtualBlock = Node.Node(type="block")
            __extendContent(mixin.rules, node, virtualBlock, mixin)

            if len(virtualBlock) > 0:
                callSelector, callMedia = Util.combineSelector(node)

                if callSelector:
                    virtualSelector = Node.Node(type="selector")
                    virtualSelector.name = callSelector

                if callMedia:
                    virtualMedia = Node.Node(type="media")
                    virtualMedia.name = callMedia

                if callSelector:
                    virtualSelector.append(virtualBlock, "rules")
                elif callMedia:
                    virtualMedia.append(virtualBlock, "rules")

                if callMedia:
                    virtualTop = virtualMedia
                elif callSelector:
                    virtualTop = virtualSelector

                pos = mixin.parent.index(mixin)
                mixin.parent.insert(pos+1, virtualTop)

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

        __injectContent(replacements, node)

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


def __injectContent(node, call):
    """
    Inserts content section of call into prepared content area of mixin clone
    """

    for child in reversed(node):
        if child:
            __injectContent(child, call)

    if node.type == "content":
        if hasattr(call, "rules"):
            Console.debug("Inserting content section from call into mixin clone")
            node.parent.insertAllReplace(node, copy.deepcopy(call.rules))
        else:
            Console.debug("Removing unused content section from mixin clone")
            node.parent.remove(node)


def __extendContent(node, call, targetBlock, stopCombineAt):
    """
    Builds up a list of selector/mediaqueries to insert after the extend to produce
    the @content sections on the intended selectors.
    """

    for child in reversed(node):
        if child:
            __extendContent(child, call, targetBlock, stopCombineAt)

    if node.type == "content" and hasattr(call, "rules"):
        # Extends support @content as well. In this case we produce a new selector
        # which matches the position of the content section and append it after
        # the original extended mixin on return

        Console.debug("Inserting content section into new virtual selector")

        selector, media = Util.combineSelector(node, stop=stopCombineAt)

        selectorNode = Node.Node(type="selector")
        selectorNode.name = selector

        selectorNode.append(copy.deepcopy(call.rules), "rules")

        # Support media queries, too
        if media:
            mediaNode = Node.Node(type="media")
            mediaNode.name = media
            mediaNode.append(selectorNode)
            targetBlock.append(mediaNode)

        else:
            targetBlock.append(selectorNode)


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

            if param.type == "variable":
                paramAsDeclaration.name = param.name
            elif param.type == "assign" and param[0].type == "variable":
                paramAsDeclaration.name = param[0].name
            else:
                raise Exception("Unsupported param structure for mixin resolver at line %s! Expected type variable or assignment and got: %s!" % (mixin.line, param.type));

            # Copy over actual param value
            if len(params) > pos:
                paramAsDeclaration.append(copy.deepcopy(params[pos]), "initializer")
            elif param.type == "assign" and param[0].type == "variable":
                paramAsDeclaration.append(copy.deepcopy(param[1]), "initializer")

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


