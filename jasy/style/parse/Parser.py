#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import re

import jasy.style.tokenize.Tokenizer as Tokenizer
import jasy.style.parse.Node as Node

__all__ = [ "parse", "parseExpression" ]


RE_SELECTOR_SPLIT = re.compile(r"\s*,\s*")


def parseExpression(source, fileId=None, line=1):
    # Convert source into expression statement to be friendly to the Tokenizer
    if not source.endswith(";"):
        source = source + ";"
    
    tokenizer = Tokenizer.Tokenizer(source, fileId, line)
    staticContext = StaticContext(False)
    
    return Expression(tokenizer, staticContext)


def parse(source, fileId=None, line=1):    
    tokenizer = Tokenizer.Tokenizer(source, fileId, line)
    staticContext = StaticContext(False)
    node = Sheet(tokenizer, staticContext)
    
    # store fileId on top-level node
    node.fileId = tokenizer.fileId
    
    # add missing comments e.g. empty file with only a comment etc.
    # if there is something non-attached by an inner node it is attached to
    # the top level node, which is not correct, but might be better than
    # just ignoring the comment after all.
    # if len(node) > 0:
    #     builder.COMMENTS_add(node[-1], None, tokenizer.getComments())
    # else:
    #     builder.COMMENTS_add(node, None, tokenizer.getComments())
    
    if not tokenizer.done():
        raise SyntaxError("Unexpected end of file", tokenizer)

    return node



class SyntaxError(Exception):
    def __init__(self, message, tokenizer):
        Exception.__init__(self, "Syntax error: %s\n%s:%s" % (message, tokenizer.fileId, tokenizer.line))


# Used as a status container during tree-building for every def body and the global body
class StaticContext(object):
    # inRule is used to check if a return stm appears in a valid context.
    def __init__(self, inRule):
        # Whether this is inside a rule, mostly True, only for top-level scope it's False
        self.inRule = inRule
        
        self.blockId = 0
        self.statementStack = []
                
        # Status
        self.bracketLevel = 0
        self.curlyLevel = 0
        self.parenLevel = 0
        self.hookLevel = 0
        

def Sheet(tokenizer, staticContext):
    """Parses the toplevel and rule bodies."""
    node = Statements(tokenizer, staticContext)
    
    # change type from "block" to "sheet" for style root
    node.type = "sheet"
    
    # copy over data from compiler context
    # node.functions = staticContext.functions
    # node.variables = staticContext.variables

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
    
    if tokenType == "variable":
        node = Variable(tokenizer, staticContext)
        return node


    elif tokenType == "left_curly":
        node = Statements(tokenizer, staticContext)
        tokenizer.mustMatch("right_curly")
        return node


    elif tokenType == "command":

        if tokenValue == "if" or tokenValue == "elif":
            node = Node.Node(tokenizer, "if")
            node.append(Expression(tokenizer, staticContext), "condition")
            staticContext.statementStack.append(node)
            node.append(Statement(tokenizer, staticContext), "thenPart")

            if tokenizer.match("command"):
                elseTokenValue = tokenizer.token.value
                if elseTokenValue == "elif":

                    # Process like an "if" and append as elsePart
                    tokenizer.unget()
                    elsePart = Statement(tokenizer, staticContext)
                    node.append(elsePart, "elsePart")        

                if elseTokenValue == "else":
                    comments = tokenizer.getComments()
                    elsePart = Statement(tokenizer, staticContext)
                    addComments(elsePart, node, comments)
                    node.append(elsePart, "elsePart")

            staticContext.statementStack.pop()

            return node

        elif tokenValue == "include":
            node = Node.Node(tokenizer, "include")
            node.append(Expression(tokenizer, staticContext))
            return node

        else:
            raise SyntaxError("Unknown system command: %s" % tokenValue, tokenizer)


    elif tokenType == "identifier":
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


    # Class selectors e.g. &.selected, &::after {...
    elif tokenType == "ampersand":
        nextTokenType = tokenizer.peek()

        if nextTokenType == "identifier" or nextTokenType == "colon" or nextTokenType == "left_curly":
            node = Selector(tokenizer, staticContext)
            return node

        else:
            raise SyntaxError("Warning: Unhandled: %s in Statement()" % nextTokenType, tokenizer)
            

    elif tokenType == "semicolon":
        node = Node.Node(tokenizer, "semicolon")
        return node


    else:
        node = Node.Node(tokenizer, "unknown")
        node.token = tokenizer.token.type
        return node



