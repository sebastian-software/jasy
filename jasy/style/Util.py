#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import itertools, re
import jasy.style.parse.Node as Node

RE_ENGINE_PROPERTY = re.compile(r"^(?:\-(apple|chrome|moz|ms|o|webkit)\-)?([a-z\-]+)$")

MATH_OPERATORS = ("plus", "minus", "mul", "div", "mod")
COMPARE_OPERATORS = ("eq", "ne", "gt", "lt", "ge", "le")
LOGIC_OPERATORS = ("not", "and", "or")

ALL_OPERATORS = MATH_OPERATORS + COMPARE_OPERATORS + LOGIC_OPERATORS


def extractVendor(name):
    match = RE_ENGINE_PROPERTY.match(name)
    if match:
        return match.group(1)


def extractName(name):
    match = RE_ENGINE_PROPERTY.match(name)
    if match:
        return match.group(2)
    else:
        return name


def executeCommand(node, profile):
    command = node.name

    params = []
    for param in node.params:
        # Variable not yet processed (possible e.g. during permutation apply)
        if param.type == "variable":
            return node
        elif param.type == "unary_minus":
            value = -param[0].value
        else:
            value = param.value

        params.append(value)

    # print("Looking for command: %s(%s)" % (command, ", ".join([str(param) for param in params])))
    result, restype = profile.executeCommand(command, params)

    if restype == "px":
        repl = Node.Node(type="number")
        repl.value = result
        repl.unit = restype

    elif restype == "url":
        repl = Node.Node(type="function")
        repl.name = "url"
        listChild = Node.Node(type="list")
        repl.append(listChild, "params")
        valueChild = Node.Node(type="identifier")
        valueChild.value = result
        listChild.append(valueChild)

    elif restype == "number":
        repl = Node.Node(type="number")
        repl.value = result

    else:
        repl = Node.Node(type="identifier")
        repl.value = result

    return repl


def assembleDot(node, result=None):
    """
    Joins a dot node (cascaded supported, too) into a single string like "foo.bar.Baz"
    """

    if result == None:
        result = []

    for child in node:
        if child.type == "identifier":
            result.append(child.value)
        elif child.type == "dot":
            assembleDot(child, result)
        else:
            return None

    return ".".join(result)


def castNativeToNode(value):
    if value is True:
        node = Node.Node(type="true")
    elif value is False:
        node = Node.Node(type="false")
    elif isinstance(value, str):
        node = Node.Node(type="string")
        node.value = value
    elif isinstance(value, (float, int)):
        node = Node.Node(type="number")
        node.value = value
    elif value is None:
        node = Node.Node(type="null")
    else:
        raise ResolverError("Could not transform field %s=%s to style value" % (name, value))

    return node


def combineSelector(node, stop=None):
    """
    Figures out the fully qualified selector of the given Node
    """

    # Fast path and fix for identical start/stop
    if node is stop:
        return ["&"], None

    selector = []
    media = []

    # Selector and media lists are in reversed order...
    current = node
    while current and current is not stop:
        if current.type == "selector":
            selector.append(current.name)
        elif current.type == "mixin":
            selector.append(current.selector)
        elif current.type == "media":
            media.append(current.name)

        current = getattr(current, "parent", None)

    if not selector and not media:
        raise Exception("Node %s at line %s is not a selector/mixin/mediaquery and is no child of any selector/mixin/mediaquery." % (node.type, node.line))

    # So we process collected selector data in reversed order, too, to get the normal order back
    combinedSelectors = []
    for item in itertools.product(*reversed(selector)):
        combined = ""
        for part in item:
            if combined:
                if "&" in part:
                    combined = part.replace("&", combined)
                else:
                    combined = "%s %s" % (combined, part)
            else:
                # Tolerate open/unsolvable "&" parent reference when we stop too early
                if not stop and "&" in part:
                    raise Exception("Can't merge selector %s - parent missing - at line %s!" % (part, node.line))
                else:
                    combined = part

        combinedSelectors.append(combined)

    if media:
        # Use compact format when possible
        if len(media) > 1:
            # So we join collected media data in reversed order, too, to get the normal order back
            combinedMedia = "(%s)" % ")and(".join(query[0] for query in reversed(media))
        else:
            combinedMedia = media[0][0]
    else:
        combinedMedia = None

    return combinedSelectors, combinedMedia

