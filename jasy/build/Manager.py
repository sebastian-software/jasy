#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import os.path

import jasy.core.Console as Console

import jasy.js.Resolver as ScriptResolver
import jasy.style.Resolver as StyleResolver

import jasy.build.Asset as AssetBuilder
import jasy.build.Script as ScriptBuilder
import jasy.build.Style as StyleBuilder


def run(profile):
    session = profile.getSession()
    parts = profile.getParts()

    assetBuilder = AssetBuilder.AssetBuilder(profile)
    scriptBuilder = ScriptBuilder.ScriptBuilder(profile)
    styleBuilder = StyleBuilder.StyleBuilder(profile)

    destinationFolder = profile.getDestinationPath()

    jsOutputPath = os.path.join(destinationFolder, profile.getJsOutputFolder())
    cssOutputPath = os.path.join(destinationFolder, profile.getCssOutputFolder())
    assetOutputPath = os.path.join(destinationFolder, profile.getAssetOutputFolder())
    templateOutputPath = os.path.join(destinationFolder, profile.getTemplateOutputFolder())

    if "kernel" in parts:

        profile.setWorkingPath(profile.getDestinationPath())

        Console.info("Building part kernel...")
        Console.indent()

        # Store kernel script
        kernelClass = parts["kernel"]["class"]
        scriptBuilder.storeKernelScript("%s/kernel.js" % jsOutputPath, bootCode="%s.boot();" % kernelClass)

        Console.outdent()


    for permutation in profile.permutate():

        for part in parts:

            if part == "kernel":
                continue

            Console.info("Building part %s..." % part)
            Console.indent()


            # SCRIPT

            partClass = parts[part]["class"]
            if partClass:
                profile.setWorkingPath(profile.getDestinationPath())

                Console.info("Generating script (%s)...", partClass)
                Console.indent()

                classItems = ScriptResolver.Resolver(profile).add(partClass).getSorted()

                if profile.getUseSource():
                    scriptBuilder.storeLoaderScript(classItems, "%s/%s-{{id}}.js" % (jsOutputPath, part), "new %s;" % partClass)
                else:
                    scriptBuilder.storeCompressedScript(classItems, "%s/%s-{{id}}.js" % (jsOutputPath, part), "new %s;" % partClass)

                Console.outdent()


            # CSS

            partStyle = parts[part]["style"]
            if partStyle:
                profile.setWorkingPath(cssOutputPath)

                Console.info("Generating style (%s)...", partStyle)
                Console.indent()

                styleItems = StyleResolver.Resolver(profile).add(partStyle).getSorted()
                styleBuilder.storeCompressedStylesheet(styleItems, "%s/%s-{{id}}.css" % (cssOutputPath, part))

                Console.outdent()



            Console.outdent()


    if profile.getCopyAssets():
        profile.getAssetManager().copyAssets()

