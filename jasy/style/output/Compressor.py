#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import json, re
import itertools

__all__ = [ "Compressor" ]

high_unicode = re.compile(r"\\u[2-9A-Fa-f][0-9A-Fa-f]{3}")
ascii_encoder = json.JSONEncoder(ensure_ascii=True)
unicode_encoder = json.JSONEncoder(ensure_ascii=False)

class Compressor:
    __semicolonSymbol = ";"
    __commaSymbol = ","
    __useIndenting = True
    __useBlockBreaks = True
    __useStatementBreaks = True
    __useWhiteSpace = True

    __indentLevel = 0


    __simple = ["true", "false", "null"]

    __dividers = {
        "plus"        : '+',
        "minus"       : '-',
        "mul"         : '*',
        "div"         : '/',
        "mod"         : '%',
        "dot"         : '.',
        "or"          : "||",
        "and"         : "&&",
        "strict_eq"   : '===',
        "eq"          : '==',
        "strict_ne"   : '!==',
        "ne"          : '!=',
        "lsh"         : '<<',
        "le"          : '<=',
        "lt"          : '<',
        "ursh"        : '>>>',
        "rsh"         : '>>',
        "ge"          : '>=',
        "gt"          : '>',
        "bitwise_or"  : '|',
        "bitwise_xor" : '^',
        "bitwise_and" : '&'
    }

    __prefixes = {    
        "increment"   : "++",
        "decrement"   : "--",
        "bitwise_not" : '~',
        "not"         : "!",
        "unary_plus"  : "+",
        "unary_minus" : "-",
        "delete"      : "delete ",
        "new"         : "new ",
        "typeof"      : "typeof ",
        "void"        : "void "
    }



    def __init__(self, format=None):
        if format:
            if format.has("indent"):
                self.__useIndenting = True

            if format.has("semicolon"):
                self.__semicolonSymbol = ";\n"
            
            if format.has("comma"):
                self.__commaSymbol = ",\n"
            
        self.__forcedSemicolon = False



    def compress(self, node):
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
            except KeyError:
                print("Compressor does not support type '%s' from line %s in file %s" % (type, node.line, node.getFileName()))
                sys.exit(1)

        return result


    def indent(self, code):

        if not self.__useIndenting:
            return code

        lines = code.split("\n")
        result = []
        prefix = self.__indentLevel * "  "

        for line in lines:
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
        # Omit writing real high unicode character which are not supported well by browsers
        ascii = ascii_encoder.encode(node.value)

        if high_unicode.search(ascii):
            return ascii
        else:
            return unicode_encoder.encode(node.value)


    def type_number(self, node):
        value = node.value

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


    def type_declaration(self, node):
        return self.indent("ERROR-DECLARATION-%s;" % node.name)

    def type_variable(self, node):
        return "$ERROR-VAR-%s" % node.name

    def type_mixin(self, node):
        # Filter out non-extend mixins
        if not getattr(node, "selector"):
            return self.indent("$ERROR-MIXIN-%s;" % node.name)

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
            result += "{\n%s\n}\n" % inner
        else:
            result += "{%s}" % inner

        return result





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
            result.append(self.compress(child))

        return " ".join(result)




