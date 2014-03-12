#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import os

import jasy.core.Console as Console

from jasy.item.Script import ScriptError
from jasy.item.Script import ScriptItem

import jasy.script.Resolver as ScriptResolver
from jasy.script.Resolver import Resolver

import jasy.script.output.Optimization as ScriptOptimization
import jasy.script.output.Formatting as ScriptFormatting

class ScriptBuilder:

    # --------------------------------------------------------------------------------------------
    #   ESSENTIALS
    # --------------------------------------------------------------------------------------------

    def __init__(self, profile):

        self.__profile = profile

        self.__session = profile.getSession()
        self.__assetManager = profile.getAssetManager()
        self.__fileManager = profile.getFileManager()

        self.__outputPath = os.path.join(profile.getDestinationPath(), profile.getJsOutputFolder())

        self.__kernelScripts = []

        self.__scriptOptimization = ScriptOptimization.Optimization()
        self.__scriptFormatting = ScriptFormatting.Formatting()



        compressionLevel = profile.getCompressionLevel()
        formattingLevel = profile.getFormattingLevel()

        self.__addDividers = formattingLevel > 0

        if compressionLevel > 0:
            self.__scriptOptimization.enable("variables")
            self.__scriptOptimization.enable("declarations")

        if compressionLevel > 1:
            self.__scriptOptimization.enable("blocks")
            self.__scriptOptimization.enable("privates")

        if formattingLevel > 1:
            self.__scriptFormatting.enable("semicolon")
            self.__scriptFormatting.enable("comma")


    def __sortScriptItems(self, items, bootCode=None, filterBy=None, inlineTranslations=False):

        profile = self.__profile
        session = self.__session

        # 1. Add given set of items
        resolver = Resolver(profile)
        for item in items:
            resolver.add(item)

        # 2. Add optional boot code
        if bootCode:
            bootScriptItem = session.getVirtualItem("jasy.generated.BootCode", ScriptItem, "(function(){%s})();" % bootCode, ".js")
            resolver.add(bootScriptItem)

        # 3. Check for asset usage
        includedScripts = resolver.getIncluded()
        usesAssets = False
        for item in includedScripts:
            if item.getId() == "jasy.Asset":
                usesAssets = True
                break

        # 4. Add asset data if needed
        if usesAssets:
            assetData = self.__assetManager.exportToJson(includedScripts)
            if assetData:
                assetScriptItem = session.getVirtualItem("jasy.generated.AssetData", ScriptItem, "jasy.Asset.addData(%s);" % assetData, ".js")
                resolver.add(assetScriptItem, prepend=True)

        # 5. Add translation data
        if not inlineTranslations:
            translationBundle = session.getTranslationBundle(profile.getCurrentLocale())
            if translationBundle:
                translationData = translationBundle.export(includedScripts)
                if translationData:
                    translationScriptItem = session.getVirtualItem("jasy.generated.TranslationData", ScriptItem, "jasy.Translate.addData(%s);" % translationData, ".js")
                    resolver.add(translationScriptItem, prepend=True)

        # 6. Sorting items
        sortedScripts = resolver.getSorted()

        # 7. Apply filter
        if filterBy:
            filteredScripts = []
            for item in sortedScripts:
                if not item in filterBy:
                    filteredScripts.append(item)

            sortedScripts = filteredScripts

        return sortedScripts


    def __compressScripts(self, items):
        try:
            profile = self.__profile
            session = self.__session

            result = []

            for item in items:
                compressed = item.getCompressed(profile)

                if self.__addDividers:
                    result.append("// FILE ID: %s\n%s\n\n" % (item.getId(), compressed))
                else:
                    result.append(compressed)

        except ScriptError as error:
            raise UserError("Error during script compression! %s" % error)

        return "".join(result)


    def __generateScriptLoader(self, items):

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
            # Ignore already compressed items
            if item.getId() in ("core.io.Script", "core.io.Queue"):
                continue

            path = item.getPath()

            # Support for multi path items
            # (typically in projects with custom layout/structure e.g. 3rd party)
            if type(path) is list:
                for singleFileName in path:
                    files.append(main.toRelativeUrl(singleFileName))

            else:
                files.append(main.toRelativeUrl(path))

        if self.__addDividers:
            loaderList = '"%s"' % '",\n"'.join(files)
        else:
            loaderList = '"%s"' % '","'.join(files)

        code += 'core.io.Queue.load([%s], null, null, true);' % loaderList
        return code




    # --------------------------------------------------------------------------------------------
    #   PUBLIC API
    # --------------------------------------------------------------------------------------------

    def getWorkingPath(self):
        # Locations inside scripts are always relative to the application root folder
        # aka the folder where HTML files are loaded from
        return self.__profile.getDestinationPath()


    def buildKernel(self, fileId):
        if not fileId:
            return

        self.__profile.setWorkingPath(self.getWorkingPath())
        self.storeKernelScript("kernel.js", bootCode="%s.boot();" % fileId)


    def buildPart(self, partId, fileId):
        if not fileId:
            return

        Console.info("Generating script (%s)...", fileId)
        Console.indent()

        self.__profile.setWorkingPath(self.getWorkingPath())
        ScriptItems = ScriptResolver.Resolver(self.__profile).add(fileId).getSorted()

        if self.__profile.getUseSource():
            self.storeLoaderScript(ScriptItems, "%s-{{id}}.js" % partId, "new %s;" % fileId)
        else:
            self.storeCompressedScript(ScriptItems, "%s-{{id}}.js" % partId, "new %s;" % fileId)

        Console.outdent()


    def storeKernelScript(self, fileName, bootCode=""):

        Console.info("Generating kernel script...")
        Console.indent()

        # Export all profile data for the kernel
        items = self.__profile.getSetupScripts().values()

        # Transfer all hard-wired fields into a permutation
        self.__profile.setStaticPermutation()

        # Sort and compress
        sortedScripts = self.__sortScriptItems(items, bootCode, inlineTranslations=True)
        compressedCode = self.__compressScripts(sortedScripts)
        self.__fileManager.writeFile(os.path.join(self.__outputPath, fileName), compressedCode)
        self.__kernelScripts = sortedScripts

        Console.outdent()


    def storeLoaderScript(self, items, fileName, bootCode=""):

        Console.info("Generating loader script...")
        Console.indent()

        sortedScripts = self.__sortScriptItems(items, bootCode, filterBy=self.__kernelScripts)
        loaderCode = self.__generateScriptLoader(sortedScripts)
        self.__fileManager.writeFile(os.path.join(self.__outputPath, fileName), loaderCode)

        Console.outdent()


    def storeCompressedScript(self, items, fileName, bootCode=""):

        Console.info("Generating compressed script...")
        Console.indent()

        sortedScripts = self.__sortScriptItems(items, bootCode, filterBy=self.__kernelScripts, inlineTranslations=True)
        compressedCode = self.__compressScripts(sortedScripts)
        self.__fileManager.writeFile(os.path.join(self.__outputPath, fileName), compressedCode)

        Console.outdent()
