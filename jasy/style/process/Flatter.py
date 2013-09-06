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

        # Increase index position when reaching new child of tree
        if getattr(node, "parent", None) == tree:
            insertIndex += 1

        # Extended mixin
        if node.type in ("selector", "mixin", "media") and len(node.rules) > 0:
            combinedSelector, combinedMedia = Util.combineSelector(node)

            if node.type == "selector":
                node.name = combinedSelector
            elif node.type == "mixin":
                node.selector = combinedSelector
            elif node.type == "media":
                pass

            if node.type == "selector" or node.type == "mixin":
                if combinedMedia:
                    # Share same media element when possible
                    previousMedia = insertIndex > 0 and tree[insertIndex-1]
                    if previousMedia and previousMedia.name[0] == combinedMedia:
                        mediaBlock = previousMedia.rules
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

            elif node.type == "media":
                # Insert direct properties into new selector:block

                previousMedia = insertIndex > 0 and tree[insertIndex-1]

                selectorNode = Node.Node(None, "selector")
                selectorNode.name = combinedSelector

                selectorBlock = Node.Node(None, "block")
                selectorNode.append(selectorBlock, "rules")
                
                # Move all rules from local block into selector block
                for mediaChild in list(node.rules):
                    if mediaChild:
                        selectorBlock.append(mediaChild)

                # Then insert the newly created and filled selector block into the media node
                node.rules.append(selectorNode)

            # When node is not yet in the root tree, append it there
            # and correct insertIndex for next insertion
            if getattr(node, "parent", None) != tree:
                tree.insert(insertIndex, node)
                insertIndex += 1



    def __clean(node):
        """
        Removes all empty rules. Starting from inside out for a deep cleanup.
        """

        # Process children first
        for child in reversed(node):
            if child is not None:
                __clean(child)

        if hasattr(node, "rules") and len(node.rules) == 0:
            Console.debug("Cleaning up empty selector/mixin at line %s" % node.line)
            node.parent.remove(node)
            return



    def __combine(tree):
        """
        Combines follow up selector/media nodes with the same name.
        """

        previousSelector = None
        previousMedia = None

        # Work on a copy to be safe for remove situations during merges
        treecopy = list(tree)
        for pos, child in enumerate(treecopy):
            if not child:
                continue

            if child.type == "selector":
                if child.name == previousSelector:
                    previous = treecopy[pos-1]
                    previous.rules.insertAll(None, child.rules)
                    tree.remove(child)

                    Console.debug("Combined selector of line %s into %s" % (child.line, previous.line))

                previousSelector = child.name
                previousMedia = None

            elif child.type == "media":
                if child.name == previousMedia:
                    previous = treecopy[pos-1]
                    previous.rules.insertAll(None, child.rules)
                    tree.remove(child)

                    Console.debug("Combined media of line %s into %s" % (child.line, previous.line))

                previousMedia = child.name
                previousSelector = None


    __flatter(tree)
    __clean(tree)
    __combine(tree)

    Console.info("Flattended %s selectors", insertIndex-1)
    Console.outdent()

    return insertIndex > 1


