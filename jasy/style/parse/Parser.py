#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.style.tokenize.Tokenizer as Tokenizer
import jasy.style.parse.Node as Node

__all__ = [ "parse" ]


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
        print("TOKENIZER AT: %s at line %s" % (tokenizer.token.type, tokenizer.token.line))
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

        if tokenValue == "if":
            node = Node.Node(tokenizer, "if")
            node.append(Expression(tokenizer, staticContext), "condition")
            staticContext.statementStack.append(node)
            node.append(Statement(tokenizer, staticContext), "thenPart")

            tokenValue = getattr(tokenizer.token, "value", "")

            if tokenizer.match("command") and tokenValue == "else":
                comments = tokenizer.getComments()
                elsePart = Statement(tokenizer, staticContext)
                addComments(elsePart, node, comments)
                node.append(elsePart, "elsePart")

            staticContext.statementStack.pop()

            return node

        else:
            print("Unknown command: %s" % tokenValue)

    elif tokenType == "identifier":
        # e.g. background: 
        if tokenizer.peek() == "colon":
            node = Property(tokenizer, staticContext)
            return node

        # e.g. h1 {...
        elif tokenizer.peek() == "left_curly":
            node = Selector(tokenizer, staticContext)
            return node

        # e.g. background-color
        elif tokenizer.peek() == "minus":
            node = Property(tokenizer, staticContext)
            return node

        # e.g. foo() or foo(a,b) or foo(a,b){}
        elif tokenizer.peek() == "left_paren":

            node = Node.Node(tokenizer, "call")
            node.name = tokenizer.token.value

            if tokenizer.mustMatch("left_paren"):
                node.append(ArgumentList(tokenizer, staticContext), "params")

            if tokenizer.peek() == "left_curly":
                node.type = "mixin"
                node.append(Block(tokenizer, staticContext), "rules")

            return node

        else:
            print("NEXT-TYPE: %s after %s" % (tokenizer.peek(), tokenType))



    # Generated content or pseudo selector
    elif tokenType == "colon":

        # e.g. ::after, ...
        if tokenizer.peek() == "colon":
            node = Selector(tokenizer, staticContext)
            return node

        # e.g. :last-child, ...
        elif tokenizer.peek() == "identifier":
            node = Selector(tokenizer, staticContext)
            return node


        else:
            print("NEXT-TYPE: %s after %s" % (tokenizer.peek(), tokenType))


    elif tokenType == "minus":
        # e.g. background-color
        if tokenizer.peek() == "minus":
            node = Property(tokenizer, staticContext)
            return node

        else:
            print("NEXT-TYPE: %s after %s" % (tokenizer.peek(), tokenType))



    else:
        node = Node.Node(tokenizer, "unknown")
        node.token = tokenizer.token.type
        return node



def Property(tokenizer, staticContext):
    node = Node.Node(tokenizer, "property")
    node.name = tokenizer.token.value
    
    while tokenizer.get() != "colon":
        if tokenizer.token.type == "minus":
            node.name += "-"


    tokenizer.unget()
    if not tokenizer.mustMatch("colon"):
        raise SyntaxError("Invalid property definition", tokenizer)

    node.append(Expression(tokenizer, staticContext), "value")

    return node


def Selector(tokenizer, staticContext):
    node = Node.Node(tokenizer, "selector")

    tokenType = tokenizer.token.type
    selector = ""

    while tokenType != "left_curly":
        if tokenType == "identifier":
            selector += tokenizer.token.value

        elif tokenType == "colon":
            selector += ":"

        elif tokenType == "comma":
            selector += ", "

        tokenType = tokenizer.get()

    node.name = selector

    # Next process content of selector
    tokenizer.unget()
    childNode = Block(tokenizer, staticContext)
    node.append(childNode, "rules")

    return node



def Variable(tokenizer, staticContext):
    
    if tokenizer.peek() == "assign":
        node = Node.Node(tokenizer, "declaration")
        node.name = tokenizer.token.value

        if tokenizer.match("assign"):
            if tokenizer.token.assignOp:
                raise SyntaxError("Invalid variable initialization", tokenizer)

            initializerNode = AssignExpression(tokenizer, staticContext)
            node.append(initializerNode, "initializer")        

    elif tokenizer.peek() == "left_curly":
        node = Node.Node(tokenizer, "mixin")
        node.name = tokenizer.token.value
        node.append(Block(tokenizer, staticContext), "rules")

    else:
        node = Node.Node(tokenizer, "variable")
        node.name = tokenizer.token.value

    return node


def ParenExpression(tokenizer, staticContext):
    tokenizer.mustMatch("left_paren")
    node = Expression(tokenizer, staticContext)
    tokenizer.mustMatch("right_paren")

    return node


def Expression(tokenizer, staticContext):
    """Top-down expression parser matched against SpiderMonkey."""
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
    
    while tokenizer.match("eq") or tokenizer.match("ne") or tokenizer.match("strict_eq") or tokenizer.match("strict_ne"):
        childNode = Node.Node(tokenizer)
        childNode.append(node)
        childNode.append(RelationalExpression(tokenizer, staticContext))
        node = childNode

    return node


def RelationalExpression(tokenizer, staticContext):
    # Uses of the in operator in shiftExprs are always unambiguous,
    # so unset the flag that prohibits recognizing it.
    node = AddExpression(tokenizer, staticContext)

    while tokenizer.match("lt") or tokenizer.match("le") or tokenizer.match("ge") or tokenizer.match("gt"):
        childNode = Node.Node(tokenizer)
        childNode.append(node)
        childNode.append(AddExpression(tokenizer, staticContext))
        node = childNode
    
    return node


