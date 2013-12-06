#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import copy, re
import jasy.style.parse.Node as Node
import jasy.core.Console as Console


builtin = set([
    # Colors
    "rgb",
    "rgba",
    "hsl",
    "hsb",

    # URLs
    "url",

    # Webfonts
    "format",

    # Transforms
    "matrix",
    "translate",
    "translateX",
    "translateY",
    "scale",
    "scaleX",
    "scaleY",
    "rotate",
    "skewX",
    "skewY",

    # 3D Transforms
    "matrix3d",
    "translate3d",
    "translateZ",
    "scale3d",
    "scaleZ",
    "rotate3d",
    "rotateX",
    "rotateY",
    "rotateZ",
    "perspective",

    # Gradients
    "linear-gradient",
    "radial-gradient",
    "repeating-linear-gradient",
    "repeating-radial-gradient"
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

        # Filter all built-in commands and all vendor prefixed ones
        if command in builtin or command.startswith("-"):
            return

        params = []
        for param in node.params:
            if param.type == "unary_minus":
                value = -param[0].value
            else:
                value = param.value

            params.append(value)

        # print("Looking for command: %s(%s)" % (command, ", ".join([str(param) for param in params])))
        result, restype = session.executeCommand(command, params)

        if restype == "px":
            repl = Node.Node(type="number")
            repl.value = result
            repl.unit = restype

        elif restype == "url":
            repl = Node.Node(type="identifier")
            repl.value = "url(%s)" % result

        elif restype == "number":
            repl = Node.Node(type="number")
            repl.value = result

        else:
            repl = Node.Node(type="identifier")
            repl.value = result

        node.parent.replace(node, repl)


