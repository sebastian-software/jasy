#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import sys
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
        "minVersion": "2.0",
        "installPath": "'pip install Pygments'",
        "updatePath": "'pip install --upgrade pygments'"
    },
    {
        "packageName": "polib",
        "minVersion": "1.0.3",
        "installPath": "'pip install polib'",
        "updatePath": "'pip install --upgrade polib'"
    },
    {
        "packageName": "requests",
        "minVersion": "2.5.0",
        "installPath": "'pip install requests'",
        "updatePath": "'pip install --upgrade requests'"
    },
    {
        "packageName": "CherryPy",
        "minVersion": "3.6.0",
        "installPath": "'pip install CherryPy'",
        "updatePath": "'pip install --upgrade CherryPy'"
    },
    {
        "packageName": "PyYAML",
        "minVersion": "3.10",
        "installPath": "'pip install PyYAML'",
        "updatePath": "'pip install --upgrade PyYAML'"
    }
]

optionals = [
    {
        "packageName": "misaka",
        "minVersion": "1.0",
        "installPath": "'pip install misaka'",
        "updatePath": "'pip install --upgrade misaka'"
    },
    {
        "packageName": "sphinx",
        "minVersion": "1.3",
        "installPath": "'pip install sphinx'",
        "updatePath": "'pip install --upgrade sphinx'"
    },
    {
        "packageName": "pillow",
        "minVersion": "2.8.0",
        "installPath": "'pip install Pillow'",
        "updatePath": "'pip install --upgrade Pillow'"
    },
    {
        "packageName": "python-dateutil",
        "minVersion": "2.4",
        "installPath": "'pip install python-dateutil'",
        "updatePath": "'pip install --upgrade python-dateutil'"
    },
    {
        "packageName": "pystache",
        "minVersion": "0.5",
        "installPath": "'pip install pystache'",
        "updatePath": "'pip install --upgrade pystache'"
    },
    {
        "packageName": "pathtools",
        "minVersion": "0.1.2",
        "installPath": "'pip install pathtools'",
        "updatePath": "'pip install --upgrade pathtools'"
    },
    {
        "packageName": "beautifulsoup4",
        "minVersion": "4.3",
        "installPath": "'pip install beautifulsoup4'",
        "updatePath": "'pip install --upgrade beautifulsoup4'"
    },
    {
        "packageName": "unidecode",
        "minVersion": "0.4",
        "installPath": "'pip install unidecode'",
        "updatePath": "'pip install --upgrade unidecode'"
    }


]


def doCompleteDoctor():
    """Checks for uninstalled or too old versions of requirements and gives a complete output."""

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
            if LooseVersion(minVersion) > LooseVersion("0.0"):
                if LooseVersion(versions[packageName.lower()]) >= LooseVersion(minVersion):
                    Console.info(Console.colorize('Version is OK (required: %s installed: %s)' % (minVersion, versions[packageName.lower()]), "green"))
                else:
                    Console.info(Console.colorize(Console.colorize('Version installed is too old (required: %s installed: %s)' % (minVersion, versions[packageName.lower()]), "red"), "bold"))
                    Console.info('Update to the newest version of %s using %s' % (packageName, updatePath))
            else:
                Console.info(Console.colorize('Found installation', "green"))
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
    """Checks for uninstalled or too old versions only of requirements and gives error output."""

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
                    Console.info(Console.colorize(Console.colorize('Version installed is too old (required: %s installed: %s)' % (minVersion, versions[packageName.lower()]), "red"), "bold"))
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