def AddExpression(tokenizer, staticContext):
    node = MultiplyExpression(tokenizer, staticContext)
    
    while tokenizer.match("plus") or tokenizer.match("minus"):
        childNode = Node.Node(tokenizer)
        childNode.append(node)
        childNode.append(MultiplyExpression(tokenizer, staticContext))
        node = childNode

    return node


def MultiplyExpression(tokenizer, staticContext):
    node = UnaryExpression(tokenizer, staticContext)
    
    while tokenizer.match("mul") or tokenizer.match("div") or tokenizer.match("mod"):
        childNode = Node.Node(tokenizer)
        childNode.append(node)
        childNode.append(UnaryExpression(tokenizer, staticContext))
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
        print("MEMBER NEXT: %s" % tokenType, tokenizer.token.line)

        if tokenType == "end":
            break
        
        if tokenType == "dot":
            childNode = Node.Node(tokenizer)
            childNode.append(node)
            
            tokenizer.mustMatch("identifier")

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

    elif tokenType == "left_bracket":
        node = builder.ARRAYINIT_build(tokenizer)
        while True:
            tokenType = tokenizer.peek(True)
            if tokenType == "right_bracket":
                break
        
            if tokenType == "comma":
                tokenizer.get()
                builder.ARRAYINIT_addElement(node, None)
                continue

            builder.ARRAYINIT_addElement(node, AssignExpression(tokenizer, staticContext))

            if tokenType != "comma" and not tokenizer.match("comma"):
                break

        # If we matched exactly one element and got a "for", we have an
        # array comprehension.
        if len(node) == 1 and tokenizer.match("for"):
            childNode = builder.ARRAYCOMP_build(tokenizer)
            builder.ARRAYCOMP_setExpression(childNode, node[0])
            builder.ARRAYCOMP_setTail(childNode, comprehensionTail(tokenizer, staticContext))
            node = childNode
        
        builder.COMMENTS_add(node, node, tokenizer.getComments())
        tokenizer.mustMatch("right_bracket")
        builder.PRIMARY_finish(node)

    elif tokenType == "left_curly":
        node = builder.OBJECTINIT_build(tokenizer)

        if not tokenizer.match("right_curly"):
            while True:
                tokenType = tokenizer.get()
                tokenValue = getattr(tokenizer.token, "value", None)
                comments = tokenizer.getComments()
                
                if tokenValue in ("get", "set") and tokenizer.peek() == "identifier":
                    if staticContext.ecma3OnlyMode:
                        raise SyntaxError("Illegal property accessor", tokenizer)
                        
                    fd = FunctionDefinition(tokenizer, staticContext, True, "expressed_form")
                    builder.OBJECTINIT_addProperty(node, fd)
                    
                else:
                    if tokenType == "identifier" or tokenType == "number" or tokenType == "string":
                        id = builder.PRIMARY_build(tokenizer, "identifier")
                        builder.PRIMARY_finish(id)
                        
                    elif tokenType == "right_curly":
                        if staticContext.ecma3OnlyMode:
                            raise SyntaxError("Illegal trailing ,", tokenizer)
                            
                        tokenizer.unget()
                        break
                            
                    else:
                        if tokenValue in jasy.js.tokenize.Lang.keywords:
                            id = builder.PRIMARY_build(tokenizer, "identifier")
                            builder.PRIMARY_finish(id)
                        else:
                            print("Value is '%s'" % tokenValue)
                            raise SyntaxError("Invalid property name", tokenizer)
                    
                    if tokenizer.match("colon"):
                        childNode = builder.PROPERTYINIT_build(tokenizer)
                        builder.COMMENTS_add(childNode, node, comments)
                        builder.PROPERTYINIT_addOperand(childNode, id)
                        builder.PROPERTYINIT_addOperand(childNode, AssignExpression(tokenizer, staticContext))
                        builder.PROPERTYINIT_finish(childNode)
                        builder.OBJECTINIT_addProperty(node, childNode)
                        
                    else:
                        # Support, e.g., |var {staticContext, y} = o| as destructuring shorthand
                        # for |var {staticContext: staticContext, y: y} = o|, per proposed JS2/ES4 for JS1.8.
                        if tokenizer.peek() != "comma" and tokenizer.peek() != "right_curly":
                            raise SyntaxError("Missing : after property", tokenizer)
                        builder.OBJECTINIT_addProperty(node, id)
                    
                if not tokenizer.match("comma"):
                    break

            builder.COMMENTS_add(node, node, tokenizer.getComments())
            tokenizer.mustMatch("right_curly")

        builder.OBJECTINIT_finish(node)

    elif tokenType == "left_paren":
        # ParenExpression does its own matching on parentheses, so we need to unget.
        tokenizer.unget()
        node = ParenExpression(tokenizer, staticContext)
        node.parenthesized = True

    elif tokenType == "variable":
        node = Node.Node(tokenizer, tokenType)
        node.name = tokenizer.token.value

    elif tokenType in ["null", "this", "true", "false", "identifier", "number", "string", "hex"]:
        node = Node.Node(tokenizer, tokenType)
        if tokenType in ("identifier", "string", "hex", "number"):
            node.value = tokenizer.token.value

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


