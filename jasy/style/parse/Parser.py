#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import re, json

import jasy.style.tokenize.Tokenizer as Tokenizer
import jasy.style.parse.Node as Node
import jasy.style.Util as Util

ascii_encoder = json.JSONEncoder(ensure_ascii=True)


RE_SELECTOR_SPLIT = re.compile(r"\s*,\s*")


def parseExpression(source, fileId=None, line=1):
    # Convert source into expression statement to be friendly to the Tokenizer
    if not source.endswith(";"):
        source = source + ";"

    tokenizer = Tokenizer.Tokenizer(source, fileId, line)
    staticContext = StaticContext()

    return Expression(tokenizer, staticContext)


def parse(source, fileId=None, line=1):
    tokenizer = Tokenizer.Tokenizer(source, fileId, line)
    staticContext = StaticContext()
    node = Sheet(tokenizer, staticContext)

    # store fileId on top-level node
    node.fileId = tokenizer.fileId

    # add missing comments e.g. empty file with only a comment etc.
    # if there is something non-attached by an inner node it is attached to
    # the top level node, which is not correct, but might be better than
    # just ignoring the comment after all.
    if len(node) > 0:
        addComments(node[-1], None, tokenizer.getComments())
    else:
        addComments(node, None, tokenizer.getComments())

    if not tokenizer.done():
        raise SyntaxError("Unexpected end of file", tokenizer)

    return node



class SyntaxError(Exception):
    def __init__(self, message, tokenizer):
        Exception.__init__(self, "Syntax error: %s\n%s at line %s" % (message, tokenizer.fileId, tokenizer.line))



# Used as a status container during tree-building for every def body and the global body
class StaticContext(object):
    def __init__(self):
        self.blockId = 0
        self.statementStack = []



def Sheet(tokenizer, staticContext):
    """Parses the toplevel and rule bodies."""
    node = Statements(tokenizer, staticContext)

    # change type from "block" to "sheet" for style root
    node.type = "sheet"

    return node



def Statements(tokenizer, staticContext):
    """Parses a list of Statements."""

    node = Node.Node(tokenizer, "block")
    staticContext.blockId += 1
    staticContext.statementStack.append(node)

    prevNode = None
    while not tokenizer.done() and tokenizer.peek(True) != "right_curly":
        comments = tokenizer.getComments()
        childNode = Statement(tokenizer, staticContext)

        # Ignore semicolons in AST
        if childNode.type != "semicolon":
            node.append(childNode)

        prevNode = childNode

    staticContext.statementStack.pop()

    return node



def Block(tokenizer, staticContext):
    tokenizer.mustMatch("left_curly")
    node = Statements(tokenizer, staticContext)
    tokenizer.mustMatch("right_curly")

    return node