def Property(tokenizer, staticContext):
    """
    Parses all CSS properties e.g.

    - background: red
    - font: 12px bold Arial;
    """

    node = Node.Node(tokenizer, "property")
    node.name = tokenizer.token.value

    if not tokenizer.mustMatch("colon"):
        raise SyntaxError("Invalid property definition", tokenizer)

    # Add all values until we find a semicolon or right curly
    while tokenizer.peek() not in ("semicolon", "right_curly"):
        childNode = Expression(tokenizer, staticContext)

        node.append(childNode)    

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

        if tokenType in ("identifier", "colon", "dot"):
            if not nospace and selector != "" and (tokenizer.skippedSpaces or tokenizer.skippedLineBreaks):
                selector += " "     

            nospace = False       

            if tokenType == "identifier":
                selector += token.value
            elif tokenType == "colon":
                selector += ":"
            elif tokenType == "dot":
                selector += "."

        else:

            # No spaces between the previous, this symbol and the next
            nospace = True

            if tokenType == "comma":
                selector += ","
            elif tokenType == "ampersand":
                selector += "&"
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
            elif tokenType == "number":
                selector += "%s%s" % (token.value, getattr(token, "unit", ""))
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
            if tokenizer.token.assignOp:
                raise SyntaxError("Invalid variable initialization", tokenizer)

            initializerNode = AssignExpression(tokenizer, staticContext)
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

        if tokenizer.mustMatch("left_paren"):
            node.append(ArgumentList(tokenizer, staticContext), "params")

        if tokenizer.peek() == "left_curly":
            node.type = "mixin"
            node.append(Block(tokenizer, staticContext), "rules")

        return node        

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


def Expression(tokenizer, staticContext):
    """
    Top-down expression parser matched against SpiderMonkey for original JS 
    parsing and modified to match styles.
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

    if lhs.type == "object_init" or lhs.type == "array_init" or lhs.type == "identifier" or lhs.type == "dot" or lhs.type == "index" or lhs.type == "call":
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

    if tokenType in ["typeof", "not", "plus", "minus"]:
        if tokenType == "plus":
            tokenType = "unary_plus"
        elif tokenType == "minus":
            tokenType = "unary_minus"
            
        node = Node.Node(tokenizer, tokenType)
        node.append(UnaryExpression(tokenizer, staticContext))
    
    elif tokenType == "increment" or tokenType == "decrement":
        # Prefix increment/decrement.
        node = Node.Node(tokenizer, tokenType)
        node.append(MemberExpression(tokenizer, staticContext, True))

    else:
        tokenizer.unget()
        node = MemberExpression(tokenizer, staticContext, True)

        # Don't look across a newline boundary for a postfix {in,de}crement.
        if tokenizer.tokens[(tokenizer.tokenIndex + tokenizer.lookahead - 1) & 3].line == tokenizer.line:
            if tokenizer.match("increment") or tokenizer.match("decrement"):
                childNode = Node.Node(tokenizer)
                childNode.postfix = True
                childNode.append(node)
                node = childNode

    return node


def MemberExpression(tokenizer, staticContext, allowCallSyntax):
    node = PrimaryExpression(tokenizer, staticContext)

    while True:
        tokenType = tokenizer.get()

        if tokenType == "end":
            break
        
        if tokenType == "dot":
            childNode = Node.Node(tokenizer)
            childNode.append(node)
            
            tokenizer.mustMatch("identifier")
            tokenType = tokenizer.token.type
            idenNode = Node.Node(tokenizer, tokenType)
            idenNode.value = tokenizer.token.value
            childNode.append(idenNode)

        elif tokenType == "left_paren" and allowCallSyntax:
            childNode = Node.Node(tokenizer, "call")
            childNode.append(node)
            childNode.append(ArgumentList(tokenizer, staticContext), "params")

        else:
            tokenizer.unget()
            return node

        node = childNode

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

    elif tokenType in ["null", "this", "true", "false", "identifier", "number", "string"]:
        node = Node.Node(tokenizer, tokenType)
        if tokenType in ("identifier", "string", "number"):
            node.value = tokenizer.token.value
        if tokenType == "number" and hasattr(tokenizer.token, "unit"):
            node.unit = tokenizer.token.unit

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


