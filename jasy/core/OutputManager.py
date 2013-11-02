#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013 Sebastian Werner
#

import os

import jasy.core.Console as Console

from jasy.core.Permutation import getPermutation
from jasy.item.Class import ClassError
from jasy.item.Class import ClassItem
from jasy.item.Style import StyleError
from jasy.item.Style import StyleItem
from jasy.js.Resolver import Resolver

from jasy import UserError

import jasy.js.output.Optimization as ScriptOptimization
import jasy.js.output.Formatting as ScriptFormatting

import jasy.style.output.Optimization as StyleOptimization
import jasy.style.output.Formatting as StyleFormatting

from jasy.core.FileManager import FileManager


class OutputManager:

    # --------------------------------------------------------------------------------------------
    #   ESSENTIALS
    # --------------------------------------------------------------------------------------------

    def __init__(self, session, assetManager=None, compressionLevel=1, formattingLevel=0):

        self.__session = session

        self.__assetManager = assetManager
        self.__fileManager = FileManager(session)

        self.__kernelScripts = []

        self.__scriptOptimization = ScriptOptimization.Optimization()
        self.__scriptFormatting = ScriptFormatting.Formatting()

        self.__styleOptimization = StyleOptimization.Optimization()
        self.__styleFormatting = StyleFormatting.Formatting()

        self.__addDividers = formattingLevel > 0

        if compressionLevel > 0:
            self.__scriptOptimization.enable("variables")
            self.__scriptOptimization.enable("declarations")

        if compressionLevel > 1:
            self.__scriptOptimization.enable("blocks")
            self.__scriptOptimization.enable("privates")

        if formattingLevel > 0:
            self.__styleFormatting.enable("blocks")

        if formattingLevel > 1:
            self.__scriptFormatting.enable("semicolon")
            self.__scriptFormatting.enable("comma")
            self.__styleFormatting.enable("statements")

        if formattingLevel > 2:
            self.__styleFormatting.enable("whitespace")
            self.__styleFormatting.enable("indent")



    # --------------------------------------------------------------------------------------------
    #   ASSETS
    # --------------------------------------------------------------------------------------------

    def deployAssets(self, items, assetFolder=None, hashNames=False):
        """
        Deploys assets for the given items and all their dependencies

        :param items: List of items to deploy assets for
        :type items: list
        :param assetFolder: Destination folder of assets (defaults to {{prefix}}/asset)
        :type assetFolder: string
        """

        Console.info("Deploying assets...")
        Console.indent()

        resolver = Resolver(self.__session)

        for itemId in items:
            resolver.add(itemId)

        self.__assetManager.deploy(resolver.getIncluded(), assetFolder=assetFolder, hashNames=hashNames)

        Console.outdent()




    # --------------------------------------------------------------------------------------------
    #   SCRIPT API
    # --------------------------------------------------------------------------------------------

    def __sortScriptItems(self, items, bootCode=None, filterBy=None, inlineTranslations=False):

        session = self.__session

        # 1. Add given set of items
        resolver = Resolver(session)
        for item in items:
            resolver.add(item)

        # 2. Add optional boot code
        if bootCode:
            bootClassItem = session.getVirtualItem("jasy.generated.BootCode", ClassItem, "(function(){%s})();" % bootCode, ".js")
            resolver.add(bootClassItem)

        # 3. Check for asset usage
        includedClasses = resolver.getIncluded()
        usesAssets = False
        for item in includedClasses:
            if item.getId() == "jasy.Asset":
                usesAssets = True
                break

        # 4. Add asset data if needed
        if usesAssets:
            assetData = self.__assetManager.exportToJson(includedClasses)
            assetClassItem = session.getVirtualItem("jasy.generated.AssetData", ClassItem, "jasy.Asset.addData(%s);" % assetData, ".js")
            resolver.add(assetClassItem, prepend=True)

        # 5. Add translation data
        if not inlineTranslations:
            translationBundle = self.__session.getCurrentTranslationBundle()
            if translationBundle:
                translationData = translationBundle.export(includedClasses)
                if translationData:
                    translationClassItem = session.getVirtualItem("jasy.generated.TranslationData", ClassItem, "jasy.Translate.addData(%s);" % translationData, ".js")
                    resolver.add(translationClassItem, prepend=True)

        # 6. Sorting items
        sortedClasses = resolver.getSorted()

        # 7. Apply filter
        if filterBy:
            filteredClasses = []
            for item in sortedClasses:
                if not item in filterBy:
                    filteredClasses.append(item)

            sortedClasses = filteredClasses

        return sortedClasses


    def __compressScripts(self, items):
        try:
            session = self.__session
            result = []

            for item in items:
                compressed = item.getCompressed(session.getCurrentPermutation(), session.getCurrentTranslationBundle(), self.__scriptOptimization, self.__scriptFormatting)

                if self.__addDividers:
                    result.append("// FILE ID: %s\n%s\n\n" % (item.getId(), compressed))
                else:
                    result.append(compressed)

        except ClassError as error:
            raise UserError("Error during script compression! %s" % error)

        return "".join(result)


    def __generateScriptLoader(self, items, urlPrefix=None):

        # For loading items we require core.ui.Queue and core.io.Script
        # being available. If they are not part of the kernel, we have to
        # prepend them as compressed code into the resulting output.

        hasLoader = False
        hasQueue = False

        for item in self.__kernelScripts:
            itemId = item.getId()
            if itemId == "core.io.Queue":
                hasQueue = True
            elif itemId == "core.io.Script":
                hasLoader = True

        code = ""

        if not hasQueue or not hasLoader:
            compress = []
            if not hasQueue:
                compress.append("core.io.Queue")
            if not hasLoader:
                compress.append("core.io.Script")

            compressedList = self.__sortScriptItems(compress, filterBy=self.__kernelScripts)
            code += self.__compressScripts(compressedList)

        main = self.__session.getMain()
        files = []

        for item in items:
            # Ignore already ompressed items
            if item.getId() in ("core.io.Script", "core.io.Queue"):
                continue

            path = item.getPath()

            # Support for multi path items
            # (typically in projects with custom layout/structure e.g. 3rd party)
            if type(path) is list:
                for singleFileName in path:
                    files.append(main.toRelativeUrl(singleFileName, urlPrefix))

            else:
                files.append(main.toRelativeUrl(path, urlPrefix))

        if self.__addDividers:
            loaderList = '"%s"' % '",\n"'.join(files)
        else:
            loaderList = '"%s"' % '","'.join(files)

        code += 'core.io.Queue.load([%s], null, null, true);' % loaderList
        return code




    # --------------------------------------------------------------------------------------------
    #   STYLE API
    # --------------------------------------------------------------------------------------------

    def __compressStyles(self, styles):
        try:
            session = self.__session
            result = []

            for styleObj in styles:
                compressed = styleObj.getCompressed(session, session.getCurrentPermutation(), self.__styleOptimization, self.__styleFormatting)

                if self.__addDividers:
                    result.append("/* FILE ID: %s */\n%s\n\n" % (styleObj.getId(), compressed))
                else:
                    result.append(compressed)

        except StyleError as error:
            raise UserError("Error during stylesheet compression! %s" % error)

        return "".join(result)




    # --------------------------------------------------------------------------------------------
    #   PUBLIC API
    # --------------------------------------------------------------------------------------------

    def storeKernelScript(self, fileName, bootCode=""):

        Console.info("Generating kernel script...")
        Console.indent()

        # Export all field data for the kernel
        items = []
        fieldSetupClasses = self.__session.getFieldSetupClasses()
        for fieldName in fieldSetupClasses:
            items.append(fieldSetupClasses[fieldName])

        # Transfer all hard-wired fields into a permutation
        self.__session.setStaticPermutation()

        # Sort and compress
        sortedClasses = self.__sortScriptItems(items, bootCode, inlineTranslations=True)
        compressedCode = self.__compressScripts(sortedClasses)
        self.__fileManager.writeFile(fileName, compressedCode)
        self.__kernelScripts = sortedClasses

        Console.outdent()


    def storeLoaderScript(self, items, fileName, bootCode="", urlPrefix=None):

        Console.info("Generating loader script...")
        Console.indent()

        sortedClasses = self.__sortScriptItems(items, bootCode, filterBy=self.__kernelScripts)
        loaderCode = self.__generateScriptLoader(sortedClasses, urlPrefix=urlPrefix)
        self.__fileManager.writeFile(fileName, loaderCode)

        Console.outdent()


    def storeCompressedScript(self, items, fileName, bootCode=""):

        Console.info("Generating compressed script...")
        Console.indent()

        sortedClasses = self.__sortScriptItems(items, bootCode, filterBy=self.__kernelScripts, inlineTranslations=True)
        compressedCode = self.__compressScripts(sortedClasses)
        self.__fileManager.writeFile(fileName, compressedCode)

        Console.outdent()


    def storeCompressedStylesheet(self, styles, fileName):

        Console.info("Generating compressed stylesheet...")
        Console.indent()

        # Resolve placeholders first
        fileName = self.__session.expandFileName(fileName)
        relativeToMain = self.__session.getMain().toRelativeUrl(fileName)

        compressedCode = self.__compressStyles(styles)
        self.__fileManager.writeFile(fileName, compressedCode)

        Console.outdent()



