#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.style.Util as Util
import jasy.core.Console as Console 
import jasy.style.parse.Node as Node

def process(tree):
    """
    Flattens selectors to that `h1{ span{ ...` is merged into `h1 span{ ...` 
    """

    insertIndex = 0

    Console.info("Flattening selectors...")
    Console.indent()

    def __flatter(node):

        nonlocal insertIndex

        # Process children first
        for child in list(node):
            if child is not None:
                __flatter(child)

        if getattr(node, "parent", None) == tree:
            insertIndex += 1

        # Extended mixin
        if node.type in ("selector", "mixin") and len(node.rules) > 0:
            if node.type == "selector":
                selector = node.name
            else:
                try:
                    selector = node.selector
                except AttributeError:
                    # Seems like a mixin which is not used. Ignore it.
                    return

            combinedSelector, combinedMedia = Util.combineSelector(node)

            if node.type == "selector":
                node.name = combinedSelector
            else:
                node.selector = combinedSelector

            if combinedMedia:
                # Share same media element when possible
                currentMedia = insertIndex > 0 and tree[insertIndex-1]
                if currentMedia and currentMedia.name[0] == combinedMedia:
                    mediaBlock = currentMedia.rules
                    mediaBlock.append(node)
                    return

                else:
                    # Dynamically create matching media query
                    mediaNode = Node.Node(None, "media")
                    mediaNode.name = [combinedMedia]

                    mediaBlock = Node.Node(None, "block")
                    mediaNode.append(mediaBlock, "rules")
                    mediaBlock.append(node)

                    # Insert media query node instead of rule node to tree
                    node = mediaNode

            if getattr(node, "parent", None) != tree:
                tree.insert(insertIndex, node)
                insertIndex += 1



    def __clean(node):

        # Process children first
        for child in reversed(node):
            if child is not None:
                __clean(child)

        if hasattr(node, "rules") and len(node.rules) == 0:
            Console.debug("Cleaning up empty selector/mixin at line %s" % node.line)
            node.parent.remove(node)
            return                

    __flatter(tree)
    __clean(tree)

    Console.info("Flattended %s selectors", insertIndex-1)
    Console.outdent()

    return insertIndex > 1


