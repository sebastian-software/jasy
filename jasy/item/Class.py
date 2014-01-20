#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import os, copy, fnmatch, re

import jasy.core.MetaData as MetaData
import jasy.core.Console as Console
import jasy.item.Abstract
import jasy.js.parse.Parser as Parser
import jasy.js.parse.ScopeScanner as ScopeScanner
import jasy.js.clean.DeadCode
import jasy.js.clean.Unused
import jasy.js.clean.Permutate
import jasy.js.optimize.Translation
import jasy.js.output.Optimization
import jasy.js.api.Data
import jasy.js.output.Compressor as Compressor
import jasy.js.util as Util

from jasy import UserError

try:
    from pygments import highlight
    from pygments.lexers import JavascriptLexer
    from pygments.formatters import HtmlFormatter
except:
    highlight = None


aliases = {}


def collectFields(node, keys=None):

    if keys is None:
        keys = set()

    # Always the first parameter
    # Supported calls: jasy.Env.isSet(key, expected?), jasy.Env.getValue(key), jasy.Env.select(key, map)
    calls = ("jasy.Env.isSet", "jasy.Env.getValue", "jasy.Env.select")
    if node.type == "dot" and node.parent.type == "call" and Util.assembleDot(node) in calls:
        stringNode = node.parent[1][0]
        if stringNode.type == "string":
            keys.add(stringNode.value)
        elif stringNode.type == "identifier":
            # Tolerate identifiers for supporting dynamic requests e.g. for asset placeholders
            pass
        else:
            raise Exception("Could not handle non string type in jasy.Env call at line: %s" % node.line)



    # Process children
    for child in reversed(node):
        if child != None:
            collectFields(child, keys)

    return keys



class ClassError(Exception):

    def __init__(self, inst, msg):
        self.__msg = msg
        self.__inst = inst

    def __str__(self):
        return "Error processing class %s: %s" % (self.__inst, self.__msg)



