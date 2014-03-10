#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import os, copy, fnmatch, re

import jasy.core.Console as Console
import jasy.core.MetaData as MetaData
import jasy.item.Abstract as AbstractItem
import jasy.style.Util as Util
import jasy.style.Engine as Engine



def includeGenerator(node):
    """
    A generator which yiels include names and the origin include nodes
    for every include in the given root node
    """

    for child in node:
        if child:
            if child.type == "include":
                valueNode = child[0]
                if valueNode.type in ("string", "identifier"):
                    includeName = valueNode.value
                elif valueNode.type == "dot":
                    includeName = Util.assembleDot(valueNode)
                else:
                    raise Exception("Invalid include: %s" % valueNode)

                yield includeName, child

            else:
                includeGenerator(child)



def collectFields(node, keys=None, condition=False):
    """
    Collects all fields accessed by the given root node
    and all children. Returns a set of field names.
    """

    if keys is None:
        keys = set()

    if getattr(node, "rel", None) == "condition":
        condition = True

    elif node.type == "command" and node.name == "field":
        keys.add(node.params[0].value)

    elif condition and node.type == "identifier":
        keys.add(node.value)

    # Process children
    for child in reversed(node):
        if child != None:
            collectFields(child, keys, condition)

    return keys



class StyleError(Exception):
    """
    Error class used for issues during style processing
    """

    def __init__(self, inst, msg):
        self.__msg = msg
        self.__inst = inst

    def __str__(self):
        return "Error processing stylesheet %s: %s" % (self.__inst, self.__msg)



