#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.style.Util as Util
import jasy.core.Console as Console 

def process(tree):
    """
    Flattens selectors to that `h1{ span{ ...` is merged into `h1 span{ ...` 
    """

    insertIndex = 1
    Console.info("Flattening selectors...")
    Console.indent()

    def __flatter(node):

        nonlocal insertIndex

        # Process children first
        for child in reversed(node):
            if child is not None:
                __flatter(child)


        # Extended mixin
        if node.type == "selector" or node.type == "mixin":
            if len(node.rules) == 0:
                Console.debug("Cleaning up empty selector/mixin at line %s" % node.line)
                node.parent.remove(node)
                return

            if node.type == "selector":
                selector = node.name
            else:
                try:
                    selector = node.selector
                except AttributeError:
                    # Seems like a mixin which is not used. Ignore it.
                    return

            combined = Util.combineSelector(node)

            if node.type == "selector":
                node.name = combined
            else:
                node.selector = combined

            tree.insert(len(tree)-insertIndex, node)
            insertIndex += 1

    __flatter(tree)

    Console.info("Flattended %s selectors", insertIndex-1)
    Console.outdent()

    return insertIndex > 1


