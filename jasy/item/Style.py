#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import os, copy, fnmatch, re

import jasy.core.Console as Console 

import jasy.item.Abstract

import jasy.style.Util as Util
import jasy.style.Engine as Engine

import jasy.style.tokenize.Tokenizer as Tokenizer

import jasy.style.parse.Parser as Parser
import jasy.style.parse.ScopeScanner as ScopeScanner

import jasy.style.clean.Unused as Unused

import jasy.style.process.Mixins as Mixins
import jasy.style.process.Variables as Variables
import jasy.style.process.Flatter as Flatter

import jasy.core.MetaData as MetaData
import jasy.style.output.Compressor as Compressor



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
    
    def __getTree(self, context=None):
        """
        Returns the parsed tree
        """
        
        field = "style:tree[%s]" % self.id
        tree = self.project.getCache().read(field, self.mtime)
        if not tree:
            Console.info("Processing stylesheet %s %s...", Console.colorize(self.id, "bold"), Console.colorize("[%s]" % context, "cyan"))
            
            Console.indent()
            tree = Engine.getTree(self.getText(), self.id)
            Console.outdent()
            
            self.project.getCache().store(field, tree, self.mtime, True)
        
        return tree
    
    
    def __getOptimizedTree(self, permutation=None, context=None):
        """
        Returns an optimized tree with permutations applied
        """

        field = "style:opt-tree[%s]-%s" % (self.id, permutation)
        tree = self.project.getCache().read(field, self.mtime)
        if not tree:
            tree = copy.deepcopy(self.__getTree("%s:plain" % context))

            # Logging
            msg = "Processing stylesheet %s" % Console.colorize(self.id, "bold")
            if permutation:
                msg += Console.colorize(" (%s)" % permutation, "grey")
            if context:
                msg += Console.colorize(" [%s]" % context, "cyan")
                
            Console.info("%s..." % msg)
            Console.indent()

            # Apply permutation
            if permutation:
                Console.debug("Patching tree with permutation: %s", permutation)
                Console.indent()
                Engine.permutateTree(tree, permutation)
                Console.outdent()
        
            self.project.getCache().store(field, tree, self.mtime, True)
            Console.outdent()

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

        permutation = self.filterPermutation(permutation)
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


    def getMetaData(self, permutation=None):
        permutation = self.filterPermutation(permutation)

        field = "style:meta[%s]-%s" % (self.id, permutation)
        meta = self.project.getCache().read(field, self.mtime)
        if meta is None:
            meta = MetaData.MetaData(self.__getOptimizedTree(permutation, "meta"))
            self.project.getCache().store(field, meta, self.mtime)
            
        return meta

        
    def getFields(self):
        field = "style:fields[%s]" % (self.id)
        fields = self.project.getCache().read(field, self.mtime)
        if fields is None:
            fields = collectFields(self.__getTree(context="fields"))
            self.project.getCache().store(field, fields, self.mtime)
        
        return fields
        
        
    def filterPermutation(self, permutation):
        if permutation:
            fields = self.getFields()
            if fields:
                return permutation.filter(fields)

        return None
        


    def getMergedTree(self, permutation, session):
        """
        Returns the merged (includes resolved) and optimized (permutation values injected) tree.
        """

        def resolveIncludesRecurser(node):
            for child in node:
                if child.type == "include":
                    valueNode = child[0]
                    if valueNode.type in ("string", "identifier"):
                        includeName = valueNode.value
                    elif valueNode.type == "dot":
                        includeName = Util.assembleDot(valueNode)
                    else:
                        raise Exception("Invalid include: %s" % valueNode)

                    childStyleItem = session.getStyleByName(includeName)

                    if childStyleItem is None:
                        raise Exception("Did not find style sheet: %s" % includeName)

                    # Use merged tree for children as well...
                    childRoot = childStyleItem.getMergedTree(permutation, session)

                    # and copy it for being free to modify it
                    childRoot = copy.deepcopy(childRoot)

                    node.replace(child, childRoot)

                else:
                    resolveIncludesRecurser(child)

        # Work is on base of optimized tree
        tree = self.__getOptimizedTree(permutation, "includes")
        
        # Copying original tree
        tree = copy.deepcopy(tree)

        # Run the actual resolver engine
        resolveIncludesRecurser(tree)

        return tree




    def getCompressed(self, session, permutation=None, translation=None, optimization=None, formatting=None, context="compressed"):

        # Disable translation for caching / patching when not actually used
        if translation and not self.getTranslations():
            translation = None
        
        field = "style:compressed[%s]-%s-%s-%s-%s" % (self.id, permutation, translation, optimization, formatting)
        compressed = self.project.getCache().read(field, self.mtime)
        if compressed == None:

            # Start with the merged tree (includes resolved)
            tree = self.getMergedTree(permutation, session)

            # Reduce tree
            Engine.reduceTree(tree)

            # Compress tree
            compressed = Compressor.Compressor(formatting).compress(tree)

            # Store in cache
            self.project.getCache().store(field, compressed, self.mtime)

        return compressed


    def getTranslations(self):
        # TODO
        return None

        field = "style:translations[%s]" % (self.id)
        result = self.project.getCache().read(field, self.mtime)
        if result is None:
            result = jasy.js.optimize.Translation.collectTranslations(self.__getTree(context="i18n"))
            self.project.getCache().store(field, result, self.mtime)

        return result        


