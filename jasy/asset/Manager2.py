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



    def getAssetUrl(self, fileId):
        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        asset = self.__assets[fileId]
        return "url(%s)" % os.path.relpath(asset.getPath(), self.__profile.getWorkingPath())


    def getAssetWidth(self, fileId):
        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        asset = self.__assets[fileId]
        if asset.isImage():
            return asset.exportData()[0]


    def getAssetHeight(self, fileId):
        if not fileId in self.__assets:
            raise Exception("Did not found asset with ID %s" % fileId)

        asset = self.__assets[fileId]
        if asset.isImage():
            return asset.exportData()[1]


    def __addCommands(self):
        session = self.__session
        profile = self.__profile

        session.addCommand("jasy.asset", lambda fileId: self.getAssetUrl(fileId))
        session.addCommand("jasy.width", lambda fileId: self.getAssetWidth(fileId))
        session.addCommand("jasy.height", lambda fileId: self.getAssetHeight(fileId))


