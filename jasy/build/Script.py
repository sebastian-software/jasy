#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import jasy.core.Console as Console

from jasy.item.Class import ClassError
from jasy.item.Class import ClassItem

from jasy.js.Resolver import Resolver
import jasy.js.output.Optimization as ScriptOptimization
import jasy.js.output.Formatting as ScriptFormatting

class ScriptBuilder:

    # --------------------------------------------------------------------------------------------
    #   ESSENTIALS
    # --------------------------------------------------------------------------------------------

    def __init__(self, profile):

        self.__profile = profile

        self.__session = profile.getSession()
        self.__assetManager = profile.getAssetManager()
        self.__fileManager = profile.getFileManager()

        self.__outputPath = os.path.join(destinationFolder, profile.getJsOutputFolder())

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
            if assetData:
                assetClassItem = session.getVirtualItem("jasy.generated.AssetData", ClassItem, "jasy.Asset.addData(%s);" % assetData, ".js")
                resolver.add(assetClassItem, prepend=True)

        # 5. Add translation data
        if not inlineTranslations:
            translationBundle = session.getTranslationBundle(profile.getCurrentLocale())
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
            profile = self.__profile
            session = self.__session

            result = []

            for item in items:
                compressed = item.getCompressed(profile)

                if self.__addDividers:
                    result.append("// FILE ID: %s\n%s\n\n" % (item.getId(), compressed))
                else:
                    result.append(compressed)

        except ClassError as error:
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

    def storeKernelScript(self, fileName, bootCode=""):

        Console.info("Generating kernel script...")
        Console.indent()

        # Export all profile data for the kernel
        items = self.__profile.getSetupClasses().values()

        # Transfer all hard-wired fields into a permutation
        self.__profile.setStaticPermutation()

        # Sort and compress
        sortedClasses = self.__sortScriptItems(items, bootCode, inlineTranslations=True)
        compressedCode = self.__compressScripts(sortedClasses)
        self.__fileManager.writeFile(os.path.join(self.__outputPath, fileName), compressedCode)
        self.__kernelScripts = sortedClasses

        Console.outdent()


    def storeLoaderScript(self, items, fileName, bootCode=""):

        Console.info("Generating loader script...")
        Console.indent()

        sortedClasses = self.__sortScriptItems(items, bootCode, filterBy=self.__kernelScripts)
        loaderCode = self.__generateScriptLoader(sortedClasses)
        self.__fileManager.writeFile(os.path.join(self.__outputPath, fileName), loaderCode)

        Console.outdent()


    def storeCompressedScript(self, items, fileName, bootCode=""):

        Console.info("Generating compressed script...")
        Console.indent()

        sortedClasses = self.__sortScriptItems(items, bootCode, filterBy=self.__kernelScripts, inlineTranslations=True)
        compressedCode = self.__compressScripts(sortedClasses)
        self.__fileManager.writeFile(os.path.join(self.__outputPath, fileName), compressedCode)

        Console.outdent()
