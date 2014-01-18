#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import json, copy

class AbstractNode(list):

    __slots__ = [
        # core data
        "line", "type", "tokenizer", "start", "end", "rel", "parent",

        # dynamic added data by other modules
        "comments", "scope", "values",

        # node type specific
        "value", "parenthesized", "fileId", "params",
        "name", "initializer", "condition", "assignOp",
        "thenPart", "elsePart", "statements",
        "statement", "variables", "names", "postfix"
    ]


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


    def getFileName(self):
        """
        Traverses up the tree to find a node with a fileId and returns it
        """

        node = self
        while node:
            fileId = getattr(node, "fileId", None)
            if fileId is not None:
                return fileId

            node = getattr(node, "parent", None)


    def getUnrelatedChildren(self):
        """Collects all unrelated children"""

        collection = []
        for child in self:
            if not hasattr(child, "rel"):
                collection.append(child)

        return collection


    def getChildrenLength(self, filter=True):
        """Number of (per default unrelated) children"""

        count = 0
        for child in self:
            if not filter or not hasattr(child, "rel"):
                count += 1
        return count


    def remove(self, kid):
        """Removes the given kid"""

        if not kid in self:
            raise Exception("Given node is no child!")

        if hasattr(kid, "rel"):
            delattr(self, kid.rel)
            del kid.rel
            del kid.parent

        list.remove(self, kid)


    def insert(self, index, kid):
        """Inserts the given kid at the given index"""

        if index is None:
            return self.append(kid)

        if hasattr(kid, "parent"):
            kid.parent.remove(kid)

        kid.parent = self

        return list.insert(self, index, kid)


    def insertAll(self, index, kids):
        """Inserts all kids starting with the given index"""

        if index is None:
            for kid in list(kids):
                self.append(kid)
        else:
            for pos, kid in enumerate(list(kids)):
                self.insert(index+pos, kid)


    def insertAllReplace(self, orig, kids):
        """Inserts all kids at the same position as the original node (which is removed afterwards)"""

        index = self.index(orig)
        for pos, kid in enumerate(list(kids)):
            self.insert(index+pos, kid)

        self.remove(orig)


    def append(self, kid, rel=None):
        """Appends the given kid with an optional relation hint"""

        # kid can be null e.g. [1, , 2].
        if kid:
            if hasattr(kid, "parent"):
                kid.parent.remove(kid)

            # Debug
            if not isinstance(kid, AbstractNode):
                raise Exception("Invalid kid: %s" % kid)

            if hasattr(kid, "tokenizer"):
                if hasattr(kid, "start"):
                    if not hasattr(self, "start") or self.start == None or kid.start < self.start:
                        self.start = kid.start

                if hasattr(kid, "end"):
                    if not hasattr(self, "end") or self.end == None or self.end < kid.end:
                        self.end = kid.end

            kid.parent = self

            # alias for function
            if rel != None:
                setattr(self, rel, kid)
                setattr(kid, "rel", rel)

        # Block None kids when they should be related
        if not kid and rel:
            return

        return list.append(self, kid)


    def replace(self, kid, repl):
        """Replaces the given kid with a replacement kid"""

        if repl in self:
            self.remove(repl)

        self[self.index(kid)] = repl

        if hasattr(kid, "rel"):
            repl.rel = kid.rel
            setattr(self, kid.rel, repl)

            # cleanup old kid
            delattr(kid, "rel")

        elif hasattr(repl, "rel"):
            # delete old relation on new child
            delattr(repl, "rel")

        delattr(kid, "parent")
        repl.parent = self

        return kid


    def toXml(self, format=True, indent=0, tab="  "):
        """Converts the node to XML"""

        lead = tab * indent if format else ""
        innerLead = tab * (indent+1) if format else ""
        lineBreak = "\n" if format else ""

        relatedChildren = []
        attrsCollection = []

        for name in self.__slots__:
            # "type" is used as node name - no need to repeat it as an attribute
            # "parent" is a relation to the parent node - for serialization we ignore these at the moment
            # "rel" is used internally to keep the relation to the parent - used by nodes which need to keep track of specific children
            # "start" and "end" are for debugging only
            if hasattr(self, name) and name not in ("type", "parent", "comments", "selector", "rel", "start", "end") and name[0] != "_":
                value = getattr(self, name)
                if isinstance(value, AbstractNode):
                    if hasattr(value, "rel"):
                        relatedChildren.append(value)

                elif type(value) in (bool, int, float, str, list, set, dict):
                    if type(value) == bool:
                        value = "true" if value else "false"
                    elif type(value) in (int, float):
                        value = str(value)
                    elif type(value) in (list, set, dict):
                        if type(value) == dict:
                            value = value.keys()
                        if len(value) == 0:
                            continue
                        try:
                            value = ",".join(value)
                        except TypeError as ex:
                            raise Exception("Invalid attribute list child at: %s: %s" % (name, ex))

                    attrsCollection.append('%s=%s' % (name, json.dumps(value)))

        attrs = (" " + " ".join(attrsCollection)) if len(attrsCollection) > 0 else ""

        comments = getattr(self, "comments", None)
        scope = getattr(self, "scope", None)
        selector = getattr(self, "selector", None)

        if len(self) == 0 and len(relatedChildren) == 0 and (not comments or len(comments) == 0) and not scope and not selector:
            result = "%s<%s%s/>%s" % (lead, self.type, attrs, lineBreak)

        else:
            result = "%s<%s%s>%s" % (lead, self.type, attrs, lineBreak)

            if comments:
                for comment in comments:
                    result += '%s<comment context="%s" variant="%s">%s</comment>%s' % (innerLead, comment.context, comment.variant, comment.text, lineBreak)

            if scope:
                for statKey in scope:
                    statValue = scope[statKey]
                    if statValue != None and len(statValue) > 0:
                        if type(statValue) is set:
                            statValue = ",".join(statValue)
                        elif type(statValue) is dict:
                            statValue = ",".join(statValue.keys())

                        result += '%s<stat name="%s">%s</stat>%s' % (innerLead, statKey, statValue, lineBreak)

            if selector:
                for entry in selector:
                    result += '%s<selector>%s</selector>%s' % (innerLead, entry, lineBreak)

            for child in self:
                if not child:
                    result += "%s<none/>%s" % (innerLead, lineBreak)
                elif not hasattr(child, "rel"):
                    result += child.toXml(format, indent+1)
                elif not child in relatedChildren:
                    raise Exception("Oops, irritated by non related: %s in %s - child says it is related as %s" % (child.type, self.type, child.rel))

            for child in relatedChildren:
                result += "%s<%s>%s" % (innerLead, child.rel, lineBreak)
                result += child.toXml(format, indent+2)
                result += "%s</%s>%s" % (innerLead, child.rel, lineBreak)

            result += "%s</%s>%s" % (lead, self.type, lineBreak)

        return result


    def __deepcopy__(self, memo):
        """Used by deepcopy function to clone AbstractNode instances"""

        CurrentClass = self.__class__

        # Create copy
        if hasattr(self, "tokenizer"):
            result = CurrentClass(tokenizer=self.tokenizer)
        else:
            result = CurrentClass(type=self.type)

        # Copy children
        for child in self:
            if child is None:
                list.append(result, None)
            else:
                # Using simple list appends for better performance
                childCopy = copy.deepcopy(child, memo)
                childCopy.parent = result
                list.append(result, childCopy)

        # Sync attributes
        # Note: "parent" attribute is handled by append() already
        for name in self.__slots__:
            if hasattr(self, name) and not name in ("parent", "tokenizer"):
                value = getattr(self, name)
                if value is None:
                    pass
                elif type(value) in (bool, int, float, str):
                    setattr(result, name, value)
                elif type(value) in (list, set, dict, CurrentClass):
                    setattr(result, name, copy.deepcopy(value, memo))
                # Scope can be assigned (will be re-created when needed for the copied node)
                elif name == "scope":
                    result.scope = self.scope

        return result


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
