#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013 Sebastian Werner
#

import os

import jasy.core.Console as Console

from jasy.core.Permutation import getPermutation
from jasy.item.Class import ClassError, ClassItem
from jasy.item.Style import StyleError, StyleItem
from jasy.js.Resolver import Resolver

from jasy import UserError

import jasy.js.output.Optimization as ScriptOptimization
import jasy.js.output.Formatting as ScriptFormatting

import jasy.style.output.Optimization as StyleOptimization
import jasy.style.output.Formatting as StyleFormatting

from jasy.core.FileManager import FileManager


class OutputManager:

    def __init__(self, session, assetManager=None, compressionLevel=1, formattingLevel=0):

        self.__session = session

        self.__assetManager = assetManager
        self.__fileManager = FileManager(session)
        self.__kernelClasses = []

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
            self.__styleFormatting.enable("selector")

        if formattingLevel > 1:
            self.__scriptFormatting.enable("semicolon")
            self.__scriptFormatting.enable("comma")
            self.__styleFormatting.enable("rule")


    def deployAssets(self, classes, assetFolder=None, hashNames=False):
        """
        Deploys assets for the given classes and all their dependencies

        :param classes: List of classes to deploy assets for
        :type classes: list
        :param assetFolder: Destination folder of assets (defaults to {{prefix}}/asset)
        :type assetFolder: string
        """

        Console.info("Deploying assets...")
        Console.indent()

        resolver = Resolver(self.__session)

        for className in classes:
            resolver.add(className)

        self.__assetManager.deploy(resolver.getIncluded(), assetFolder=assetFolder, hashNames=hashNames)

        Console.outdent()


    def __buildClassList(self, classes, bootCode=None, filterBy=None, inlineTranslations=False):

        session = self.__session

        # 1. Add given set of classes
        resolver = Resolver(session)
        for classItem in classes:
            resolver.add(classItem)

        # 2. Add optional boot code
        if bootCode:
            bootClassItem = session.getVirtualItem("jasy.generated.BootCode", ClassItem, "(function(){%s})();" % bootCode, ".js")
            resolver.add(bootClassItem)

        # 3. Check for asset usage
        includedClasses = resolver.getIncluded()
        usesAssets = False
        for classItem in includedClasses:
            if classItem.getId() == "jasy.Asset":
                usesAssets = True
                break

        # 4. Add asset data if needed
        if usesAssets:
            assetData = self.__assetManager.export(includedClasses)
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

        # 6. Sorting classes
        sortedClasses = resolver.getSorted()

        # 7. Apply filter
        if filterBy:
            filteredClasses = []
            for classObj in sortedClasses:
                if not classObj in filterBy:
                    filteredClasses.append(classObj)

            sortedClasses = filteredClasses

        return sortedClasses


    def __compressClasses(self, classes):
        try:
            session = self.__session
            result = []

            for classObj in classes:
                compressed = classObj.getCompressed(session.getCurrentPermutation(), session.getCurrentTranslationBundle(), self.__scriptOptimization, self.__scriptFormatting)

                if self.__addDividers:
                    result.append("// FILE ID: %s\n%s\n\n" % (classObj.getId(), compressed))
                else:
                    result.append(compressed)
                
        except ClassError as error:
            raise UserError("Error during class compression! %s" % error)

        return "".join(result)



    def __compressStyles(self, styles):
        try:
            session = self.__session
            result = []

            for styleObj in styles:
                compressed = styleObj.getCompressed(session, session.getCurrentPermutation(), session.getCurrentTranslationBundle(), self.__styleOptimization, self.__styleFormatting)

                if self.__addDividers:
                    result.append("/* FILE ID: %s */\n%s\n\n" % (styleObj.getId(), compressed))
                else:
                    result.append(compressed)
                
        except StyleError as error:
            raise UserError("Error during stylesheet compression! %s" % error)

        return "".join(result)



    def loadClasses(self, classes, urlPrefix=None):

        # For loading classes we require core.ui.Queue and core.io.Script 
        # being available. If they are not part of the kernel, we have to 
        # prepend them as compressed code into the resulting output.

        hasLoader = False
        hasQueue = False

        for classObj in self.__kernelClasses:
            className = classObj.getId()
            if className == "core.io.Queue":
                hasQueue = True
            elif className == "core.io.Script":
                hasLoader = True

        code = ""

        if not hasQueue or not hasLoader:
            compress = []
            if not hasQueue:
                compress.append("core.io.Queue")
            if not hasLoader:
                compress.append("core.io.Script")

            compressedList = self.__buildClassList(compress, filterBy=self.__kernelClasses)
            code += self.__compressClasses(compressedList)


        main = self.__session.getMain()
        files = []

        for classObj in classes:
            # Ignore already ompressed classes
            if classObj.getId() in ("core.io.Script", "core.io.Queue"):
                continue

            path = classObj.getPath()

            # Support for multi path classes 
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


    def storeKernelScript(self, fileName, bootCode=""):

        Console.info("Generating kernel script...")
        Console.indent()

        # Export all field data for the kernel
        classes = []
        fieldSetupClasses = self.__session.getFieldSetupClasses()
        for fieldName in fieldSetupClasses:
            classes.append(fieldSetupClasses[fieldName])

        # Transfer all hard-wired fields into a permutation
        self.__session.setStaticPermutation()

        # Sort and compress
        sortedClasses = self.__buildClassList(classes, bootCode, inlineTranslations=True)
        
        Console.info("Compressing %s items...", len(sortedClasses))
        compressedCode = self.__compressClasses(sortedClasses)

        # Write file to disk
        self.__fileManager.writeFile(fileName, compressedCode)

        # Remember kernel level classes
        self.__kernelClasses = sortedClasses

        Console.outdent()


    def storeLoaderScript(self, classes, fileName, bootCode="", urlPrefix=None):

        Console.info("Generating loader script...")
        Console.indent()

        # Build class list
        sortedClasses = self.__buildClassList(classes, bootCode, filterBy=self.__kernelClasses)
            
        # Compress code
        Console.info("Including %s items...", len(sortedClasses))
        loaderCode = self.loadClasses(sortedClasses, urlPrefix=urlPrefix)

        # Write file to disk
        self.__fileManager.writeFile(fileName, loaderCode)

        Console.outdent()


    def storeCompressedScript(self, classes, fileName, bootCode=""):

        Console.info("Generating compressed script...")
        Console.indent()

        # Build class list
        sortedClasses = self.__buildClassList(classes, bootCode, filterBy=self.__kernelClasses, inlineTranslations=True)
            
        # Compress code
        Console.info("Including %s items...", len(sortedClasses))
        compressedCode = self.__compressClasses(sortedClasses)

        # Write file to disk
        self.__fileManager.writeFile(fileName, compressedCode)

        Console.outdent()        


    def storeCompressedStylesheet(self, styles, fileName, bootCode=""):

        Console.info("Generating compressed stylesheet...")
        Console.indent()

        # Compress code
        Console.info("Including %s items...", len(styles))
        compressedCode = self.__compressStyles(styles)

        # Write file to disk
        self.__fileManager.writeFile(fileName, compressedCode)

        Console.outdent()



