#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import os

import jasy.core.Console as Console

from jasy.item.Style import StyleError
from jasy.item.Style import StyleItem

import jasy.style.Resolver as StyleResolver

import jasy.style.output.Optimization as StyleOptimization
import jasy.style.output.Formatting as StyleFormatting

class StyleBuilder:

    # --------------------------------------------------------------------------------------------
    #   ESSENTIALS
    # --------------------------------------------------------------------------------------------

    def __init__(self, profile):

        self.__profile = profile
        self.__session = profile.getSession()
        self.__fileManager = profile.getFileManager()
        self.__outputPath = os.path.join(profile.getDestinationPath(), profile.getCssOutputFolder())


    def __compressStyles(self, styles):
        try:
            profile = self.__profile
            result = []

            for styleObj in styles:
                compressed = styleObj.getCompressed(profile)

                if profile.getFormattingLevel() > 0:
                    result.append("/* FILE ID: %s */\n%s\n\n" % (styleObj.getId(), compressed))
                else:
                    result.append(compressed)

        except StyleError as error:
            raise UserError("Error during stylesheet compression! %s" % error)

        return "".join(result)



    # --------------------------------------------------------------------------------------------
    #   PUBLIC API
    # --------------------------------------------------------------------------------------------

    def getWorkingPath(self):
        # Locations inside stylesheets are always relative to the stylesheet folder
        # Note: We think of output stylesheets being stored without sub folder here
        return self.__outputPath


    def buildKernel(self, fileId):
        if not fileId:
            return

        if fileId:
            raise Exception("Non permuated styles are not supported yet!")


    def buildPart(self, partId, fileId):
        if not fileId:
            return

        Console.info("Generating style (%s)...", fileId)
        Console.indent()

        self.__profile.setWorkingPath(self.getWorkingPath())
        styleItems = StyleResolver.Resolver(self.__profile).add(fileId).getSorted()
        self.storeCompressedStylesheet(styleItems, "%s-{{id}}.css" % partId)

        Console.outdent()


    def storeCompressedStylesheet(self, styles, fileName):

        Console.info("Generating compressed stylesheet...")
        Console.indent()

        # Resolve placeholders first
        fileName = self.__profile.expandFileName(fileName)
        relativeToMain = self.__session.getMain().toRelativeUrl(fileName)

        compressedCode = self.__compressStyles(styles)
        self.__fileManager.writeFile(os.path.join(self.__outputPath, fileName), compressedCode)

        Console.outdent()
