#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import jasy.core.Console as Console

import jasy.build.Asset as AssetBuilder
import jasy.build.Script as ScriptBuilder
import jasy.build.Style as StyleBuilder

KERNEL_NAME = "kernel"

def run(profile):
    session = profile.getSession()
    parts = profile.getParts()

    assetBuilder = AssetBuilder.AssetBuilder(profile)
    scriptBuilder = ScriptBuilder.ScriptBuilder(profile)
    styleBuilder = StyleBuilder.StyleBuilder(profile)

    if KERNEL_NAME in parts:
        scriptBuilder.buildKernel(parts["kernel"]["class"])
        styleBuilder.buildKernel(parts["kernel"]["style"])

    for permutation in profile.permutate():
        for part in parts:
            if part != KERNEL_NAME:
                scriptBuilder.buildPart(part, parts[part]["class"])
                styleBuilder.buildPart(part, parts[part]["style"])

    if profile.getCopyAssets():
        profile.getAssetManager().copyAssets()
