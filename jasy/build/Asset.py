#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import os

import jasy.core.Console as Console

class AssetBuilder:

    # --------------------------------------------------------------------------------------------
    #   ESSENTIALS
    # --------------------------------------------------------------------------------------------

    def __init__(self, profile):

        self.__profile = profile
        self.__assetManager = profile.getAssetManager()

        assetOutputPath = os.path.join(profile.getDestinationPath(), profile.getAssetOutputFolder())



    # --------------------------------------------------------------------------------------------
    #   PUBLIC API
    # --------------------------------------------------------------------------------------------

    def deployAssets(self, items, assetFolder=None, hashNames=False):
        """
        Deploys assets for the given items and all their dependencies

        :param items: List of items to deploy assets for
        :type items: list
        :param assetFolder: Destination folder of assets (defaults to {{prefix}}/asset)
        :type assetFolder: string
        """

        Console.info("Deploying assets...")
        Console.indent()

        resolver = Resolver(self.__profile)

        for itemId in items:
            resolver.add(itemId)

        self.__assetManager.deploy(resolver.getIncluded(), assetFolder=assetFolder, hashNames=hashNames)

        Console.outdent()
