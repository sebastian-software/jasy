#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import copy, re
import jasy.style.parse.Node as Node
import jasy.core.Console as Console


builtin = set([
    "rgb",
    "rgba",
    "hsl",
    "hsb",
    "url",
    "format"
])


class MethodError(Exception):
    def __init__(self, message, node):
        Exception.__init__(self, "Method Error: %s for node type=%s in %s at line %s!" % (message, node.type, node.getFileName(), node.line))


def execute(tree, session):
    if session is None:
        return

    Console.info("Executing methods...")
    Console.indent()

    __executeRecurser(tree, session)

    Console.outdent()


def __executeRecurser(node, session):

    # Worked on copy to prevent issues during length changes (due removing/adding children, etc.)
    for child in list(node):
        if child is not None:
            __executeRecurser(child, session)


    if node.type == "system":
        command = node.name

        if command in builtin:
            return

        params = [ param.value for param in node.params ]

        # print("Looking for command: %s(%s)" % (command, ", ".join([str(param) for param in params])))
        result = session.executeCommand(command, params)
        # print("Result: %s" % result)

        repl = Node.Node(type="identifier")
        repl.value = result

        node.parent.replace(node, repl)


