#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import os, copy, fnmatch, re

import jasy.core.Console as Console

import jasy.item.Abstract

import jasy.style.Util as Util
import jasy.style.Engine as Engine

import jasy.core.MetaData as MetaData
import jasy.style.output.Compressor as Compressor


def includeGenerator(node, session):
    """
    A generator which yiels style items and include nodes
    for every include in the given root node
    """

    for child in node:
        if child.type == "include":
            valueNode = child[0]
            if valueNode.type in ("string", "identifier"):
                includeName = valueNode.value
            elif valueNode.type == "dot":
                includeName = Util.assembleDot(valueNode)
            else:
                raise Exception("Invalid include: %s" % valueNode)

            item = session.getStyleByName(includeName)
            if item is None:
                raise Exception("Did not find style sheet: %s" % item.name)

            yield item, child

        else:
            includeGenerator(child, session)



def collectFields(node, keys=None, condition=False):

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

    def __init__(self, inst, msg):
        self.__msg = msg
        self.__inst = inst

    def __str__(self):
        return "Error processing stylesheet %s: %s" % (self.__inst, self.__msg)



class StyleItem(jasy.item.Abstract.AbstractItem):

    kind = "style"

    def generateId(self, relpath, package):
        if package:
            fileId = "%s/" % package
        else:
            fileId = ""

        return (fileId + os.path.splitext(relpath)[0]).replace("/", ".")


    def __getTree(self):
        """
        Returns the abstract syntax tree
        """

        field = "style:tree[%s]" % self.id
        tree = self.project.getCache().read(field, self.mtime)
        if not tree:
            Console.info("Processing stylesheet %s...", Console.colorize(self.id, "bold"))

            Console.indent()
            tree = Engine.getTree(self.getText(), self.id)
            Console.outdent()

            self.project.getCache().store(field, tree, self.mtime, True)

        return tree



    def __getPermutatedTree(self, permutation=None):
        """
        Returns an permutated tree: a copy of the normal tree
        where the conditions are resolved based on the given permutation.
        """

        if permutation is None:
            return self.__getTree()

        permutation = self.filterPermutation(permutation)
        field = "style:permutated[%s]-%s" % (self.id, permutation)
        tree = self.project.getCache().read(field, self.mtime)

        if not tree:
            tree = copy.deepcopy(self.__getTree())

            Console.debug("Permutating tree...")
            Console.indent()
            Engine.permutateTree(tree, permutation)
            Console.outdent()

            # self.project.getCache().store(field, tree, self.mtime, True)

        return tree



    def getBreaks(self, permutation=None, items=None, warnings=True):
        """
        Returns all down-priorized dependencies. This are dependencies which are required to
        make the module work, but are not required being available before the current item.
        """

        meta = self.getMetaData(permutation)
        result = set()

        for entry in meta.breaks:
            if entry == self.id:
                pass
            elif entry in items and items[entry].kind == "style":
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



    def getDependencies(self, permutation=None, items=None, fields=None, warnings=True):
        """
        Returns a set of dependencies seen through the given list of known
        items (ignoring all unknown items in original set). This method also
        makes use of the meta data.
        """

        meta = self.getMetaData(permutation)
        result = set()

        # Manually defined names/classes
        for entry in meta.requires:
            if entry == self.id:
                pass
            elif entry in items and items[entry].kind == "style":
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



    def getMetaData(self, permutation):
        """
        Returns the meta data of this stylesheet
        """

        permutation = self.filterPermutation(permutation)

        field = "style:meta[%s]-%s" % (self.id, permutation)
        meta = self.project.getCache().read(field, self.mtime)
        if meta is None:
            meta = MetaData.MetaData(self.__getPermutatedTree(permutation))
            self.project.getCache().store(field, meta, self.mtime)

        return meta



    def getFields(self):
        """
        Returns the fields which are accessed by this stylesheet.
        """

        field = "style:fields[%s]" % self.id
        fields = self.project.getCache().read(field, self.mtime)
        if fields is None:
            fields = collectFields(self.__getTree())
            self.project.getCache().store(field, fields, self.mtime)

        return fields



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



    def getMergedMtime(self, profile):
        """
        Returns the newest modification date of the stylesheet (respecting all includes)
        """

        mtime = self.mtime
        permutation = self.filterPermutation(profile.getCurrentPermutation())

        # Work is on base of optimized tree
        tree = self.__getPermutatedTree(permutation)

        # Run the actual resolver engine and figure out newest mtime
        for item, include in includeGenerator(tree, profile.getSession()):

            mtime = max(mtime, item.getMergedMtime(profile))

        return mtime



    def getMergedTree(self, profile):
        """
        Returns the merged (includes resolved) and optimized (permutation values applied) tree.
        """

        # Work is on base of optimized tree
        tree = self.__getPermutatedTree(profile.getCurrentPermutation())

        # Copying original tree
        tree = copy.deepcopy(tree)

        # Run the actual resolver engine
        for item, include in includeGenerator(tree, profile.getSession()):

            # Use merged tree for children as well...
            childRoot = item.getMergedTree(profile)

            # Copy it for being able to freely modify it
            childRoot = copy.deepcopy(childRoot)

            # Then replace it with include node
            include.parent.replace(include, childRoot)

        return tree



    def getCompressed(self, profile):
        """
        Returns the compressed CSS code of this stylesheet.
        """

        field = "style:compressed[%s]-%s" % (self.id, profile.getId())
        mtime = self.getMergedMtime(profile)
        compressed = self.project.getCache().read(field, mtime)

        if compressed is None:

            # Start with the merged tree (includes resolved)
            tree = self.getMergedTree(profile)

            # Read out profile config
            optimization = profile.getCurrentOptimization()
            formatting = profile.getCurrentFormatting()

            # Reduce tree
            Engine.reduceTree(tree, profile)

            # Compress tree
            compressed = Compressor.Compressor(formatting).compress(tree)

            # Store in cache
            # self.project.getCache().store(field, compressed, mtime)

        return compressed



