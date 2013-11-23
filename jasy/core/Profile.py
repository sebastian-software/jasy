#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy

import os.path
import time, socket, uuid, getpass

import jasy.core.Console as Console
import jasy.core.OutputManager as OutputManager
import jasy.core.FileManager as FileManager
import jasy.core.Util as Util

import jasy.asset.Manager2 as AssetManager

import jasy.item.Class as ClassItem

import jasy.js.Resolver as ScriptResolver
import jasy.style.Resolver as StyleResolver



class Profile():
    """
    Configuration object for the build profile of the current task
    """

    __destinationFolder = None
    __destinationUrl = None

    __parts = None

    __templateFolder = "tmpl"
    __jsFolder = "js"
    __cssFolder = "css"
    __assetFolder = "asset"

    # Currently selected output path
    __workingPath = None

    __hashAssets = False
    __copyAssets = False
    __useSource = False

    __compressionLevel = 0
    __formattingLevel = 5


    __timeStamp = None
    __timeHash = None


    def __init__(self, session):

        self.__session = session
        self.__parts = {}

        # Behaves like Date.now() in JavaScript: UTC date in milliseconds
        self.__timeStamp = int(round(time.time() * 1000))
        self.__timeHash = Util.generateChecksum(str(self.__timeStamp))



    def getDestinationFolder(self):
        return self.__destinationFolder

    def setDestinationFolder(self, folder):
        self.__destinationFolder = folder

    def getDestinationUrl(self):
        return self.__destinationUrl

    def setDestinationUrl(self, url):
        self.__destinationUrl = url



    def getCssFolder(self):
        return "%s/%s" % (self.__destinationFolder, self.__cssFolder)

    def setCssFolder(self, folder):
        self.__cssFolder = folder

    def getJsFolder(self):
        return "%s/%s" % (self.__destinationFolder, self.__jsFolder)

    def setJsFolder(self, folder):
        self.__jsFolder = folder

    def getAssetFolder(self):
        return "%s/%s" % (self.__destinationFolder, self.__assetFolder)

    def setAssetFolder(self, folder):
        self.__assetFolder = folder

    def getTemplateFolder(self):
        return "%s/%s" % (self.__destinationFolder, self.__templateFolder)

    def setTemplateFolder(self, folder):
        self.__templateFolder = folder



    def getWorkingPath(self):
        return self.__workingPath

    def getHashAssets(self):
        return self.__hashAssets

    def setHashAssets(self, enable):
        self.__hashAssets = enable

    def getCopyAssets(self):
        return self.__copyAssets

    def setCopyAssets(self, enable):
        self.__copyAssets = enable

    def getUseSource(self):
        return self.__useSource

    def setUseSource(self, enable):
        self.__useSource = enable




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



    def exportData(self):
        return {
            "root" : self.getDestinationUrl() or self.getDestinationFolder()
        }


    def build(self):

        parts = self.__parts

        # Initialize shared objects
        assetManager = AssetManager.AssetManager(self, self.__session)
        outputManager = OutputManager.OutputManager(self, self.__session, assetManager,
            compressionLevel=self.__compressionLevel, formattingLevel=self.__formattingLevel)
        fileManager = FileManager.FileManager(self.__session)


        scriptFolder = self.getScriptFolder()
        styleFolder = self.getStyleFolder()
        assetFolder = self.getAssetFolder()
        templateFolder = self.getTemplateFolder()

        if "kernel" in parts:

            self.__workingPath = self.__destinationFolder

            Console.info("Building part kernel...")
            Console.indent()

            # Store kernel script
            kernelClass = parts["kernel"]["class"]
            outputManager.storeKernelScript("%s/kernel.js" % scriptFolder, bootCode="%s.boot();" % kernelClass)

            Console.outdent()


        for permutation in self.__session.permutate():

            for part in parts:

                if part == "kernel":
                    continue


                Console.info("Building part %s..." % part)
                Console.indent()


                # SCRIPT

                self.__workingPath = self.__destinationFolder

                partClass = parts[part]["class"]
                Console.info("Generating script (%s)...", partClass)
                Console.indent()

                classItems = ScriptResolver.Resolver(self.__session).add(partClass).getSorted()

                if self.__useSource:
                    outputManager.storeLoaderScript(classItems, "%s/%s-{{id}}.js" % (scriptFolder, part), "new %s;" % partClass)
                else:
                    outputManager.storeCompressedScript(classItems, "%s/%s-{{id}}.js" % (scriptFolder, part), "new %s;" % partClass)

                Console.outdent()


                # STYLE

                self.__workingPath = styleFolder

                partStyle = parts[part]["style"]
                Console.info("Generating style (%s)...", partStyle)
                Console.indent()

                styleItems = StyleResolver.Resolver(self.__session).add(partStyle).getSorted()
                outputManager.storeCompressedStylesheet(styleItems, "%s/%s-{{id}}.css" % (styleFolder, part))

                Console.outdent()
                Console.outdent()


        if self.__copyAssets:
            assetManager.copyAssets()




    def __getEnvironmentId(self):
        """
        Returns a build ID based on environment variables and state
        """

        hostName = socket.gethostname()
        hostId = uuid.getnode()
        userName = getpass.getuser()

        return "host:%s|id:%s|user:%s" % (hostName, hostId, userName)


    def getSetupClasses(self):
        """
        Returns a list of (virtual) classes which are relevant for initial setup.
        """

        setups = {}

        # Add user configured fields from session
        setups.update(self.__session.getFieldSetupClasses())



        # Info about actual build

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.build.env",4,"%s"' % self.__getEnvironmentId())
        setups["jasy.build.env"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.build.rev",4,"%s"' % self.__session.getMain().getRevision())
        setups["jasy.build.rev"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.build.time",4,%s' % self.__timeStamp)
        setups["jasy.build.time"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        # Version of Jasy which was used for build

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.version",4,"%s"' % jasy.__version__)
        setups["jasy.version"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        # Destination URL e.g. CDN

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.url",4,"%s"' % (self.__destinationUrl or ""))
        setups["jasy.url"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        # Folder names inside destination

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.folder.template",4,"%s"' % (self.__templateFolder or ""))
        setups["jasy.folder.template"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.folder.js",4,"%s"' % (self.__jsFolder or ""))
        setups["jasy.folder.js"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.folder.css",4,"%s"' % (self.__cssFolder or ""))
        setups["jasy.folder.css"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.folder.asset",4,"%s"' % (self.__assetFolder or ""))
        setups["jasy.folder.asset"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        return setups






