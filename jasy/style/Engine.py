#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import copy

import jasy.core.Console as Console

import jasy.style.tokenize.Tokenizer as Tokenizer

import jasy.style.parse.Parser as Parser
import jasy.style.parse.ScopeScanner as ScopeScanner

import jasy.style.clean.Unused as Unused
import jasy.style.clean.Permutate as Permutate

import jasy.style.process.Mixins as Mixins
import jasy.style.process.Flatter as Flatter
import jasy.style.process.Executer as Executer

import jasy.style.output.Optimization as Optimization
import jasy.style.output.Formatting as Formatting

import jasy.style.output.Compressor as Compressor


def getTokenizer(text, fileId=None):
    """
    Returns a tokenizer for the given file content
    """

    return Tokenizer.Tokenizer(text, fileId, 0)



def getTree(text, fileId=None):
    """
    Returns a tree of nodes from the given text
    """

    return Parser.parse(text, fileId)



def permutateTree(tree, permutation=None):
    """
    Returns an optimized tree with permutations applied
    """

    if permutation:
        Permutate.patch(tree, permutation)
        return tree

    else:
        return tree



def reduceTree(tree, profile=None):
    """
    Applies all relevant modifications to the tree to allow compression to CSS
    """

    Console.info("Reducing tree: %s...", tree.fileId)
    Console.indent()

    # PHASE 2
    # Trivial cleanups
    ScopeScanner.scan(tree)
    Unused.cleanup(tree)

    # PHASE 3
    # Resolve all mixins
    Mixins.processMixins(tree)
    Mixins.processSelectors(tree)

    # PHASE 4
    # Assign selectors to mixins (support for extend)
    Mixins.processExtends(tree)

    # PHASE 5
    # Post mixin cleanups
    ScopeScanner.scan(tree)
    Unused.cleanup(tree)

    # PHASE 6
    # Execute variable resolution and method calls
    Executer.process(tree, profile)

    # PHASE 7
    # Flattening selectors
    Flatter.process(tree)

    # PHASE 8
    # Post scan to remove (hopefully) all variable/mixin access
    ScopeScanner.scan(tree)

    Console.outdent()

    return tree



def compressTree(tree, formatting=None):
    """
    Returns the compressed result from the given tree
    """

    return Compressor.Compressor(formatting).compress(tree)



def printTokens(text, fileId=None):
    """
    Prints out a structured list of tokens
    """

    tokenizer = getTokenizer(text, fileId)
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


