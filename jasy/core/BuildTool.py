#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import os.path

import jasy.core.Console as Console
import jasy.core.OutputManager as OutputManager
import jasy.js.Resolver as ScriptResolver
import jasy.style.Resolver as StyleResolver

def run(profile):
    session = profile.getSession()
    parts = profile.getParts()

    outputManager = OutputManager.OutputManager(profile)

    destinationFolder = profile.getDestinationPath()

    jsOutputPath = os.path.join(destinationFolder, profile.getJsFolder())
    cssOutputPath = os.path.join(destinationFolder, profile.getCssFolder())
    assetOutputPath = os.path.join(destinationFolder, profile.getAssetFolder())
    templateOutputPath = os.path.join(destinationFolder, profile.getTemplateFolder())

    if "kernel" in parts:

        profile.setWorkingPath(profile.getDestinationPath())

        Console.info("Building part kernel...")
        Console.indent()

        # Store kernel script
        kernelClass = parts["kernel"]["class"]
        outputManager.storeKernelScript("%s/kernel.js" % jsOutputPath, bootCode="%s.boot();" % kernelClass)

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
                    outputManager.storeLoaderScript(classItems, "%s/%s-{{id}}.js" % (jsOutputPath, part), "new %s;" % partClass)
                else:
                    outputManager.storeCompressedScript(classItems, "%s/%s-{{id}}.js" % (jsOutputPath, part), "new %s;" % partClass)

                Console.outdent()


            # CSS

            partStyle = parts[part]["style"]
            if partStyle:
                profile.setWorkingPath(cssOutputPath)

                Console.info("Generating style (%s)...", partStyle)
                Console.indent()

                styleItems = StyleResolver.Resolver(profile).add(partStyle).getSorted()
                outputManager.storeCompressedStylesheet(styleItems, "%s/%s-{{id}}.css" % (cssOutputPath, part))

                Console.outdent()



            Console.outdent()


    if profile.getCopyAssets():
        profile.getAssetManager().copyAssets()