def Statement(tokenizer, staticContext):
    """Parses a Statement."""

    tokenType = tokenizer.get(True)
    tokenValue = getattr(tokenizer.token, "value", "")


    if tokenType == "left_curly":
        node = Statements(tokenizer, staticContext)
        tokenizer.mustMatch("right_curly")
        return node


    elif tokenType == "command":

        if tokenValue == "if" or tokenValue == "elif":
            node = Node.Node(tokenizer, "if")
            node.append(Expression(tokenizer, staticContext), "condition")
            staticContext.statementStack.append(node)
            thenPart = Statement(tokenizer, staticContext)
            thenPart.noscope = True
            node.append(thenPart, "thenPart")

            if tokenizer.match("command"):
                elseTokenValue = tokenizer.token.value
                if elseTokenValue == "elif":

                    # Process like an "if" and append as elsePart
                    tokenizer.unget()
                    elsePart = Statement(tokenizer, staticContext)
                    elsePart.noscope = True
                    node.append(elsePart, "elsePart")

                if elseTokenValue == "else":
                    comments = tokenizer.getComments()
                    elsePart = Statement(tokenizer, staticContext)
                    elsePart.noscope = True
                    addComments(elsePart, node, comments)
                    node.append(elsePart, "elsePart")

            staticContext.statementStack.pop()

            return node

        elif tokenValue == "content":
            node = Node.Node(tokenizer, "content")
            return node

        elif tokenValue == "include":
            node = Node.Node(tokenizer, "include")
            node.append(Expression(tokenizer, staticContext))
            return node

        elif tokenValue in ("require", "load", "break", "asset"):
            node = Node.Node(tokenizer, "meta")
            node.name = tokenValue
            node.append(Expression(tokenizer, staticContext))
            return node

        elif tokenValue == "font-face":
            return FontFace(tokenizer, staticContext)

        # Special case: Support keyframe command with engine prefix
        elif tokenValue == "keyframes" or tokenValue.endswith("-keyframes"):
            return KeyFrames(tokenizer, staticContext)

        elif tokenValue == "media":
            return Media(tokenizer, staticContext)

        else:
            raise SyntaxError("Unknown system command: %s" % tokenValue, tokenizer)


    elif tokenType == "identifier" or tokenType == "mul":

        if tokenType == "identifier":
            nextTokenType = tokenizer.peek()

            # e.g. jasy.gradient() or gradient() - process them as expressions
            # native calls in these places result in full property or multiple full properties
            if nextTokenType == "left_paren":
                tokenizer.unget()
                node = Expression(tokenizer, staticContext)
                return node

        # It's hard to differentiate between selectors and properties.
        # The strategy is to look for these next symbols as they define if the tokens
        # until then are either a selector or property declaration.
        nextRelevantTokenType = tokenizer.find(("semicolon", "left_curly", "right_curly"))

        # e.g. background: xxx;
        if nextRelevantTokenType == "right_curly" or nextRelevantTokenType == "semicolon":
            node = Property(tokenizer, staticContext)
            return node

        # e.g. h1, #dad {...
        elif nextRelevantTokenType == "left_curly":
            node = Selector(tokenizer, staticContext)
            return node

        else:
            raise SyntaxError("Warning: Unhandled: %s in Statement()" % nextTokenType, tokenizer)


    # Declaration / Assignment
    elif tokenType == "variable":
        node = Variable(tokenizer, staticContext)
        return node


    # Vendor prefixed property
    elif tokenType == "minus":
        node = Property(tokenizer, staticContext)
        return node


    # Generated content or pseudo selector
    elif tokenType == "colon":
        nextTokenType = tokenizer.peek()

        # e.g. ::after, ...
        if nextTokenType == "colon":
            node = Selector(tokenizer, staticContext)
            return node

        # e.g. :last-child, ...
        elif nextTokenType == "identifier":
            node = Selector(tokenizer, staticContext)
            return node

        else:
            raise SyntaxError("Warning: Unhandled: %s in Statement()" % nextTokenType, tokenizer)


    # Class selectors e.g. .message {...
    elif tokenType == "dot":
        nextTokenType = tokenizer.peek()

        if nextTokenType == "identifier":
            node = Selector(tokenizer, staticContext)
            return node

        else:
            raise SyntaxError("Warning: Unhandled: %s in Statement()" % nextTokenType, tokenizer)


    # Attribute selectors e.g. [hidden] {...
    elif tokenType == "left_bracket":
        nextTokenType = tokenizer.peek()

        if nextTokenType == "identifier":
            node = Selector(tokenizer, staticContext)
            return node

        else:
            raise SyntaxError("Warning: Unhandled: %s in Statement()" % nextTokenType, tokenizer)


    # Class selectors e.g. &.selected, &::after {...
    elif tokenType == "ampersand":
        nextTokenType = tokenizer.peek()

        if nextTokenType == "identifier" or nextTokenType == "colon" or nextTokenType == "left_curly" or nextTokenType == "left_bracket":
            node = Selector(tokenizer, staticContext)
            return node

        else:
            raise SyntaxError("Warning: Unhandled: %s in Statement()" % nextTokenType, tokenizer)


    elif tokenType == "semicolon":
        node = Node.Node(tokenizer, "semicolon")
        return node


    else:
        raise SyntaxError("Warning: Unsupported token in Statement(): %s" % tokenType, tokenizer)



