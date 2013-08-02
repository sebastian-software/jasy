#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.style.Util as Util
import jasy.core.Console as Console 

def process(tree):

    insertIndex = 1
    Console.info("Flattening selectors...")

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
                selector = node.selector

            combined = Util.combineSelector(node)

            if node.type == "selector":
                node.name = combined
            else:
                node.selector = combined

            tree.insert(len(tree)-insertIndex, node)
            insertIndex += 1

    __flatter(tree)


