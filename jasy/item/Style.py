#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import os, copy, zlib, fnmatch, re

import jasy.core.Console as Console 

import jasy.item.Abstract

import jasy.style.Util as Util

import jasy.style.tokenize.Tokenizer as Tokenizer

import jasy.style.parse.Parser as Parser
import jasy.style.parse.ScopeScanner as ScopeScanner

import jasy.style.clean.Permutate as Permutate
import jasy.style.clean.Unused as Unused

import jasy.style.process.Mixins as Mixins
import jasy.style.process.Variables as Variables
import jasy.style.process.Flatter as Flatter

import jasy.style.output.Compressor as Compressor



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
        return self.__printTokens()

    # Temporary development alias
    def getTree(self):
        return self.__getTree()




    def __printTokens(self, context=None):
        """
        Prints out a structured list of tokens 
        """

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
        """
        Returns the parsed tree
        """
        
        field = "style:tree[%s]" % self.id
        tree = self.project.getCache().read(field, self.mtime)
        if not tree:
            Console.info("Processing stylesheet %s %s...", Console.colorize(self.id, "bold"), Console.colorize("[%s]" % context, "cyan"))
            
            Console.indent()
            tree = Parser.parse(self.getText(), self.id)
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
                Permutate.patch(tree, permutation)
                Console.outdent()
        
            self.project.getCache().store(field, tree, self.mtime, True)
            Console.outdent()

        return tree








        
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




    def __resolveConditionals(self, tree):

        return

        # Scope Analyse von JavaScript?
        # Alle deklarierten und zugegriffenen Variablen auf den aktuellen Selektor oder das aktuelle StyleSheet hängen?
        # Nach jedem komplett Durchlauf durch alle Nodes überprüfen ob noch Werte übrig sind und Vorgang gegenfalls wiederholen
        # Ermittlung von nicht zur Verfügung stehenden Variablen

        def recurser(node):
            return False


        while recurser(tree):
            pass

        return tree




    def getCompressed(self, session, permutation=None, translation=None, optimization=None, formatting=None, context="compressed"):

        tree = self.getMergedTree(permutation, session)

        # PHASE 1
        # Resolving conditionals
        self.__resolveConditionals(tree)

        # PHASE 2
        # Trivial cleanups
        ScopeScanner.scan(tree)
        Unused.cleanup(tree)

        # PHASE 3
        # Resolve all mixins
        Mixins.processExtends(tree)
        Mixins.processMixins(tree)
        Mixins.processSelectors(tree)

        # PHASE 4
        # Post mixin cleanups
        ScopeScanner.scan(tree)
        Unused.cleanup(tree)

        # PHASE 5
        # Compute variables
        Variables.compute(tree)

        # PHASE 6
        # Flattening selectors
        Flatter.process(tree)

        # PHASE 7
        # Post scan to remove (hopefully) all variable/mixin access
        ScopeScanner.scan(tree)

        # DONE
        return Compressor.Compressor(formatting).compress(tree)
        
        