def Property(tokenizer, staticContext):
    """
    Parses all CSS properties e.g.

    - background: red
    - font: 12px bold Arial;
    """

    node = Node.Node(tokenizer, "property")
    node.name = ""

    # Start from the beginning to support mixed identifiers/variables easily
    tokenizer.unget()

    while tokenizer.match("variable") or tokenizer.match("identifier"):
        token = tokenizer.token
        if token.type == "variable":
            node.name += "${%s}" % token.value

            if hasattr(node, "dynamic"):
                node.dynamic.add(token.value)
            else:
                node.dynamic = set([token.value])

        else:
            node.name += token.value

    if not tokenizer.mustMatch("colon"):
        raise SyntaxError("Invalid property definition", tokenizer)

    # Add all values until we find a semicolon or right curly
    while tokenizer.peek() not in ("semicolon", "right_curly"):
        childNode = ValueExpression(tokenizer, staticContext)

        node.append(childNode)

    return node


def KeyFrames(tokenizer, staticContext):
    """
    Supports e.g.:

    @keyframes fade{
      from, 10%{
        background-color: #000000;
      }

      100%{
        background-color: #FFFFFF;
      }
    }
    """

    node = Node.Node(tokenizer, "keyframes")
    node.vendor = Util.extractVendor(tokenizer.token.value)

    # Use param as name on keyframes
    tokenizer.get()
    node.name = tokenizer.token.value

    tokenizer.mustMatch("left_curly")

    while tokenizer.get() != "right_curly":

        # Parse frame as block
        frameNode = Node.Node(tokenizer, "frame")
        token = tokenizer.token
        frameNode.value = "%s%s" % (token.value, getattr(token, "unit", ""))
        node.append(frameNode)

        # Process comma separated values for
        while True:
            if tokenizer.peek() != "comma":
                break
            else:
                tokenizer.mustMatch("comma")

                # Next one is our next value
                tokenizer.get()
                token = tokenizer.token
                frameNode.value += ",%s%s" % (token.value, getattr(token, "unit", ""))

        # Next process content of selector
        blockNode = Block(tokenizer, staticContext)
        frameNode.append(blockNode, "rules")

    return node


def FontFace(tokenizer, staticContext):

    # Like a selector but store as a different type

    node = node = Node.Node(tokenizer, "fontface")
    childNode = Block(tokenizer, staticContext)
    node.append(childNode, "rules")

    return node


def Media(tokenizer, staticContext):
    """
    Supports e.g.:

    @media print{
      body{
        background-color: #000000;
      }
    }

    @media handheld, tv{
      body{
        background-color: yellow;
      }
    }
    """

    node = Node.Node(tokenizer, "media")

    tokenType = tokenizer.get()
    query = ""
    requiresSpace = False

    while tokenType != "left_curly":
        token = tokenizer.token

        if tokenType == "identifier":
            if requiresSpace :
                query += " "
            query += token.value
            requiresSpace = True
        elif tokenType == "comma":
            query += ","
            requiresSpace = False
        elif tokenType == "left_paren":
            if requiresSpace:
                query += " "
            query += "("
            requiresSpace = False
        elif tokenType == "right_paren":
            query += ")"
            requiresSpace = True
        elif tokenType == "colon":
            query += ":"
            requiresSpace = False
        elif tokenType == "div":
            query += "/"
            requiresSpace = False
        elif tokenType == "string":
            if requiresSpace:
                query += " "
            query += ascii_encoder.encode(token.value)
            requiresSpace = True
        elif tokenType == "number":
            if requiresSpace:
                query += " "
            query += "%s%s" % (token.value, getattr(token, "unit", ""))
            requiresSpace = True
        elif tokenType in ("and", "or", "not"):
            if requiresSpace :
                query += " "
            query += tokenType
            requiresSpace = True
        else:
            raise SyntaxError("Unsupported selector token %s" % tokenType, tokenizer)


        tokenType = tokenizer.get()

    # Split at commas, but ignore any white spaces (trim single selectors)
    node.name = RE_SELECTOR_SPLIT.split(query)

    # Next process content of selector
    tokenizer.unget()
    childNode = Block(tokenizer, staticContext)
    node.append(childNode, "rules")

    return node





