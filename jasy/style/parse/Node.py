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
        "value", "parenthesized", "fileId", "params",
        "name", "initializer", "condition", "assignOp",
        "thenPart", "elsePart", "statements",
        "statement", "variables", "names",

        # style specific
        "rules", "token", "unit", "selector", "dynamic", "vendor", "quote", "noscope"
    ]

