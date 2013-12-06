#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013 Sebastian Werner
#

class MetaData:
    """
    Data structure to hold all meta information.

    A instance of this class is typically created by processing all
    meta data relevant tags of all doc comments in the given node structure.

    Hint: Must be a clean data class without links to other
    systems for optiomal cachability using Pickle
    """

    __slots__ = [ "requires", "optionals", "breaks", "assets" ]


    def __init__(self, tree):
        self.requires = set()
        self.optionals = set()
        self.breaks = set()
        self.assets = set()

        self.parse(tree)


    def parse(self, node):
        """
        The internal inspection routine to add relevant data from comments
        """

        # Parse meta
        if node.type == "meta":

            child = node[0]
            value = child.value

            if node.name == "require":
                self.requires.add(value)

            if node.name == "load":
                self.requires.add(value)
                self.breaks.add(value)

            if node.name == "optional":
                self.optionals.add(value)

            if node.name == "break":
                self.breaks.add(value)

            if node.name == "asset":
                self.assets.add(value)


        # Parse comments
        comments = getattr(node, "comments", None)
        if comments:
            for comment in comments:
                commentTags = comment.getTags()
                if commentTags:

                    if "require" in commentTags:
                        self.requires.update(commentTags["require"])

                    if "load" in commentTags:
                        # load is a special combination shorthand for requires + breaks
                        # This means load it but don't require it being loaded first
                        self.requires.update(commentTags["load"])
                        self.breaks.update(commentTags["load"])

                    if "optional" in commentTags:
                        self.optionals.update(commentTags["optional"])

                    if "break" in commentTags:
                        self.breaks.update(commentTags["break"])

                    if "asset" in commentTags:
                        self.assets.update(commentTags["asset"])

        # Process children
        for child in node:
            if child is not None:
                self.parse(child)