def Selector(tokenizer, staticContext):
    """
    CSS selector parser e.g.

    h1
    .infobox
    #header
    h1::after
    h2:first-child
    """

    node = Node.Node(tokenizer, "selector")

    tokenType = tokenizer.token.type
    selector = ""
    nospace = True

    while tokenType != "left_curly":
        token = tokenizer.token

        if tokenType in ("identifier", "colon", "dot", "ampersand", "command"):
            if not nospace and selector != "" and (tokenizer.skippedSpaces or tokenizer.skippedLineBreaks):
                selector += " "

            nospace = False

            if tokenType == "identifier":
                selector += token.value
            elif tokenType == "colon":
                selector += ":"
            elif tokenType == "dot":
                selector += "."
            elif tokenType == "ampersand":
                selector += "&"
            elif tokenType == "command":
                selector += "@%s" % token.value

        else:

            # No spaces between the previous, this symbol and the next
            nospace = True

            if tokenType == "comma":
                selector += ","
            elif tokenType == "tilde":
                selector += "~"
            elif tokenType == "plus":
                selector += "+"
            elif tokenType == "gt":
                selector += ">"
            elif tokenType == "left_bracket":
                selector += "["
            elif tokenType == "right_bracket":
                selector += "]"
            elif tokenType == "left_paren":
                selector += "("
            elif tokenType == "right_paren":
                selector += ")"
            elif tokenType == "dollar":
                selector += "$"
            elif tokenType == "carat":
                selector += "^"
            elif tokenType == "pipe":
                selector += "|"
            elif tokenType == "mul":
                selector += "*"
            elif tokenType == "not":
                selector += "not"
            elif tokenType == "assign":
                if token.assignOp:
                    if token.assignOp == "mul":
                        selector += "*"
                    else:
                        raise SyntaxError("Invalid attribute selector expression %s" % token.assignOp, tokenizer)
                selector += "="
            elif tokenType == "string":
                selector += ascii_encoder.encode(token.value)
            elif tokenType == "number":
                selector += "%s%s" % (token.value, getattr(token, "unit", ""))
            elif tokenType == "variable":
                if hasattr(node, "dynamic"):
                    node.dynamic.add(token.value)
                else:
                    node.dynamic = set([token.value])

                selector += "${%s}" % token.value
            else:
                raise SyntaxError("Unsupported selector token %s" % tokenType, tokenizer)

        tokenType = tokenizer.get()

    # Split at commas, but ignore any white spaces (trim single selectors)
    node.name = RE_SELECTOR_SPLIT.split(selector)

    # Next process content of selector
    tokenizer.unget()
    childNode = Block(tokenizer, staticContext)
    node.append(childNode, "rules")

    return node



