#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import jasy.style.Util as Util
import jasy.core.Console as Console
import jasy.style.parse.Node as Node

def process(tree):
    """
    Flattens selectors to that `h1{ span{ ...` is merged into `h1 span{ ...`
    """

    Console.info("Flattening selectors...")
    Console.indent()

    def __flatter(node, dest):
        """
        Moves all selectors to the top tree node while keeping media queries intact
        and/or making them CSS2 compatible (regarding formatting)
        """

        process = node.type in ("selector", "mixin", "media")

        # Insert all children of top-level nodes into a helper element first
        # This is required to place mixins first, before the current node and append
        # all remaining nodes afterwards
        if process:
            chdest = Node.Node(None, "helper")
        else:
            chdest = dest

        # Process children first
        if len(node) > 0:
            for child in list(node):
                if child is not None:
                    __flatter(child, chdest)

        # Filter out empty nodes from processing
        if process and hasattr(node, "rules") and len(node.rules) > 0:

            # Combine selector and/or media query
            combinedSelector, combinedMedia = Util.combineSelector(node)

            if node.type == "selector":
                node.name = combinedSelector
            elif node.type == "mixin":
                node.selector = combinedSelector
            elif node.type == "media":
                pass

            if combinedMedia and node.type in ("selector", "mixin"):
                # Dynamically create matching media query
                mediaNode = Node.Node(None, "media")
                mediaNode.name = [combinedMedia]

                mediaBlock = Node.Node(None, "block")
                mediaNode.append(mediaBlock, "rules")

                mediaBlock.append(node)
                node = mediaNode


            elif node.type == "media":
                # Insert direct properties into new selector:block

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


        if process:

            # Place any mixins before the current node
            for child in list(chdest):
                if child.type == "mixin":
                    dest.append(child)

            # The append self
            dest.append(node)

            # Afterwards append any children
            for child in list(chdest):
                dest.append(child)




    def __clean(node):
        """
        Removes all empty rules. Starting from inside out for a deep cleanup.
        This is a required step for the next one where we combine media queries
        and selectors and need to have an easy reference point to the previous node.
        """

        # Process children first
        for child in reversed(node):
            if child is not None:
                __clean(child)

        if hasattr(node, "rules") and len(node.rules) == 0:
            Console.debug("Cleaning up empty selector/mixin at line %s" % node.line)
            node.parent.remove(node)

        elif node.type == "content":
            Console.debug("Cleaning up left over @content at line %s" % node.line)
            node.parent.remove(node)

        elif node.type == "meta":
            Console.debug("Cleaning up left over @meta at line %s" % node.line)
            node.parent.remove(node)

        elif node.type == "block" and node.parent.type in ("sheet", "block"):
            Console.debug("Inlining content of unnecessary block node at line %s" % node.line)
            node.parent.insertAllReplace(node, node)



    def __combine(tree, top=True):
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


        # Re-run combiner inside all media queries.
        # Selectors in there are allowed and could be combined, too
        if top:
            for child in tree:
                if child and child.type == "media":
                    __combine(child.rules, False)


    # Execute the different features in order
    dest = Node.Node(None, "sheet")
    __flatter(tree, dest)
    tree.insertAll(0, dest)

    __clean(tree)
    __combine(tree)

    Console.outdent()

    return


