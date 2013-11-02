#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import os, fnmatch, re, json

from jasy import UserError

import jasy.core.Console as Console
import jasy.core.File as File


class AssetManager():

    def __init__(self, profile, session):

        Console.info("Initializing assets...")
        Console.indent()

        self.__profile = profile
        self.__session = session
        self.__copylist = set()

        # Loop though all projects and merge assets
        assets = self.__assets = {}
        for project in self.__session.getProjects():
            assets.update(project.getAssets())

        self.__addCommands()

        Console.outdent()
        Console.info("Activated %s assets", len(assets))


    def getAssetUrl(self, fileId):
        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]

        # Add asset item to tracking list for copy process
        self.__copylist.add(assetItem)

        # Check for whether files are being copied over to somewhere
        # or whether we use the relative URL to the source folder
        if self.__profile.getCopyAssets():
            url = os.path.join(self.__profile.getAssetFolder(), self.__computeDestinationName(assetItem))
        else:
            url = os.path.relpath(assetItem.getPath(), self.__profile.getWorkingPath())

        return "url(%s)" % url


    def getAssetWidth(self, fileId):
        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]
        if assetItem.isImage():
            return assetItem.exportData()[0]


    def getAssetHeight(self, fileId):
        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]
        if assetItem.isImage():
            return assetItem.exportData()[1]


    def __addCommands(self):
        self.__session.addCommand("jasy.asset", lambda fileId: self.getAssetUrl(fileId))
        self.__session.addCommand("jasy.width", lambda fileId: self.getAssetWidth(fileId))
        self.__session.addCommand("jasy.height", lambda fileId: self.getAssetHeight(fileId))



    def __computeDestinationName(self, assetItem):
        if self.__profile.getHashAssets():
            return "%s%s" % (assetItem.getChecksum(), assetItem.extension)
        else:
            return assetItem.getId().replace("/", os.sep)


    def copyAssets(self, destination, hashNames):
        Console.info("Copying assets...")
        counter = 0

        assetFolder = self.__profile.getAssetFolder()

        for assetItem in self.__copylist:
            srcFile = assetItem.getPath()
            dstFile = os.path.join(assetFolder, self.__computeDestinationName(assetItem))

            if File.syncfile(srcFile, dstFile):
                counter += 1

        Console.info("Copied %s assets.", counter)


    def exportToJson(self, items=None):
        """
        Exports asset data for usage at the client side. Utilizes JavaScript
        class jasy.Asset to inject data into the client at runtime.
        """

        # Processing assets
        assets = self.__assets

        result = {}
        filterExpr = self.__compileFilterExpr(items) if items else None
        for fileId in assets:
            if filterExpr and not filterExpr.match(fileId):
                continue

            entry = {}

            assetItem = assets[fileId]
            self.__copylist.add(assetItem)
            entry["t"] = assetItem.getType(short=True)

            assetData = assetItem.exportData()
            if assetData:
                entry["d"] = assetData

            result[fileId] = entry

        # Ignore empty result
        if not result:
            return None

        Console.info("Exported %s assets", len(result))

        return json.dumps({
            "assets" : self.__structurize(result),
            "profile" : self.__profile.exportData()
        }, indent=2, sort_keys=True)





    def __structurize(self, data):
        """
        This method structurizes the incoming data into a cascaded structure representing the
        file system location (aka file IDs) as a tree. It further extracts the extensions and
        merges files with the same name (but different extensions) into the same entry. This is
        especially useful for alternative formats like audio files, videos and fonts. It only
        respects the data of the first entry! So it is not a good idea to have different files
        with different content stored with the same name e.g. content.css and content.png.
        """

        root = {}

        # Easier to debug and understand when sorted
        for fileId in sorted(data):
            current = root
            splits = fileId.split("/")

            # Extract the last item aka the filename itself
            basename = splits.pop()

            # Find the current node to store info on
            for split in splits:
                if not split in current:
                    current[split] = {}
                elif type(current[split]) != dict:
                    raise UserError("Invalid asset structure. Folder names must not be identical to any filename without extension: \"%s\" in %s" % (split, fileId))

                current = current[split]

            # Create entry
            Console.debug("Adding %s..." % fileId)
            current[basename] = data[fileId]

        return root


    def __compileFilterExpr(self, classes):
        """Returns the regular expression object to use for filtering"""

        # Merge asset hints from all classes and remove duplicates
        hints = set()
        for classObj in classes:
            hints.update(classObj.getMetaData(self.__session.getCurrentPermutation()).assets)

        # Compile filter expressions
        matcher = "^%s$" % "|".join(["(?:%s)" % fnmatch.translate(hint) for hint in hints])
        Console.debug("Compiled asset matcher: %s" % matcher)

        return re.compile(matcher)
