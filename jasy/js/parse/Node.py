#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.parse.AbstractNode as AbstractNode

class Node(AbstractNode.AbstractNode):

    __slots__ = [
        # core data
        "line", "type", "tokenizer", "start", "end", "rel", "parent",

        # dynamic added data by other modules
        "comments", "scope",

        # node type specific
        "value", "expression", "body", "functionForm", "parenthesized", "fileId", "params",
        "name", "readOnly", "initializer", "condition", "isLoop", "isEach", "object", "assignOp",
        "iterator", "thenPart", "exception", "elsePart", "setup", "postfix", "update", "tryBlock",
        "block", "defaultIndex", "discriminant", "label", "statements", "finallyBlock",
        "statement", "variables", "names", "guard", "for", "tail", "expressionClosure"
    ]