class StyleItem(AbstractItem.AbstractItem):

    kind = "jasy.Style"

    def generateId(self, relpath, package):
        """
        Generates the fileId of this item as being used by other modules
        """

        if package:
            packageId = "%s/" % package
        else:
            packageId = ""

        pathId = os.path.splitext(relpath)[0]

        return (packageId + pathId).replace("/", ".")


    def __getTree(self):
        """
        Returns the abstract syntax tree of the stylesheet.
        """

        field = "style:tree[%s]" % self.id
        tree = self.project.getCache().read(field, self.mtime)

        if not tree:
            Console.info("Parsing stylesheet %s...", Console.colorize(self.id, "bold"))

            Console.indent()
            tree = Engine.getTree(self.getText(), self.id)
            Console.outdent()

            self.project.getCache().store(field, tree, self.mtime, True)

        return tree



    def __getPermutatedTree(self, permutation=None):
        """
        Returns a permutated tree: a copy of the original tree
        where conditions based on the given permutation are resolved.
        """

        if permutation is None:
            return self.__getTree()

        permutation = self.filterPermutation(permutation)
        field = "style:permutated[%s]-%s" % (self.id, permutation)
        tree = self.project.getCache().read(field, self.mtime)

        if not tree:
            tree = copy.deepcopy(self.__getTree())

            Console.info("Permutating stylesheet %s...", Console.colorize(self.id, "bold"))
            Console.indent()
            Engine.permutateTree(tree, permutation)
            Console.outdent()

            self.project.getCache().store(field, tree, self.mtime, True)

        return tree



    def getDependencies(self, permutation=None, items=None, fields=None, warnings=True):
        """
        Returns a set of dependencies seen through the given list of known
        items (ignoring all unknown items in original set).
        """

        meta = self.getMetaData(permutation)
        result = set()

        # Manually defined names/classes
        for entry in meta.requires:
            if entry == self.id:
                pass
            elif entry in items and items[entry].kind == "jasy.Style":
                result.add(items[entry])
            elif "*" in entry:
                reobj = re.compile(fnmatch.translate(entry))
                for itemId in items:
                    if itemId != self.id:
                        if reobj.match(itemId):
                            result.add(items[itemId])
            elif warnings:
                Console.warn("Missing item for require command: %s in %s", entry, self.id)

        return result



    def getBreaks(self, permutation=None, items=None, warnings=True):
        """
        Returns all down-priorized dependencies. These are dependencies which are required to
        make the item work, but are not required being available before the current item.
        """

        meta = self.getMetaData(permutation)
        result = set()

        for entry in meta.breaks:
            if entry == self.id:
                pass
            elif entry in items and items[entry].kind == "jasy.Style":
                result.add(items[entry])
            elif "*" in entry:
                reobj = re.compile(fnmatch.translate(entry))
                for itemId in items:
                    if itemId != self.id:
                        if reobj.match(itemId):
                            result.add(items[itemId])
            elif warnings:
                Console.warn("Missing item for break command: %s in %s", entry, self.id)

        return result



    def getMetaData(self, permutation):
        """
        Returns the meta data of this stylesheet
        """

        permutation = self.filterPermutation(permutation)

        field = "style:meta[%s]-%s" % (self.id, permutation)
        meta = self.project.getCache().read(field, self.mtime)
        if meta is None:
            Console.debug("Collecting meta data %s...", Console.colorize(self.id, "bold"))
            meta = MetaData.MetaData(self.__getPermutatedTree(permutation))
            self.project.getCache().store(field, meta, self.mtime)

        return meta



    def getFields(self):
        """
        Returns the fields which are used by this stylesheet.
        """

        field = "style:fields[%s]" % self.id
        fields = self.project.getCache().read(field, self.mtime)
        if fields is None:
            Console.debug("Collecting fields %s...", Console.colorize(self.id, "bold"))
            fields = collectFields(self.__getTree())
            self.project.getCache().store(field, fields, self.mtime)

        return fields



    def getIncludes(self, permutation):
        """
        Returns the includes which are referenced by this stylesheet.
        """

        field = "style:includes[%s]" % self.id
        includes = self.project.getCache().read(field, self.mtime)
        if includes is None:
            Console.debug("Collecting includes %s...", Console.colorize(self.id, "bold"))
            includes = []
            for includeName, includeNode in includeGenerator(self.__getPermutatedTree(permutation)):
                includes.append(includeName)

            self.project.getCache().store(field, includes, self.mtime)

        return includes



    def filterPermutation(self, permutation):
        """
        Returns a new permutation which only contains information
        about the fields actually accessed in this stylesheet.
        """

        if permutation:
            fields = self.getFields()
            if fields:
                return permutation.filter(fields)

        return None



    def getModificationTime(self, profile):
        """
        Returns the modification date of the stylesheet
        (or the sum of modification dates when using includes)
        """

        mtime = self.mtime
        permutation = self.filterPermutation(profile.getCurrentPermutation())
        session = profile.getSession()

        mtime = self.mtime
        for includeName in self.getIncludes(permutation):
            styleItem = session.getStyleByName(includeName)
            if styleItem is None:
                raise Exception("Did not find style sheet: %s" % includeName)
            mtime += styleItem.getModificationTime(profile)

        return mtime



    def getMergedTree(self, profile):
        """
        Returns the merged (includes resolved) and optimized
        (permutation values applied) tree.
        """

        session = profile.getSession()

        # Work is on base of optimized tree
        tree = self.__getPermutatedTree(profile.getCurrentPermutation())

        # Copying original tree
        tree = copy.deepcopy(tree)

        # Run the actual resolver engine
        for includeName, includeNode in includeGenerator(tree):

            styleItem = session.getStyleByName(includeName)
            if styleItem is None:
                raise Exception("Did not find style sheet: %s" % includeName)

            # Use merged tree for children as well...
            childRoot = styleItem.getMergedTree(profile)

            # Copy it for being able to freely modify it
            childRoot = copy.deepcopy(childRoot)

            # Then replace it with include node
            includeNode.parent.replace(includeNode, childRoot)

        return tree



    def getCompressed(self, profile):
        """
        Returns the compressed CSS code of this item.
        """

        field = "style:compressed[%s]-%s" % (self.id, profile.getId())
        mtime = self.getModificationTime(profile)

        compressed = self.project.getCache().read(field, mtime)

        if compressed is None:

            Console.info("Compressing tree %s...", Console.colorize(self.id, "bold"))

            # Start with the merged tree (includes resolved)
            tree = self.getMergedTree(profile)

            # Reduce tree
            Engine.reduceTree(tree, profile)

            # Compress tree
            compressed = Engine.compressTree(tree, profile.getCompressionLevel(), profile.getFormattingLevel())

            # Store in cache
            self.project.getCache().store(field, compressed, mtime)

        return compressed

