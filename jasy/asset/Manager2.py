#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import os, fnmatch

from jasy import UserError
import jasy.core.Console as Console


class AssetManager():

    def __init__(self, profile, session):

        Console.info("Initializing assets...")
        Console.indent()

        self.__profile = profile
        self.__session = session

        # Loop though all projects and merge assets
        assets = self.__assets = {}
        for project in self.__session.getProjects():
            assets.update(project.getAssets())

        self.__addCommands()

        Console.outdent()
        Console.info("Activated %s assets", len(assets))


    def __addCommands(self):
        session = self.__session
        profile = self.__profile

        data = self.__data
        assets = self.__assets

        main = session.getMain()

        def assetCmd(fileId):
            if not fileId in assets:
                raise Exception("Did not found asset with ID %s" % fileId)

            asset = assets[fileId]
            return "url(%s)" % os.path.relpath(asset.getPath(), resultPath)


        def widthCmd(fileId):
            if not fileId in assets:
                raise Exception("Did not found asset with ID %s" % fileId)

            asset = assets[fileId]
            if asset.isImage():
                return asset.exportData()[0]


        def heightCmd(fileId):
            if not fileId in assets:
                raise Exception("Did not found asset with ID %s" % fileId)

            asset = assets[fileId]
            if asset.isImage():
                return asset.exportData()[1]


        session.addCommand("jasy.asset", assetCmd)
        session.addCommand("jasy.width", widthCmd)
        session.addCommand("jasy.height", heightCmd)


