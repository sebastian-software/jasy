#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import json, re, sys
import jasy.style.Util as Util

ascii_encoder = json.JSONEncoder(ensure_ascii=True)


class CompressorError(Exception):
    def __init__(self, message, node):
        Exception.__init__(self, "Compressor Error: %s for node type=%s in %s at line %s!" % (message, node.type, node.getFileName(), node.line))


class Compressor:
    __useIndenting = False
    __useBlockBreaks = False
    __useStatementBreaks = False
    __useWhiteSpace = False

    __indentLevel = 0


    __simple = ["true", "false", "null"]

    __dividers = {
        "plus"        : '+',
        "minus"       : '-',
        "mul"         : '*',
        "div"         : '/',
        "mod"         : '%',
        "dot"         : '.',
        "eq"          : '==',
        "ne"          : '!=',
        "le"          : '<=',
        "lt"          : '<',
        "ge"          : '>=',
        "gt"          : '>'
    }

    __prefixes = {
        "unary_plus"  : "+",
        "unary_minus" : "-"
    }



    def __init__(self, format=None):
        if format:
            if format.has("indent"):
                self.__useIndenting = True

            if format.has("blocks"):
                self.__useBlockBreaks = True

            if format.has("statements"):
                self.__useStatementBreaks = True

            if format.has("whitespace"):
                self.__useWhiteSpace = True


    def compress(self, node):
        """
        Compresses the given node and returns the compressed text result
        """

        type = node.type

        if type in self.__simple:
            result = type
        elif type in self.__prefixes:
            if getattr(node, "postfix", False):
                result = self.compress(node[0]) + self.__prefixes[node.type]
            else:
                result = self.__prefixes[node.type] + self.compress(node[0])

        elif type in self.__dividers:
            first = self.compress(node[0])
            second = self.compress(node[1])
            divider = self.__dividers[node.type]

            # Fast path
            if node.type not in ("plus", "minus"):
                result = "%s%s%s" % (first, divider, second)

            # Special code for dealing with situations like x + ++y and y-- - x
            else:
                result = first
                if first.endswith(divider):
                    result += " "

                result += divider

                if second.startswith(divider):
                    result += " "

                result += second

        else:
            try:
                result = getattr(self, "type_%s" % type)(node)
            except AttributeError:
                raise Exception("Style compressor does not support type '%s' from line %s in file %s" % (type, node.line, node.getFileName()))

        return result


    def indent(self, code):
        """
        Indents the given code by the current indenting setup
        """

        if not self.__useIndenting:
            return code

        lines = code.split("\n")
        result = []
        prefix = self.__indentLevel * "  "

        for line in lines:
            if line:
                result.append("%s%s" % (prefix, line))

        return "\n".join(result)





    #
    # Sheet Scope
    #

    def type_sheet(self, node):
        return self.__statements(node)


    def type_selector(self, node):
        # Ignore selectors without rules
        if len(node.rules) == 0:
            return ""

        selector = node.name

        if self.__useBlockBreaks:
            result = ",\n".join(selector)
        elif self.__useWhiteSpace:
            result = ", ".join(selector)
        else:
            result = ",".join(selector)

        return self.indent("%s%s" % (result, self.compress(node.rules)))


    def type_string(self, node):
        if hasattr(node, "quote"):
            return "%s%s%s" % (node.quote, node.value, node.quote)
        else:
            return ascii_encoder.encode(node.value)


    def type_number(self, node):
        value = node.value

        # Apply basic rounding to reduce size overhead of floating point
        if type(value) is float and not hasattr(node, "precision"):
            value = round(value, 4)

        # Special handling for protected float/exponential
        if type(value) == str:
            # Convert zero-prefix
            if value.startswith("0.") and len(value) > 2:
                value = value[1:]

            # Convert zero postfix
            elif value.endswith(".0"):
                value = value[:-2]

        elif int(value) == value and node.parent.type != "dot":
            value = int(value)

        return "%s%s" % (value, getattr(node, "unit", ""))


    def type_identifier(self, node):
        return node.value


    def type_slash(self, node):
        return "/"


    def type_expr(self, node):
        child = node[0]
        return self.compress(child)


    def type_raw(self, node):
        child = node[0]
        result = self.compress(child)

        # Remove string quotes
        if child.type == "string":
            result = result[1:-1]

        return result


    def type_list(self, node):
        return " ".join([ self.compress(child) for child in node ])


    def type_comma(self, node):
        first = self.compress(node[0])
        second = self.compress(node[1])
        if self.__useWhiteSpace:
            res = "%s, %s"
        else:
            res = "%s,%s"

        return res % (first, second)


    def type_block(self, node):
        self.__indentLevel += 1
        inner = self.__statements(node)
        self.__indentLevel -= 1

        if self.__useBlockBreaks:
            return "{\n%s\n}\n" % inner
        else:
            return "{%s}" % inner


    def type_property(self, node):
        self.__indentLevel += 1
        inner = self.__values(node)
        self.__indentLevel -= 1

        if self.__useWhiteSpace:
            return self.indent("%s: %s;" % (node.name, inner))
        else:
            return self.indent("%s:%s;" % (node.name, inner))


    def type_call(self, node):
        params = []
        callParams = getattr(node, "params", None)
        if callParams:
            for paramNode in callParams:
                params.append(self.compress(paramNode))

        if self.__useWhiteSpace:
            paramsJoin = ", "
        else:
            paramsJoin = ","

        return "%s(%s)" % (node[0].value, paramsJoin.join(params))


    def type_mixin(self, node):
        # Filter out non-extend mixins
        if not hasattr(node, "selector"):
            raise CompressorError("Left mixin \"%s\" found in tree to compress" % node.name, node)

        selector = node.selector

        if self.__useBlockBreaks:
            result = ",\n".join(selector)
        elif self.__useWhiteSpace:
            result = ", ".join(selector)
        else:
            result = ",".join(selector)

        self.__indentLevel += 1
        inner = self.__statements(node.rules)
        self.__indentLevel -= 1

        if self.__useBlockBreaks:
            result += "{\n%s\n}" % inner
        else:
            result += "{%s}" % inner

        return result


    def type_function(self, node):
        name = node.name

        if self.__useWhiteSpace:
            separator = ", "
        else:
            separator = ","

        return "%s(%s)" % (name, separator.join([ self.compress(child) for child in node.params ]))


    def type_keyframes(self, node):
        vendor = getattr(node, "vendor", None)
        if vendor:
            result = "@-%s-keyframes " % vendor
        else:
            result = "@keyframes "

        result += "%s{" % node.name

        if self.__useBlockBreaks:
            result += "\n"

        self.__indentLevel += 1

        frames = "".join([ self.compress(child) for child in node ])
        result += self.indent(frames)

        self.__indentLevel -= 1

        if self.__useBlockBreaks:
            result += "\n"

        result += "}"

        return result


    def type_frame(self, node):
        result = ""

        if self.__useWhiteSpace:
            result += node.value.replace(",", ", ")
        else:
            result += node.value

        result += self.compress(node.rules)

        return result


    def type_media(self, node):
        if self.__useBlockBreaks:
            separator = ",\n"
        elif self.__useWhiteSpace:
            separator = ", "
        else:
            separator = ","

        result = "@media %s" % separator.join(node.name)
        result += self.compress(node.rules)

        return self.indent(result)


    def type_fontface(self, node):
        result = "@font-face" + self.compress(node.rules)

        return self.indent(result)



    #
    # Helpers
    #

    def __statements(self, node):
        result = []
        for child in node:
            result.append(self.compress(child))

        if self.__useStatementBreaks:
            return "\n".join(result)
        else:
            return "".join(result)


    def __values(self, node):
        result = []
        for child in node:
            result.append(str(self.compress(child)))

        return " ".join(result)