def Variable(tokenizer, staticContext):
    """
    All kind of variable usage:

    - variable access
    - variable declaration
    - mixin declaration
    - mixin call
    """

    name = tokenizer.token.value

    # e.g. $foo = 1
    if tokenizer.peek() == "assign":

        node = Node.Node(tokenizer, "declaration")
        node.name = name

        if tokenizer.match("assign"):
            # Support declarations with assign operations
            # Declaration and assignment are effectively the same
            node.assignOp = tokenizer.token.assignOp

            initializerNode = OrExpression(tokenizer, staticContext)

            if tokenizer.peek() not in ("comma", "semicolon"):
                initializerList = Node.Node(tokenizer, "list")
                initializerList.append(initializerNode)
                node.append(initializerList, "initializer")

                while tokenizer.peek() not in ("comma", "semicolon"):
                    initializerList.append(OrExpression(tokenizer, staticContext))

            else:
                node.append(initializerNode, "initializer")

        # Ignore trailing comma... handle it like a follow up expression
        if tokenizer.peek("comma"):
            tokenizer.get()

    # e.g. $foo {}
    elif tokenizer.peek() == "left_curly":
        node = Node.Node(tokenizer, "mixin")
        node.name = name

        node.append(Block(tokenizer, staticContext), "rules")

    # e.g. $foo() or $foo(a,b) or $foo(a,b) {}
    elif tokenizer.peek() == "left_paren":
        node = Node.Node(tokenizer, "call")
        node.name = name

        # Mixin call or Mixin definition
        if tokenizer.mustMatch("left_paren"):
            node.append(ArgumentList(tokenizer, staticContext), "params")

        # Mixin definition
        if tokenizer.peek() == "left_curly":
            node.type = "mixin"
            node.append(Block(tokenizer, staticContext), "rules")

        # Mixin call with content section
        elif tokenizer.peek() == "lt":
            # Ignore smaller symbol / Jump to block
            tokenizer.get()
            node.append(Block(tokenizer, staticContext), "rules")

        return node

    # e.g. ${align}: left; => Parse as property
    elif tokenizer.peek() == "colon":
        return Property(tokenizer, staticContext)

    else:
        node = Node.Node(tokenizer, "variable")
        node.name = name

    return node


def ParenExpression(tokenizer, staticContext):
    """
    An expression in parens. Sometimes to force priority of math operations etc.
    """

    tokenizer.mustMatch("left_paren")
    node = Expression(tokenizer, staticContext)
    tokenizer.mustMatch("right_paren")

    return node


def ValueExpression(tokenizer, staticContext):
    """
    Top-down expression parser for rule values in stylestyles.
    """

    node = UnaryExpression(tokenizer, staticContext)

    if tokenizer.match("comma"):
        childNode = Node.Node(tokenizer, "comma")
        childNode.append(node)
        node = childNode

        while True:
            childNode = node[len(node)-1]
            node.append(UnaryExpression(tokenizer, staticContext))

            if not tokenizer.match("comma"):
                break

    return node


def Expression(tokenizer, staticContext):
    """
    Top-down expression parser for stylestyles.
    """

    node = AssignExpression(tokenizer, staticContext)

    if tokenizer.match("comma"):
        childNode = Node.Node(tokenizer, "comma")
        childNode.append(node)
        node = childNode

        while True:
            childNode = node[len(node)-1]
            node.append(AssignExpression(tokenizer, staticContext))

            if not tokenizer.match("comma"):
                break

    return node


def AssignExpression(tokenizer, staticContext):
    comments = tokenizer.getComments()
    node = Node.Node(tokenizer, "assign")
    lhs = OrExpression(tokenizer, staticContext)
    addComments(lhs, None, comments)

    if not tokenizer.match("assign"):
        return lhs

    if lhs.type == "variable":
        pass
    else:
        raise SyntaxError("Bad left-hand side of assignment", tokenizer)

    node.assignOp = tokenizer.token.assignOp
    node.append(lhs)
    node.append(AssignExpression(tokenizer, staticContext))

    return node


def OrExpression(tokenizer, staticContext):
    node = AndExpression(tokenizer, staticContext)

    while tokenizer.match("or"):
        childNode = Node.Node(tokenizer, "or")
        childNode.append(node)
        childNode.append(AndExpression(tokenizer, staticContext))
        node = childNode

    return node


def AndExpression(tokenizer, staticContext):
    node = EqualityExpression(tokenizer, staticContext)

    while tokenizer.match("and"):
        childNode = Node.Node(tokenizer, "and")
        childNode.append(node)
        childNode.append(EqualityExpression(tokenizer, staticContext))
        node = childNode

    return node


def EqualityExpression(tokenizer, staticContext):
    node = RelationalExpression(tokenizer, staticContext)

    while tokenizer.match("eq") or tokenizer.match("ne"):
        childNode = Node.Node(tokenizer)
        childNode.append(node)

        express = RelationalExpression(tokenizer, staticContext)
        if express.type == "identifier":
            raise SyntaxError("Invalid expression", tokenizer)

        childNode.append(express)
        node = childNode

    return node


