#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import os, fnmatch, re, json

from jasy import UserError

import jasy.core.Console as Console
import jasy.core.File as File
import jasy.core.Util as Util

RE_URL_PARAMS = re.compile("^([^?#]*)(.*)$")


class AssetManager():

    def __init__(self, profile):
        # The current build profile
        self.__profile = profile

        # All known assets
        self.__assets = {}

        # The set of assets to copy during deployment
        self.__copylist = set()


    def addProject(self, project):
        self.__assets.update(project.getAssets())


    def getAssetUrl(self, fileId):
        """
        Returns the asset URL for the given item relative to the current working path
        """

        matched = False
        if not fileId in self.__assets:
            # Try to split asset params before resolving
            matched = re.match(RE_URL_PARAMS, fileId)
            if matched:
                fileId = matched.group(1)
                postFix = matched.group(2)

            if not fileId in self.__assets:
                raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]

        # Add asset item to tracking list for copy process
        self.__copylist.add(assetItem)

        # Check for whether files are being copied over to somewhere
        # or whether we use the relative URL to the source folder
        if self.__profile.getUseSource():
            url = assetItem.getPath()
        else:
            url = self.__computeDestinationPath(assetItem)

        # Make URL relative to current working path
        url = os.path.relpath(url, self.__profile.getWorkingPath())

        # Post append asset param/query
        if matched:
            url += postFix

        return url


    def getAssetWidth(self, fileId):
        """
        Returns the width (image width) of the given item
        """

        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]
        if assetItem.isImage():
            return assetItem.exportData()[0]


    def getAssetHeight(self, fileId):
        """
        Returns the width (image height) of the given item
        """

        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]
        if assetItem.isImage():
            return assetItem.exportData()[1]


    def getSpriteId(self, fileId):
        """
        Returns the sprite asset which contains the image with the given ID
        """

        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]
        if assetItem.isImage():
            assetData = assetItem.exportData()
            if len(assetData) < 2:
                raise Exception("No such sprite image: %s" % fileId)

            spriteData = assetData[2]
            spriteIndex = spriteData[0]
            return self.__sprites[spriteIndex]


    def getSpriteUrl(self, fileId):
        """
        Returns the url of the sprite sheet which contains the given single image
        """

        return self.getAssetUrl(self.getSpriteId(fileId))


    def getSpriteWidth(self, fileId):
        """
        Returns the width of the sprite sheet which contains the given single image
        """

        return self.getAssetWidth(self.getSpriteId(fileId))


    def getSpriteHeight(self, fileId):
        """
        Returns the height of the sprite sheet which contains the given single image
        """

        return self.getAssetHeight(self.getSpriteId(fileId))


    def getSpriteLeft(self, fileId):
        """
        Returns the left position of the image on the sprite sheet
        """

        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]
        if assetItem.isImage():
            assetData = assetItem.exportData()
            if len(assetData) < 2:
                raise Exception("No such sprite image: %s" % fileId)

            spriteData = assetData[2]
            return spriteData[1]


    def getSpriteTop(self, fileId):
        """
        Returns the top position of the image on the sprite sheet
        """

        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]
        if assetItem.isImage():
            assetData = assetItem.exportData()
            if len(assetData) < 2:
                raise Exception("No such sprite image: %s" % fileId)

            spriteData = assetData[2]
            return spriteData[2]


    def getAnimationColumns(self, fileId):
        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]
        if assetItem.isImage():
            assetData = assetItem.exportData()
            if len(assetData) < 3:
                raise Exception("No such animated image: %s" % fileId)

            animationData = assetData[3]
            return animationData[0]


    def getAnimationRows(self, fileId):
        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]
        if assetItem.isImage():
            assetData = assetItem.exportData()
            if len(assetData) < 3:
                raise Exception("No such animated image: %s" % fileId)

            animationData = assetData[3]
            return animationData[1]


    def getAnimationFrames(self, fileId):
        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        assetItem = self.__assets[fileId]
        if assetItem.isImage():
            assetData = assetItem.exportData()
            if len(assetData) < 3:
                raise Exception("No such animated image: %s" % fileId)

            animationData = assetData[3]
            try:
                return animationData[2]
            except IndexError:
                return animationData[0] * animationData[1]



    def processSprites(self):
        """
        Processes jasysprite files to merge sprite data into asset registry
        """

        assets = self.__assets
        configs = [fileId for fileId in assets if assets[fileId].isImageSpriteConfig()]

        if configs:
            Console.info("Processing %s...", Console.colorize("%s sprites", "magenta") % len(configs))

        sprites = []
        Console.indent()
        for fileId in configs:
            Console.debug("Processing %s...", fileId)

            asset = assets[fileId]
            spriteBase = os.path.dirname(fileId)

            try:
                spriteConfig = asset.getParsedObject();
            except ValueError as err:
                raise UserError("Could not parse jasysprite at %s: %s" % (fileId, err))

            Console.indent()
            for spriteImage in spriteConfig:
                spriteImageId = "%s/%s" % (spriteBase, spriteImage)

                singleRelPaths = spriteConfig[spriteImage]
                Console.debug("Image %s combines %s images", spriteImageId, len(singleRelPaths))

                for singleRelPath in singleRelPaths:
                    singleId = "%s/%s" % (spriteBase, singleRelPath)
                    singleData = singleRelPaths[singleRelPath]
                    singleItem = assets[singleId]

                    # Verify that sprite sheet is up-to-date
                    fileChecksum = singleItem.getChecksum()
                    storedChecksum = singleData["checksum"]

                    Console.debug("Checksum Compare: %s <=> %s", fileChecksum, storedChecksum)
                    if storedChecksum != fileChecksum:
                        raise UserError("Sprite Sheet is not up-to-date. Checksum of %s differs." % singleId)

                    if not spriteImageId in sprites:
                        spriteImageIndex = len(sprites)
                        sprites.append(spriteImageId)
                    else:
                        spriteImageIndex = sprites.index(spriteImageId)

                    # Add relevant data to find image on sprite sheet
                    singleItem.addImageSpriteData(spriteImageIndex, singleData["left"], singleData["top"])

            Console.outdent()

            # The config file does not make any sense on the client side
            Console.debug("Deleting sprite config from assets: %s", fileId)
            del assets[fileId]

        Console.outdent()
        self.__sprites = sprites


    def processAnimations(self):
        """Processes jasyanimation files to merge animation data into asset registry"""

        assets = self.__assets
        configs = [fileId for fileId in assets if assets[fileId].isImageAnimationConfig()]

        if configs:
            Console.info("Processing %s...", Console.colorize("%s animations", "magenta") % len(configs))

        Console.indent()
        for fileId in configs:
            Console.debug("Processing %s...", fileId)

            asset = assets[fileId]
            base = os.path.dirname(fileId)

            try:
                config = asset.getParsedObject()
            except ValueError as err:
                raise UserError("Could not parse jasyanimation at %s: %s" % (fileId, err))

            for relPath in config:
                imageId = "%s/%s" % (base, relPath)
                data = config[relPath]

                if not imageId in assets:
                    raise UserError("Unknown asset %s in %s" % (imageId, fileId))

                animationAsset = assets[imageId]

                if "rows" in data or "columns" in data:
                    rows = Util.getKey(data, "rows", 1)
                    columns = Util.getKey(data, "columns", 1)
                    frames = Util.getKey(data, "frames")

                    animationAsset.addImageAnimationData(columns, rows, frames)

                    if frames is None:
                        frames = rows * columns

                elif "layout" in data:
                    layout = data["layout"]
                    animationAsset.addImageAnimationData(None, None, layout=layout)
                    frames = len(layout)

                else:
                    raise UserError("Invalid image frame data for: %s" % imageId)

                Console.debug("  - Animation %s has %s frames", imageId, frames)

            Console.debug("  - Deleting animation config from assets: %s", fileId)
            del assets[fileId]

        Console.outdent()


    def __computeDestinationPath(self, assetItem):
        """
        Returns the path of the given asset item including the asset folder path
        """

        profile = self.__profile
        assetFolder = os.path.join(profile.getDestinationPath(), profile.getAssetFolder())

        if profile.getHashAssets():
            fileName = "%s%s" % (assetItem.getChecksum(), assetItem.extension)
        else:
            fileName = assetItem.getId().replace("/", os.sep)

        return assetFolder + "/" + fileName


    def copyAssets(self):
        """
        Copies assets from their source folder to the configured
        destination folder. Does apply file name transformations
        during copying when requested.
        """

        Console.info("Copying assets...")

        counter = 0
        for assetItem in self.__copylist:
            srcFile = assetItem.getPath()
            dstFile = self.__computeDestinationPath(assetItem)

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

        # Destination folder for assets
        assetPath = os.path.join(self.__profile.getDestinationPath(), self.__profile.getAssetFolder());

        result = {}
        filterExpr = self.__compileFilterExpr(items) if items else None
        for fileId in assets:
            if filterExpr and not filterExpr.match(fileId):
                continue

            entry = {}
            # t = file type
            # u = full file url
            # h = file hash (based on content)
            # d = asset data (image size, etc.)

            assetItem = assets[fileId]
            self.__copylist.add(assetItem)

            if self.__profile.getUseSource():
                # Compute relative folder from asset location to even external
                # locations (e.g. auto cloned remote projects)
                entry["u"] = os.path.relpath(assetItem.getPath(), assetPath)
            elif self.__profile.getHashAssets():
                # Export checksum (SHA1 encoded as URL-safe Base62)
                entry["h"] = assetItem.getChecksum()

            # Store file type as analyzed by asset item
            entry["t"] = assetItem.getType(short=True)

            # Store additional data figured out by asset item e.g.
            # image dimensions, video format, play duration, ...
            assetData = assetItem.exportData()
            if assetData:
                entry["d"] = assetData

            result[fileId] = entry

        # Ignore empty result
        if not result:
            return None

        Console.info("Exported %s assets", len(result))

        return json.dumps({
            "assets" : self.__structurize(result)
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
            hints.update(classObj.getMetaData(self.__profile.getCurrentPermutation()).assets)

        # Compile filter expressions
        matcher = "^%s$" % "|".join(["(?:%s)" % fnmatch.translate(hint) for hint in hints])
        Console.debug("Compiled asset matcher: %s" % matcher)

        return re.compile(matcher)






