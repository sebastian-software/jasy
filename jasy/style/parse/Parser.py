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



def Statement(tokenizer, staticContext):
    """Parses a Statement."""

    tokenType = tokenizer.get(True)
    tokenValue = getattr(tokenizer.token, "value", "")
    
    print("TOKEN-TYPE: %s: %s" % (tokenType, tokenValue))

    if tokenType == "variable":
        node = Variable(tokenizer, staticContext)
        return node





def Variable(tokenizer, staticContext):
    
    if tokenizer.peek() == "assign":
        node = Node.Node(tokenizer, "declaration")
        node.name = tokenizer.token.value
        
        # Jump over assign
        tokenizer.get()

        # Process value
        expression = AssignExpression(tokenizer, staticContext)
        node.append(expression, "initializer")

    else:
        node = Node.Node(tokenizer, "variable")
        node.name = tokenizer.token.value


    print("XXX")
    print(node)
    #node.name = 



def AssignExpression(tokenizer, staticContext):
    node = Node.Node(tokenizer, "expression")
    return node

