def RelationalExpression(tokenizer, staticContext):
    # Uses of the in operator in shiftExprs are always unambiguous,
    # so unset the flag that prohibits recognizing it.
    node = AddExpression(tokenizer, staticContext)
    if node.type == "identifier":
        return node

    while tokenizer.match("lt") or tokenizer.match("le") or tokenizer.match("ge") or tokenizer.match("gt"):
        childNode = Node.Node(tokenizer)
        childNode.append(node)

        express = AddExpression(tokenizer, staticContext)
        if express.type == "identifier":
            raise SyntaxError("Invalid expression", tokenizer)

        childNode.append(express)
        node = childNode

    return node


def AddExpression(tokenizer, staticContext):
    node = MultiplyExpression(tokenizer, staticContext)
    if node.type == "identifier":
        return node

    while tokenizer.match("plus") or tokenizer.match("minus"):
        # Whether there was skipped spaces before
        skippedA = tokenizer.skippedSpaces or tokenizer.skippedLineBreaks

        # ...but not after the plus/minus token
        peek = tokenizer.peek()
        skippedB = tokenizer.skippedSpaces or tokenizer.skippedLineBreaks

        # ... then do not interpret as plus/minus expression but as unary prefix
        if skippedA and not skippedB:
            tokenizer.unget()
            return node

        # Build real plus/minus node
        childNode = Node.Node(tokenizer)
        childNode.append(node)

        express = MultiplyExpression(tokenizer, staticContext)
        if express.type == "identifier":
            raise SyntaxError("Invalid expression", tokenizer)

        childNode.append(express)
        node = childNode

    return node


def MultiplyExpression(tokenizer, staticContext):
    node = UnaryExpression(tokenizer, staticContext)
    if node.type == "identifier":
        return node

    while tokenizer.match("mul") or tokenizer.match("div") or tokenizer.match("mod"):
        childNode = Node.Node(tokenizer)
        childNode.append(node)

        express = UnaryExpression(tokenizer, staticContext)
        if express.type == "identifier":
            raise SyntaxError("Invalid expression", tokenizer)

        childNode.append(express)
        node = childNode

    return node


def UnaryExpression(tokenizer, staticContext):
    tokenType = tokenizer.get(True)

    if tokenType in ["not", "plus", "minus"]:
        if tokenType == "plus":
            tokenType = "unary_plus"
        elif tokenType == "minus":
            tokenType = "unary_minus"

        node = Node.Node(tokenizer, tokenType)
        node.append(UnaryExpression(tokenizer, staticContext))

    else:
        tokenizer.unget()
        node = MemberExpression(tokenizer, staticContext)

    return node


def MemberExpression(tokenizer, staticContext):
    node = PrimaryExpression(tokenizer, staticContext)

    while True:
        tokenType = tokenizer.get()

        if tokenType == "end":
            break

        # system calls
        elif tokenType == "left_paren":

            if node.type == "identifier":
                childNode = Node.Node(tokenizer, "function")
                childNode.name = node.value

                # Special processing of URL commands
                if node.value == "url":
                    childNode.append(UrlArgumentList(tokenizer, staticContext), "params")
                else:
                    childNode.append(ArgumentList(tokenizer, staticContext), "params")

            elif node.type == "command":
                if node.name == "raw":
                    childNode = RawArgument(tokenizer, staticContext)
                elif node.name == "expr":
                    childNode = ExpressionArgument(tokenizer, staticContext)
                else:
                    childNode = Node.Node(tokenizer, "command")
                    childNode.name = node.name
                    childNode.append(ArgumentList(tokenizer, staticContext), "params")

            else:
                raise SyntaxError("Unsupported mixin include in expression statement", tokenizer)

        else:
            tokenizer.unget()
            return node

        node = childNode

    return node


def RawArgument(tokenizer, staticContext):
    if tokenizer.match("right_paren", True):
        raise SyntaxError("Expected expression", tokenizer)

    node = Node.Node(tokenizer, "raw")
    node.append(PrimaryExpression(tokenizer, staticContext))

    tokenizer.mustMatch("right_paren")

    return node


