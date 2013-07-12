#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import os, copy, zlib, fnmatch, re

import jasy.style.tokenize.Tokenizer as Tokenizer
import jasy.style.parse.Parser as Parser
import jasy.style.clean.Permutate
import jasy.style.output.Optimization
from jasy.style.output.Compressor import Compressor
from jasy.style.Util import assembleDot


import jasy.core.Permutation
import jasy.core.Console as Console 

import jasy.item.Abstract

defaultOptimization = jasy.style.output.Optimization.Optimization()
defaultPermutation = jasy.core.Permutation.getPermutation({"debug" : False})


def collectFields(node, keys=None):
    
    if keys is None:
        keys = set()
    
    if node.type == "select":
        keys.add(node.value)

    # Process children
    for child in reversed(node):
        if child != None:
            collectFields(child, keys)
            
    return keys


class StyleError(Exception):
    def __init__(self, inst, msg):
        self.__msg = msg
        self.__inst = inst
        
    def __str__(self):
        return "Error processing stylesheet %s: %s" % (self.__inst, self.__msg)


class StyleItem(jasy.item.Abstract.AbstractItem):
    
    kind = "style"
    
    # Temporary development alias
    def getTokens(self):
        return self.__getTokens()

    # Temporary development alias
    def getTree(self):
        return self.__getTree()




    def __getTokens(self, context=None):
        tokenizer = Tokenizer.Tokenizer(self.getText(), self.id, 0)
        indent = 0

        while tokenizer.get() and not tokenizer.done():
            tokenType = tokenizer.token.type 
            tokenValue = getattr(tokenizer.token, "value", None)
            if tokenType == "left_curly":
                indent += 1
                continue
            elif tokenType == "right_curly":
                indent -= 1
                continue

            if tokenValue is not None:
                Console.info("%s%s: %s" % (indent * "  ", tokenType, tokenValue))
            else:
                Console.info("%s%s" % (indent * "  ", tokenType))


    def __getTree(self, context=None):
        
        field = "tree[%s]" % self.id
        tree = self.project.getCache().read(field, self.mtime)
        if not tree:
            Console.info("Processing stylesheet %s %s...", Console.colorize(self.id, "bold"), Console.colorize("[%s]" % context, "cyan"))
            
            Console.indent()
            tree = Parser.parse(self.getText(), self.id)
            Console.outdent()
            
            self.project.getCache().store(field, tree, self.mtime, True)
        
        return tree
    
    
    def __getOptimizedTree(self, permutation=None, context=None):
        """Returns an optimized tree with permutations applied"""

        field = "opt-tree[%s]-%s" % (self.id, permutation)
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
                jasy.style.clean.Permutate.patch(tree, permutation)
                Console.outdent()
        
            self.project.getCache().store(field, tree, self.mtime, True)
            Console.outdent()

        return tree



    def getDependencies(self, permutation=None, classes=None, fields=None, warnings=True):
        """ 
        Returns a set of dependencies
        """

        permutation = self.filterPermutation(permutation)

        result = set()

        # Match fields with current permutation and give detection classes
        # Add detection classes of fields which are accessed but not permutated
        # to the list of dependencies for this class.
        if fields:
            accessedFields = self.getFields()
            if accessedFields:
                for fieldName in accessedFields:
                    if permutation is None or not permutation.has(fieldName):
                        if fieldName in fields:
                            result.add(fields[fieldName])

        # TODO: Handle imports



        return result

        
    def getFields(self):
        field = "fields[%s]" % (self.id)
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
                        includeName = assembleDot(valueNode)
                    else:
                        raise Exception("Invalid include: %s" % valueNode)

                    childStyleItem = session.getStyleByName(includeName)

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


        
    def getCompressed(self, permutation=None, optimization=None, formatting=None, context="compressed"):

        return

        permutation = self.filterPermutation(permutation)
        
        field = "compressed[%s]-%s-%s-%s" % (self.id, permutation, optimization, formatting)
        compressed = self.project.getCache().read(field, self.mtime)
        if compressed == None:
            tree = self.__getOptimizedTree(permutation, context)
            
            # Copying original tree
            tree = copy.deepcopy(tree)

            if optimization:
                tree = copy.deepcopy(tree)

                try:
                    optimization.apply(tree)
                except jasy.style.output.Optimization.Error as error:
                    raise StyleError(self, "Could not compress class! %s" % error)
                
            compressed = Compressor(formatting).compress(tree)
            self.project.getCache().store(field, compressed, self.mtime)
            
        return compressed
            
            
    def getSize(self):
        field = "size[%s]" % self.id
        size = self.project.getCache().read(field, self.mtime)
        
        if size is None:
            compressed = self.getCompressed(context="size")
            optimized = self.getCompressed(permutation=defaultPermutation, optimization=defaultOptimization, context="size")
            zipped = zlib.compress(optimized.encode("utf-8"))
            
            size = {
                "compressed" : len(compressed),
                "optimized" : len(optimized),
                "zipped" : len(zipped)
            }
            
            self.project.getCache().store(field, size, self.mtime)
            
        return size
        
        
