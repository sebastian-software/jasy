#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import jasy.core.Console as Console
from distutils.version import StrictVersion, LooseVersion

try:
    import pip
except ImportError:
    Console.error("pip is required to run JASY!")
    sys.exit(1)


needs = [
    {
        "packageName": "Pygments",
        "minVersion": "1.6",
        "installPath": "'pip3 install Pygments'",
        "updatePath": "'pip3 install --upgrade pygments'"
    },
    {
        "packageName": "polib",
        "minVersion": "1.0.3",
        "installPath": "'pip3 install polib'",
        "updatePath": "'pip3 install --upgrade polib'"
    },
    {
        "packageName": "requests",
        "minVersion": "2.0",
        "installPath": "'pip3 install requests'",
        "updatePath": "'pip3 install --upgrade requests'"
    },
    {
        "packageName": "CherryPy",
        "minVersion": "3.2.4",
        "installPath": "'pip install CherryPy'",
        "updatePath": "'pip3 install --upgrade CherryPy'"
    },
    {
        "packageName": "PyYAML",
        "minVersion": "3.10",
        "installPath": "'pip install PyYAML'",
        "updatePath": "'pip3 install --upgrade PyYAML'"
    }
]

optionals = [
    {
        "packageName": "misaka",
        "minVersion": "1.0",
        "installPath": "'pip3 install misaka'",
        "updatePath": ""
    },
    {
        "packageName": "sphinx",
        "minVersion": "1.1",
        "installPath": "'pip3 install sphinx'",
        "updatePath": ""
    },
    {
        "packageName": "pillow",
        "minVersion": "2.2.0",
        "installPath": "'pip3 install Pillow'",
        "updatePath": ""
    }
]


def doCompleteDoctor():
    """Checks for uninstalled or too old versions of requirements and gives a complete output"""

    Console.header("Doctor")

    dists = [dist for dist in pip.get_installed_distributions()]
    keys = [dist.key for dist in pip.get_installed_distributions()]

    versions = {}
    for dist in dists:
        versions[dist.key] = dist.version

    def checkSingleInstallation(keys, versions, packageName, minVersion, installPath, updatePath):
        Console.info('%s:' % packageName)
        Console.indent()
        if packageName.lower() in keys:
            Console.info(Console.colorize('Found installation', "green"))
            if LooseVersion(minVersion) > LooseVersion("0.0"):
                if LooseVersion(versions[packageName.lower()]) >= LooseVersion(minVersion):
                    Console.info(Console.colorize('Version is OK (needed: %s installed: %s)' % (minVersion, versions[packageName.lower()]), "green"))
                else:
                    Console.info(Console.colorize(Console.colorize('- Version is NOT OK (needed: %s installed: %s)' % (minVersion, versions[packageName.lower()]) , "red"), "bold"))
                    Console.info('Update to the newest version of %s using %s' % (packageName, updatePath))
        else:
            Console.info(Console.colorize(Console.colorize('Did NOT find installation', "red"), "bold"))
            Console.info('Install the newest version of %s using %s' % (packageName, installPath))
        Console.outdent()


    # Required packages
    Console.info("Required Packages:")
    Console.indent()
    for entry in needs:
        checkSingleInstallation(keys, versions, entry["packageName"], entry["minVersion"], entry["installPath"], entry["updatePath"])
    Console.outdent()

    # Optional packages
    Console.info("")
    Console.info("Optional Packages:")
    Console.indent()
    for entry in optionals:
        checkSingleInstallation(keys, versions, entry["packageName"], entry["minVersion"], entry["installPath"], entry["updatePath"])
    Console.outdent()


def doInitializationDoctor():
    """Checks for uninstalled or too old versions only of needed requirements and gives error output"""

    dists = [dist for dist in pip.get_installed_distributions()]
    keys = [dist.key for dist in pip.get_installed_distributions()]

    versions = {}
    for dist in dists:
        versions[dist.key] = dist.version

    def checkSingleInstallation(keys, versions, packageName, minVersion, installPath, updatePath):
        if packageName.lower() in keys:
            if LooseVersion(minVersion) > LooseVersion("0.0"):
                if LooseVersion(versions[packageName.lower()]) < LooseVersion(minVersion):
                    Console.info(Console.colorize(Console.colorize('Jasy requirement error: "%s"' % packageName, "red"), "bold"))
                    Console.indent()
                    Console.info(Console.colorize(Console.colorize('Version is NOT OK (needed: %s installed: %s)' % (minVersion, versions[packageName.lower()]) , "red"), "bold"))
                    Console.info('Update to the newest version of %s using %s' % (packageName, updatePath))
                    Console.outdent()
                    return False
        else:
            Console.info(Console.colorize(Console.colorize('Jasy requirement error: "%s"' % packageName, "red"), "bold"))
            Console.indent()
            Console.info(Console.colorize(Console.colorize('Did NOT find installation', "red"), "bold"))
            Console.info('Install the newest version of %s using %s' % (packageName, installPath))
            Console.outdent()
            return False

        return True

    allOk = True

    for entry in needs:
        if not checkSingleInstallation(keys, versions, entry["packageName"], entry["minVersion"], entry["installPath"], entry["updatePath"]):
            allOk = False

    return allOk