def ExpressionArgument(tokenizer, staticContext):
    if tokenizer.match("right_paren", True):
        raise SyntaxError("Expected expression", tokenizer)

    node = Node.Node(tokenizer, "expr")
    node.append(AddExpression(tokenizer, staticContext))

    tokenizer.mustMatch("right_paren")

    return node


def UrlArgumentList(tokenizer, staticContext):
    node = Node.Node(tokenizer, "list")

    if tokenizer.match("right_paren", True):
        return node

    url = ""
    while True:
        tokenType = tokenizer.get()

        if tokenType == "right_paren":
            break
        elif tokenType == "string":
            token = tokenizer.token
            url += token.value
        elif tokenType == "number":
            token = tokenizer.token
            url += "%s%s" % (token.value, getattr(token, "unit", ""))
        elif tokenType == "div":
            url += "/"
        elif tokenType == "dot":
            url += "."
        elif tokenType == "identifier":
            token = tokenizer.token
            url += token.value
        elif tokenType == "variable":
            # Fast path when variable present
            token = tokenizer.token
            var = Node.Node(tokenizer)
            var.name = token.value
            node.append(var)
            tokenizer.mustMatch("right_paren")
            return node
        else:
            token = tokenizer.token
            raise SyntaxError("Invalid token in URL parameter: Type = %s ; Value = %s" % (token.type, getattr(token, "value", None)), tokenizer)

    urlParam = Node.Node(tokenizer, "identifier")
    urlParam.value = url
    node.append(urlParam)

    return node


def ArgumentList(tokenizer, staticContext):
    node = Node.Node(tokenizer, "list")

    if tokenizer.match("right_paren", True):
        return node

    while True:
        childNode = AssignExpression(tokenizer, staticContext)
        node.append(childNode)
        if not tokenizer.match("comma"):
            break

    tokenizer.mustMatch("right_paren")

    return node


def PrimaryExpression(tokenizer, staticContext):
    tokenType = tokenizer.get(True)

    if tokenType == "function":
        node = FunctionDefinition(tokenizer, staticContext, False, "expressed_form")

    elif tokenType == "left_paren":
        # ParenExpression does its own matching on parentheses, so we need to unget.
        tokenizer.unget()
        node = ParenExpression(tokenizer, staticContext)
        node.parenthesized = True

    elif tokenType == "variable":
        node = Node.Node(tokenizer, tokenType)
        node.name = tokenizer.token.value

    elif tokenType == "command":
        node = Node.Node(tokenizer, tokenType)
        node.name = tokenizer.token.value

    elif tokenType in ["null", "true", "false", "identifier", "number", "string", "div"]:
        node = Node.Node(tokenizer, tokenType)
        if tokenType in ("identifier", "string", "number"):
            node.value = tokenizer.token.value
        if tokenType == "number" and hasattr(tokenizer.token, "unit"):
            node.unit = tokenizer.token.unit
        if tokenType == "string":
            node.quote = tokenizer.token.quote
        if tokenType == "div":
            node.type = "slash"

    else:
        raise SyntaxError("Missing operand. Found type: %s" % tokenType, tokenizer)

    return node






def addComments(currNode, prevNode, comments):
    if not comments:
        return

    currComments = []
    prevComments = []
    for comment in comments:
        # post comments - for previous node
        if comment.context == "inline":
            prevComments.append(comment)

        # all other comment styles are attached to the current one
        else:
            currComments.append(comment)

    # Merge with previously added ones
    if hasattr(currNode, "comments"):
        currNode.comments.extend(currComments)
    else:
        currNode.comments = currComments

    if prevNode:
        if hasattr(prevNode, "comments"):
            prevNode.comments.extend(prevComments)
        else:
            prevNode.comments = prevComments
    else:
        # Don't loose the comment in tree (if not previous node is there, attach it to this node)
        currNode.comments.extend(prevComments)


