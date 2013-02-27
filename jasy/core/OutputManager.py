#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013 Sebastian Werner
#

import os

import jasy.core.Console as Console

from jasy.core.Permutation import getPermutation
from jasy.item.Class import ClassError, ClassItem
from jasy.js.Resolver import Resolver
from jasy.js.Sorter import Sorter
from jasy.js.parse.Parser import parse
from jasy.js.output.Compressor import Compressor
from jasy import UserError

from jasy.js.output.Optimization import Optimization
from jasy.js.output.Formatting import Formatting

from jasy.core.FileManager import FileManager

compressor = Compressor()
packCache = {}


def packCode(code):
    """Packs the given code by passing it to the compression engine"""
    
    if code in packCache:
       return packCache[code]
    
    packed = compressor.compress(parse(code))
    packCache[code] = packed
    
    return packed



class OutputManager:

    def __init__(self, session, assetManager=None, compressionLevel=1, formattingLevel=0):

        self.__session = session

        self.__assetManager = assetManager
        self.__fileManager = FileManager(session)

        self.__scriptOptimization = Optimization()
        
        self.__compressGeneratedCode = False

        self.__kernelClasses = []

        if compressionLevel > 0:
            self.__scriptOptimization.enable("variables")
            self.__scriptOptimization.enable("declarations")
            
            self.__compressGeneratedCode = True

        if compressionLevel > 1:
            self.__scriptOptimization.enable("blocks")
            self.__scriptOptimization.enable("privates")

        self.__scriptFormatting = Formatting()

        if formattingLevel > 0:
            self.__scriptFormatting.enable("semicolon")
            self.__scriptFormatting.enable("comma")


    def deployAssets(self, classes, assetFolder=None):
        """
        Deploys assets for the given classes and all their dependencies

        :param classes: List of classes to deploy assets for
        :type classes: list
        :param assetFolder: Destination folder of assets (defaults to $prefix/asset)
        :type assetFolder: string
        """

        Console.info("Deploying assets...")
        Console.indent()

        resolver = Resolver(self.__session)

        for className in classes:
            resolver.addClassName(className)

        self.__assetManager.deploy(resolver.getIncludedClasses(), assetFolder=assetFolder)

        Console.outdent()


    def collectFieldData(self):
        """

        """

        Console.info("Analysing configured fields...")
        Console.indent()

        # Generate client side code for every field
        detects = self.__session.exportFieldDetects()
        codeBlocks = [ self.__session.exportField(field) for field in detects ]

        Console.outdent()

        return codeBlocks


    def buildClassList(self, classes, bootCode=None, filterBy=None, inlineTranslations=False):

        session = self.__session

        # 1. Add given set of classes
        resolver = Resolver(session)
        for classItem in classes:
            resolver.addClass(classItem)

        # 2. Add optional boot code
        if bootCode:
            bootClassItem = session.getVirtualItem("jasy.generated.BootCode", ClassItem, "(function(){%s})();" % bootCode, ".js")
            resolver.addClass(bootClassItem)

        # 3. Check for usage assets
        includedClasses = resolver.getIncludedClasses()
        usesAssets = False
        for classItem in includedClasses:
            if classItem.getId() == "jasy.Asset":
                usesAssets = True
                break

        # 4. Add asset data
        if usesAssets:
            assetData = self.__assetManager.export(includedClasses)
            assetClassItem = session.getVirtualItem("jasy.generated.AssetData", ClassItem, "jasy.Asset.addData(%s);" % assetData, ".js")
            resolver.addClass(assetClassItem, prepend=True)

        # 5. Add translation data
        if not inlineTranslations:
            translationBundle = self.__session.getCurrentTranslationBundle()
            if translationBundle:
                translationData = translationBundle.export(filtered)
                if translationData:
                    translationClassItem = session.getVirtualItem("jasy.generated.TranslationData", ClassItem, "jasy.Translate.addData(%s);" % translationData, ".js")
                    resolver.addClass(translationClassItem, prepend=True)

        # 6. Sorting classes
        sortedClasses = resolver.getSortedClasses()

        # 7. Apply filter
        if filterBy:
            filteredClasses = []
            for classObj in sortedClasses:
                if not classObj in filterBy:
                    filteredClasses.append(classObj)

            sortedClasses = filteredClasses

        return sortedClasses


    def compressClasses(self, classes, dividers=True):
        try:
            session = self.__session
            result = []

            for classObj in classes:
                compressed = classObj.getCompressed(session.getCurrentPermutation(), session.getCurrentTranslationBundle(), self.__scriptOptimization, self.__scriptFormatting)

                if dividers:
                    result.append("// FILE ID: %s\n%s\n\n" % (classObj.getId(), compressed))
                else:
                    result.append(compressed)
                
        except ClassError as error:
            raise UserError("Error during class compression! %s" % error)

        return "\n".join(result)


    def loadClasses(self, classes, dividers=True, urlPrefix=None):

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

            compressedList = self.buildClassList(compress, filterBy=self.__kernelClasses)
            code += self.compressClasses(compressedList, dividers=dividers)


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

        if not dividers:
            loaderList = '"%s"' % '","'.join(files)
        else:
            loaderList = '"%s"' % '",\n"'.join(files)

        code += 'core.io.Queue.load([%s], null, null, true);' % loaderList
        return code


    def storeKernel(self, fileName, bootCode=""):

        Console.info("Storing kernel...")
        Console.indent()

        # Export all field data for the kernel
        classes = []
        allFieldData = self.collectFieldData()
        for fieldData in allFieldData:
            classItem = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem, "jasy.Env.addField(%s);" % fieldData, ".js")
            classes.append(classItem)

        # Transfer all hard-wired fields into a permutation
        self.__session.setStaticPermutation()

        # Sort and compress
        sortedClasses = self.buildClassList(classes, bootCode)
        
        Console.info("Compressing %s classes...", len(sortedClasses))
        compressedCode = self.compressClasses(sortedClasses)

        # Write file to disk
        self.__fileManager.writeFile(fileName, compressedCode)

        # Remember kernel level classes
        self.__kernelClasses = sortedClasses

        Console.outdent()


    def storeLoader(self, classes, fileName, bootCode=""):

        Console.info("Storing loader...")
        Console.indent()

        # Build class list
        sortedClasses = self.buildClassList(classes, bootCode, filterBy=self.__kernelClasses)
            
        # Compress code
        Console.info("Including %s classes...", len(sortedClasses))
        loaderCode = self.loadClasses(sortedClasses)

        # Write file to disk
        self.__fileManager.writeFile(fileName, loaderCode)

        Console.outdent()
