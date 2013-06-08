#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import json, copy

class Node(list):        

    def __init__(self, tokenizer=None, type=None, args=[]):
        list.__init__(self)
        
        self.start = 0
        self.end = 0
        self.line = None
        
        if tokenizer:
            token = getattr(tokenizer, "token", None)
            if token:
                # We may define a custom type but use the same positioning as another token
                # e.g. transform curlys in block nodes, etc.
                self.type = type if type else getattr(token, "type", None)
                self.line = token.line
                
                # Start & end are file positions for error handling.
                self.start = token.start
                self.end = token.end
            
            else:
                self.type = type
                self.line = tokenizer.line
                self.start = None
                self.end = None

            self.tokenizer = tokenizer
            
        elif type:
            self.type = type

        for arg in args:
            self.append(arg)
                
        
    def getSource(self):
        """Returns the source code of the node"""

        if not self.tokenizer:
            raise Exception("Could not find source for node '%s'" % node.type)
            
        if getattr(self, "start", None) is not None:
            if getattr(self, "end", None) is not None:
                return self.tokenizer.source[self.start:self.end]
            return self.tokenizer.source[self.start:]
    
        if getattr(self, "end", None) is not None:
            return self.tokenizer.source[:self.end]
    
        return self.tokenizer.source[:]


    # Map Python built-ins
    __repr__ = toXml
    __str__ = toXml
    
    
    def __eq__(self, other):
        return self is other

    def __bool__(self): 
        return True