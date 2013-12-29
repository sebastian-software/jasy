#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy

import time, socket, uuid, getpass

import jasy.core.Console as Console
import jasy.core.FileManager as FileManager
import jasy.core.Util as Util

import jasy.asset.Manager as AssetManager
import jasy.item.Class as ClassItem



class Profile():
    """
    Configuration object for the build profile of the current task
    """

    # Relative or path of the destination folder
    __destinationPath = None

    # The same as destination folder but from the URL/server perspective
    __destinationUrl = None

    # The user configured application parts
    __parts = None

    # Name of the folder inside the destination folder for storing compiled templates
    __templateFolder = "tmpl"

    # Name of the folder inside the destination folder for storing generated script files
    __jsFolder = "js"

    # Name of the folder inside the destination folder for storing generated style sheets
    __cssFolder = "css"

    # Name of the folder inside the destination folder for storing used assets
    __assetFolder = "asset"

    # Currently selected output path
    __workingPath = None

    # Whether the content hash of assets should be used instead of their name
    __hashAssets = False

    # Whether assets should be copied to the destination folder
    __copyAssets = False

    # Whether files should be loaded from the different source folders
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

        # Initialize objects
        self.__assetManager = AssetManager.AssetManager(self, session)
        self.__fileManager = FileManager.FileManager(session)


    def getSession(self):
        return self.__session

    def getParts(self):
        return self.__parts

    def getOutputManager(self):
        return self.__outputManager

    def getAssetManager(self):
        return self.__assetManager

    def getFileManager(self):
        return self.__fileManager


    def getDestinationPath(self):
        return self.__destinationPath or self.__session.getCurrentPrefix()

    def setDestinationPath(self, path):
        self.__destinationPath = path

    def getDestinationUrl(self):
        return self.__destinationUrl

    def setDestinationUrl(self, url):
        # Fix missing end slash
        if not url.endswith("/"):
            url += "/"

        self.__destinationUrl = url



    #
    # OUTPUT FOLDER NAMES
    #

    def getCssFolder(self):
        return self.__cssFolder

    def setCssFolder(self, folder):
        self.__cssFolder = folder

    def getJsFolder(self):
        return self.__jsFolder

    def setJsFolder(self, folder):
        self.__jsFolder = folder

    def getAssetFolder(self):
        return self.__assetFolder

    def setAssetFolder(self, folder):
        self.__assetFolder = folder

    def getTemplateFolder(self):
        return self.__templateFolder

    def setTemplateFolder(self, folder):
        self.__templateFolder = folder



    #
    # CONFIGURATION OPTIONS
    #

    def getWorkingPath(self):
        return self.__workingPath

    def setWorkingPath(self, path):
        self.__workingPath = path

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



    #
    # OUTPUT FORMATTING/COMPRESSION SETTINGS
    #

    def getCompressionLevel(self):
        return self.__compressionLevel

    def setCompressionLevel(self, level):
        self.__compressionLevel = level

    def getFormattingLevel(self):
        return self.__formattingLevel

    def setFormattingLevel(self, level):
        self.__formattingLevel = level



    #
    # PART MANAGEMENT
    #

    def registerPart(self, name, className="", styleName="", templateName=""):
        if name in self.__parts:
            raise Exception("The part %s is already registered!")

        self.__parts[name] = {
            "class" : className,
            "style" : styleName,
            "template" : templateName
        }



    #
    # EXPORT DATA FOR CLIENT SIDE
    #

    def exportData(self):
        return {
            "root" : self.getDestinationUrl() or self.getDestinationFolder()
        }



    #
    # MAIN BUILD METHOD
    #

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

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.url",4,"%s"' % (self.getDestinationUrl() or ""))
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






