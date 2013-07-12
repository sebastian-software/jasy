#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

class Compressor:
    __semicolonSymbol = ";"
    __commaSymbol = ","
    

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


    #
    # Sheet Scope
    #

    def type_sheet(self, node):
        return self.__statements(node)


    def type__statements(self, node):
        return self.__statements(node)





    #
    # Helpers
    #
    
    def __statements(self, node):
        result = []
        for child in node:
            result.append(self.compress(child))

        return "".join(result)

