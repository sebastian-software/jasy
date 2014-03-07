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

    if "kernel" in parts:

        profile.setWorkingPath(scriptBuilder.getWorkingPath())

        Console.info("Building part kernel...")
        Console.indent()

        # Store kernel script
        kernelClass = parts["kernel"]["class"]
        scriptBuilder.storeKernelScript("kernel.js", bootCode="%s.boot();" % kernelClass)

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
                Console.info("Generating script (%s)...", partClass)
                Console.indent()

                profile.setWorkingPath(scriptBuilder.getWorkingPath())
                classItems = ScriptResolver.Resolver(profile).add(partClass).getSorted()

                if profile.getUseSource():
                    scriptBuilder.storeLoaderScript(classItems, "%s-{{id}}.js" % part, "new %s;" % partClass)
                else:
                    scriptBuilder.storeCompressedScript(classItems, "%s-{{id}}.js" % part, "new %s;" % partClass)

                Console.outdent()


            # CSS

            partStyle = parts[part]["style"]
            if partStyle:
                Console.info("Generating style (%s)...", partStyle)
                Console.indent()

                profile.setWorkingPath(styleBuilder.getWorkingPath())
                styleItems = StyleResolver.Resolver(profile).add(partStyle).getSorted()
                styleBuilder.storeCompressedStylesheet(styleItems, "%s-{{id}}.css" % part)

                Console.outdent()



            Console.outdent()


    if profile.getCopyAssets():
        profile.getAssetManager().copyAssets()

