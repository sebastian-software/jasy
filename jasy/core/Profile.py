#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.core.Console as Console


class Profile():
    """
    Configuration object for the build profile of the current task
    """

    __destinationFolder = None

    __parts = None

    __styleFolder = None
    __scriptFolder = None
    __assetFolder = None
    __templateFolder = None

    __hashAssets = False

    __compressionLevel = 0
    __formattingLevel = 5




    def __init__(self, session):

        self.__session = session
        self.__parts = {}



    def getDestinationFolder(self):
        return self.__destinationFolder

    def setDestinationFolder(self, folder):
        self.__destinationFolder = folder




    def getStyleFolder(self):
        return self.__styleFolder

    def setStyleFolder(self, folder):
        self.__styleFolder = folder

    def getScriptFolder(self):
        return self.__scriptFolder

    def setScriptFolder(self, folder):
        self.__scriptFolder = folder

    def getAssetFolder(self):
        return self.__assetFolder

    def setAssetFolder(self, folder):
        self.__assetFolder = folder

    def getTemplateFolder(self):
        return self.__templateFolder

    def setTemplateFolder(self, folder):
        self.__templateFolder = folder




    def getHashAssets(self):
        return self.__hashAssets

    def setHashAssets(self, enable):
        self.__hashAssets = enable

    def getLoadScriptSource(self):
        return self.__loadScriptSource

    def setLoadScriptSource(self, enable):
        self.__loadScriptSource = enable




    def getCompressionLevel(self):
        return self.__compressionLevel

    def setCompressionLevel(self, level):
        self.__compressionLevel = level

    def getFormattingLevel(self):
        return self.__formattingLevel

    def setFormattingLevel(self, level):
        self.__formattingLevel = level




    def registerPart(self, name, className="", styleName="", templateName=""):
        if name in self.__parts:
            raise Exception("The part %s is already registered!")

        self.__parts[name] = {
            "class" : className,
            "style" : styleName,
            "template" : templateName
        }



    def build(self):

        parts = self.__parts

        if "kernel" in parts:

            Console.info("Building part kernel...")
            Console.indent()



            Console.outdent()


        for permutation in self.__session.permutate():

            if "main" in parts:

                Console.info("Building part main...")
                Console.indent()

                Console.outdent()

            for part in parts:

                if part in ("kernel", "main"):
                    continue

                Console.info("Building part %s", part)












