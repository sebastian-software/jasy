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
        and/or making them CSS2 compatible (regarding structure)
        """

        process = node.type in ("selector", "mixin", "media", "supports")

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
            combinedSelector, combinedMedia, combinedSupports = Util.combineSelector(node)

            if node.type == "selector":
                node.name = combinedSelector
            elif node.type == "mixin":
                node.selector = combinedSelector
            elif node.type == "media":
                pass
            elif node.type == "supports":
                pass

            if (combinedMedia or combinedSupports) and node.type in ("selector", "mixin"):

                if combinedSupports:
                    # Dynamically create matching media query
                    supportsNode = Node.Node(None, "supports")
                    supportsNode.name = combinedSupports

                    supportsBlock = Node.Node(None, "block")
                    supportsNode.append(supportsBlock, "rules")

                    supportsBlock.append(node)
                    node = supportsNode

                if combinedMedia:
                    # Dynamically create matching media query
                    mediaNode = Node.Node(None, "media")
                    mediaNode.name = combinedMedia

                    mediaBlock = Node.Node(None, "block")
                    mediaNode.append(mediaBlock, "rules")

                    mediaBlock.append(node)
                    node = mediaNode

            elif node.type == "media" or node.type == "supports":
                # Insert direct properties into new selector block
                # Goal is to place in this structure: @media->@supports->selector

                # Update media query of found media queries as it might
                # contain more than the local one (e.g. queries in parent nodes)
                if node.type == "media":
                    node.name = combinedMedia

                # Update support query of found supports query as it might
                # contain more than the local one (e.g. queries in parent nodes)
                elif node.type == "supports":
                    node.name = combinedSupports

                # Create new selector node where we move all rules into
                selectorNode = Node.Node(None, "selector")
                selectorNode.name = combinedSelector

                selectorBlock = Node.Node(None, "block")
                selectorNode.append(selectorBlock, "rules")

                # Move all rules from local media/supports block into new selector block
                for nonSelectorChild in list(node.rules):
                    if nonSelectorChild:
                        selectorBlock.append(nonSelectorChild)

                if node.type == "supports" and combinedMedia:
                    # Dynamically create matching mediaquery node
                    mediaNode = Node.Node(None, "media")
                    mediaNode.name = combinedMedia

                    mediaBlock = Node.Node(None, "block")
                    mediaNode.append(mediaBlock, "rules")

                    # Replace current node with media node
                    node.parent.replace(node, mediaNode)

                    # Then append this node to the media node
                    mediaBlock.append(node)

                    # Selector should be placed inside this node
                    node.rules.append(selectorNode)

                    # Update node reference to new outer node for further processing
                    node = mediaNode

                elif node.type == "media" and combinedSupports:
                    # Dynamically create matching supports node
                    supportsNode = Node.Node(None, "supports")
                    supportsNode.name = combinedSupports

                    supportsBlock = Node.Node(None, "block")
                    supportsNode.append(supportsBlock, "rules")

                    # Move supports node into this node
                    node.rules.append(supportsNode)

                    # The supports block is the parent of the selector
                    supportsBlock.append(selectorNode)

                else:
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
            Console.debug("Cleaning up empty selector/mixin/@media/@supports at line %s" % node.line)
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

        elif node.type == "root" and len(node) == 0:
            Console.debug("Cleaning up left over @root at line %s" % node.line)
            node.parent.remove(node)




    def __combine(tree, top=True):
        """
        Combines follow up selector/media/supports nodes with the same name.
        """

        previousSelector = None
        previousMedia = None
        previousSupports = None

        # Work on a copy to be safe for remove situations during merges
        previousChild = None
        for child in list(tree):
            if not child:
                continue

            if child.type == "selector" or child.type == "mixin":
                if child.type == "selector":
                    thisSelector = child.name
                elif child.type == "mixin":
                    thisSelector = child.selector

                if thisSelector == previousSelector:
                    previousChild.rules.insertAll(None, child.rules)
                    tree.remove(child)
                    Console.debug("Combined selector of line %s into %s" % (child.line, previousChild.line))
                else:
                    previousChild = child

                previousSelector = thisSelector
                previousMedia = None
                previousSupports = None

            elif child.type == "media":
                if child.name == previousMedia:
                    previousChild.rules.insertAll(None, child.rules)
                    tree.remove(child)
                    Console.debug("Combined @media of line %s into %s" % (child.line, previousChild.line))
                else:
                    previousChild = child

                previousMedia = child.name
                previousSelector = None
                previousSupports = None

            elif child.type == "supports":
                if child.name == previousSupports:
                    previousChild.rules.insertAll(None, child.rules)
                    tree.remove(child)
                    Console.debug("Combined @supports of line %s into %s" % (child.line, previousChild.line))
                else:
                    previousChild = child

                previousSupports = child.name
                previousSelector = None
                previousMedia = None

            else:
                previousChild = None
                previousSelector = None
                previousSupports = None
                previousMedia = None


        # Re-run combiner inside all media queries.
        # Selectors in there are allowed and could be combined, too
        if top:
            for child in tree:
                if child and (child.type == "media" or child.type == "supports"):
                    __combine(child.rules, False)


    # Execute the different features in order
    dest = Node.Node(None, "sheet")
    __flatter(tree, dest)
    tree.insertAll(0, dest)

    __clean(tree)
    __combine(tree)

    Console.outdent()

    return