class ClassItem(jasy.item.Abstract.AbstractItem):

    kind = "class"

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

        field = "script:tree[%s]" % self.id
        tree = self.project.getCache().read(field, self.mtime)
        if not tree:
            Console.info("Processing class %s...", Console.colorize(self.id, "bold"))

            Console.indent()
            tree = Parser.parse(self.getText(), self.id)
            ScopeScanner.scan(tree)
            Console.outdent()

            self.project.getCache().store(field, tree, self.mtime, True)

        return tree


    def __getOptimizedTree(self, permutation=None):
        """
        Returns an optimized tree with permutations applied
        """

        field = "script:opt-tree[%s]-%s" % (self.id, permutation)
        tree = self.project.getCache().read(field, self.mtime)
        if not tree:
            tree = copy.deepcopy(self.__getTree())

            # Logging
            msg = "Optimizing class %s" % Console.colorize(self.id, "bold")
            if permutation:
                msg += Console.colorize(" (%s)" % permutation, "grey")

            Console.info("%s..." % msg)
            Console.indent()

            # Apply permutation
            if permutation:
                Console.debug("Patching tree with permutation: %s", permutation)
                Console.indent()
                jasy.js.clean.Permutate.patch(tree, permutation)
                Console.outdent()

            # Cleanups
            jasy.js.clean.DeadCode.cleanup(tree)
            ScopeScanner.scan(tree)
            jasy.js.clean.Unused.cleanup(tree)

            self.project.getCache().store(field, tree, self.mtime, True)
            Console.outdent()

        return tree



    def getBreaks(self, permutation=None, items=None):
        """
        Returns all down-priorized dependencies. This are dependencies which are required to
        make the module work, but are not required being available before the current item.
        """

        meta = self.getMetaData(permutation)

        result = set()

        for name in meta.breaks:
            if name != self.id and name in items and items[name].kind == "class":
                result.add(items[name])
            elif "*" in name:
                reobj = re.compile(fnmatch.translate(name))
                for className in items:
                    if className != self.id:
                        if reobj.match(className):
                            result.add(items[className])

        return result



    def getDependencies(self, permutation=None, items=None, fields=None, warnings=True):
        """
        Returns a set of dependencies seen through the given list of known
        classes (ignoring all unknown items in original set) and configured fields
        with their individual detection classes. This method also
        makes use of the meta data and the variable data.
        """

        permutation = self.filterPermutation(permutation)

        meta = self.getMetaData(permutation)
        scope = self.getScopeData(permutation)

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

        # Manually defined names/classes
        for name in meta.requires:
            if name != self.id and name in items and items[name].kind == "class":
                result.add(items[name])
            elif "*" in name:
                reobj = re.compile(fnmatch.translate(name))
                for className in items:
                    if className != self.id:
                        if reobj.match(className):
                            result.add(items[className])
            elif warnings:
                Console.warn("Missing class (required): %s in %s", name, self.id)

        # Globally modified names (mostly relevant when working without namespaces)
        for name in scope.shared:
            if name != self.id and name in items and items[name].kind == "class":
                result.add(items[name])

        # Add classes from detected package access
        for package in scope.packages:
            if package in aliases:
                className = aliases[package]
                if className in items:
                    result.add(items[className])
                    continue

            orig = package
            while True:
                if package == self.id:
                    break

                elif package in items and items[package].kind == "class":
                    aliases[orig] = package
                    result.add(items[package])
                    break

                else:
                    pos = package.rfind(".")
                    if pos == -1:
                        break

                    package = package[0:pos]

        # Manually excluded names/classes
        for name in meta.optionals:
            if name != self.id and name in items and items[name].kind == "class":
                result.remove(items[name])
            elif warnings:
                Console.warn("Missing class (optional): %s in %s", name, self.id)

        return result



    def getScopeData(self, permutation=None):
        """
        Returns the top level scope object which contains information about the
        global variable and package usage/influence.
        """

        permutation = self.filterPermutation(permutation)

        field = "script:scope[%s]-%s" % (self.id, permutation)
        scope = self.project.getCache().read(field, self.mtime)
        if scope is None:
            scope = self.__getOptimizedTree(permutation).scope
            self.project.getCache().store(field, scope, self.mtime)

        return scope



    def getApi(self, highlight=True):
        field = "script:api[%s]-%s" % (self.id, highlight)
        apidata = self.project.getCache().read(field, self.mtime, inMemory=False)
        if apidata is None:
            apidata = jasy.js.api.Data.ApiData(self.id, highlight)

            tree = self.__getTree()
            Console.indent()
            apidata.scanTree(tree)
            Console.outdent()

            metaData = self.getMetaData()
            apidata.addAssets(metaData.assets)
            for require in metaData.requires:
                apidata.addUses(require)
            for optional in metaData.optionals:
                apidata.removeUses(optional)

            apidata.addFields(self.getFields())

            self.project.getCache().store(field, apidata, self.mtime, inMemory=False)

        return apidata



    def getHighlightedCode(self):
        field = "script:highlighted[%s]" % self.id
        source = self.project.getCache().read(field, self.mtime)
        if source is None:
            if highlight is None:
                raise UserError("Could not highlight JavaScript code! Please install Pygments.")

            lexer = JavascriptLexer(tabsize=2)
            formatter = HtmlFormatter(full=True, style="autumn", linenos="table", lineanchors="line")
            source = highlight(self.getText(), lexer, formatter)

            self.project.getCache().store(field, source, self.mtime)

        return source



    def getMetaData(self, permutation=None):
        permutation = self.filterPermutation(permutation)

        field = "script:meta[%s]-%s" % (self.id, permutation)
        meta = self.project.getCache().read(field, self.mtime)
        if meta is None:
            meta = MetaData.MetaData(self.__getOptimizedTree(permutation))
            self.project.getCache().store(field, meta, self.mtime)

        return meta



    def getFields(self):
        field = "script:fields[%s]" % (self.id)
        fields = self.project.getCache().read(field, self.mtime)
        if fields is None:
            try:
                fields = collectFields(self.__getTree())
            except Exception as ex:
                raise Exception("Unable to collect fields in file %s: %s" % (self.id, ex))

            self.project.getCache().store(field, fields, self.mtime)

        return fields



    def getTranslations(self):
        field = "script:translations[%s]" % (self.id)
        result = self.project.getCache().read(field, self.mtime)
        if result is None:
            result = jasy.js.optimize.Translation.collectTranslations(self.__getTree())
            self.project.getCache().store(field, result, self.mtime)

        return result



    def filterPermutation(self, permutation):
        if permutation:
            fields = self.getFields()
            if fields:
                return permutation.filter(fields)

        return None



    def getCompressed(self, profile):
        field = "script:compressed[%s]-%s" % (self.id, profile.getId())
        compressed = self.project.getCache().read(field, self.mtime)
        if compressed == None:
            permutation = self.filterPermutation(profile.getCurrentPermutation())
            tree = self.__getOptimizedTree(permutation)

            translation = profile.getCurrentTranslation()
            optimization = profile.getCurrentOptimization()
            formatting = profile.getCurrentFormatting()

            if translation or optimization:
                tree = copy.deepcopy(tree)

                if translation:
                    jasy.js.optimize.Translation.optimize(tree, translation)

                if optimization:
                    try:
                        optimization.apply(tree)
                    except jasy.js.output.Optimization.Error as error:
                        raise ClassError(self, "Could not compress class! %s" % error)

            compressed = Compressor.Compressor(formatting).compress(tree)
            self.project.getCache().store(field, compressed, self.mtime)

        return compressed


