#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.style.Util as Util
import jasy.core.Console as Console 

def process(tree):

    return
    values = {}

    recurser(tree, values)


def recurser(node, values, inCondition=False):

    print("TYPE: %s, REL: %s" % (node.type, getattr(node, "rel", None)))

    for child in reversed(node):
        if child is not None:
            recurser(child, values, inCondition or getattr(child, "rel", None) == "condition")

    if inCondition:
        print("NODE IN CONDITION: %s" % node.type)

        if node.type == "identifier":
            print("Looking up: %s" % node.value)
            value = values[node.value]
            print("Replace with: %s" % value)



    if node.type == "if":
        print("Found IF: ", node)


