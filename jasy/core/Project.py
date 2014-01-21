#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2012-2014 Sebastian Werner
#

import os, re, fnmatch, copy

import jasy.core.Cache
import jasy.core.Config as Config
import jasy.core.File as File
import jasy.core.Console as Console
import jasy.core.Util as Util

import jasy.vcs.Repository as Repository

import jasy.item.Abstract
import jasy.item.Doc
import jasy.item.Translation
import jasy.item.Class
import jasy.item.Asset

from jasy import UserError


__all__ = ["Project", "getProjectFromPath", "getProjectDependencies"]

repositoryFolder = re.compile(r"^([a-zA-Z0-9\.\ _-]+)-([a-f0-9]{40})$")
projects = {}
structures = {}

def addStructure(name, structure):
    structures[name] = structure


addStructure("application", {
    "source/class/*.js" : {
        "type" : "jasy.Class"
    },
    "source/style/*.style" : {
        "type" : "jasy.Style"
    },
    "source/translation/*.{po,properties,txt}" : {
        "type" : "jasy.Translation"
    },
    "source/asset/*" : {
        "type" : "jasy.Asset"
    },
    "source/class/*{package.md,readme.md}" : {
        "type" : "jasy.Doc"
    }
})

addStructure("resource", {
    "src/*.js" : {
        "type" : "jasy.Class"
    },
    "src/*.style" : {
        "type" : "jasy.Style"
    },
    "src/*" : {
        "type" : "jasy.Asset"
    }
})

addStructure("flat", {
    "class/*.js" : {
        "type" : "jasy.Class"
    },
    "style/*.style" : {
        "type" : "jasy.Style"
    },
    "asset/*" : {
        "type" : "jasy.Asset"
    },
    "translation/*.{po,properties,txt}" : {
        "type" : "jasy.Translation"
    }
})



def getProjectFromPath(path, session, config=None, version=None):
    global projects

    if not path in projects:
        projects[path] = Project(path, session, config, version)

    return projects[path]


def getProjectDependencies(project, checkoutDirectory="external", updateRepositories=True):
    """ Returns a sorted list of projects depending on the given project (including the given one) """

    def __resolve(project):

        name = project.getName()

        # List of required projects
        Console.info("Getting requirements of %s...", Console.colorize(name, "bold"))
        Console.indent()
        requires = project.getRequires(checkoutDirectory, updateRepositories)
        Console.outdent()

        if not requires:
            return

        Console.debug("Processing %s requirements...", len(requires))
        Console.indent()

        # Adding all project in reverse order.
        # Adding all local ones first before going down to their requirements
        childProjects = []
        for requiredProject in reversed(requires):
            requiredName = requiredProject.getName()
            if not requiredName in names:
                Console.debug("Adding: %s %s (via %s)", requiredName, requiredProject.version, project.getName())
                names[requiredName] = True
                result.append(requiredProject)
                childProjects.append(requiredProject)
            elif not requiredProject in result:
                Console.debug("Blocking: %s %s (via %s)", requiredName, requiredProject.version, project.getName())
                requiredProject.pause()

        # Process all requirements of added projects
        for requiredProject in reversed(childProjects):
            if requiredProject.hasRequires():
                __resolve(requiredProject)

        Console.outdent()

    result = [project]
    names = {
        project.getName() : True
    }

    __resolve(project)

    return result



def getProjectNameFromPath(path):
    name = os.path.basename(path)

    # Remove folder SHA1 postfix when cloned via git etc.
    clone = repositoryFolder.match(name)
    if clone is not None:
        name = clone.group(1)

    # Slashes are often used as a separator to optional data
    if "-" in name:
        name = name[:name.rindex("-")]

    return name


class Project():

    kind = "none"
    scanned = False


    def __init__(self, path, session, config=None, version=None):
        """
        Constructor call of the project.

        - First param is the path of the project relative to the current working directory.
        - Config can be read from jasyproject.json or using constructor parameter @config
        - Parent is used for structural debug messages (dependency trees)
        """

        if not os.path.isdir(path):
            raise UserError("Invalid project path: %s" % path)

        # Only store and work with full path
        self.__path = os.path.abspath(os.path.expanduser(path))

        # Store given params
        self.version = version

        # Intialize item registry
        self.items = {}

        self.__session = session

        # Load project configuration
        self.__config = Config.Config(config)
        self.__config.loadValues(os.path.join(self.__path, "jasyproject"), optional=True)

        # Initialize cache
        try:
            File.mkdir(os.path.join(self.__path, ".jasy"))
            self.__cache = jasy.core.Cache.Cache(self.__path, filename=".jasy/cache")
        except IOError as err:
            raise UserError("Could not initialize project. Cache file in %s could not be initialized! %s" % (self.__path, err))

        # Detect version changes
        if version is None:
            self.__modified = True
        else:
            cachedVersion = self.__cache.read("project[version]")
            self.__modified = cachedVersion != version
            self.__cache.store("project[version]", version)

        # Read name from manifest or use the basename of the project's path
        self.__name = self.__config.get("name", getProjectNameFromPath(self.__path))

        # Read requires
        self.__requires = self.__config.get("requires", {})

        # Defined whenever no package is defined and classes/styles/assets are not stored in the toplevel structure.
        self.__package = self.__config.get("package", self.__name if self.__config.has("name") else None)

        # Read fields (for injecting data into the project and build permutations)
        self.__fields = self.__config.get("fields", {})

        # Read setup for running command pre-scan
        self.__setup = self.__config.get("setup")



    #
    # Project Scan/Init
    #

    def scan(self):

        if self.scanned:
            return

        updatemsg = "[updated]" if self.__modified else "[cached]"

        if self.version:
            Console.info("Scanning %s @ %s %s...", Console.colorize(self.getName(), "bold"), Console.colorize(self.version, "magenta"), Console.colorize(updatemsg, "grey"))
        else:
            Console.info("Scanning %s %s...", Console.colorize(self.getName(), "bold"), Console.colorize(updatemsg, "grey"))

        Console.indent()

        # Support for pre-initialize projects...
        setup = self.__setup
        if setup and self.__modified:
            Console.info("Running setup...")
            Console.indent()

            for cmd in setup:
                Console.info("Executing %s...", cmd)

                result = None
                try:
                    result = None
                    result = Util.executeCommand(cmd, "Failed to execute setup command %s" % cmd, path=self.__path)
                except Exception as ex:
                    if result:
                        Console.error(result)

                    raise UserError("Could not scan project %s: %s" % (self.__name, ex))

            Console.outdent()

        # Processing custom content section. Only supports classes and assets.
        if self.__config.has("content"):
            self.kind = "manual"
            self.__addContent(self.__config.get("content"))

        else:
            # Read scan path from config
            if not self.__config.has("scan"):
                if self.__hasDir("source"):
                    self.kind = "application"
                    scan = self.__resolveScanConfig(structures[self.kind])
                elif self.__hasDir("src"):
                    self.kind = "resource"
                    scan = self.__resolveScanConfig(structures[self.kind])
                else:
                    self.kind = "flat"
                    scan = self.__resolveScanConfig(structures[self.kind])

            else:
                scan = self.__resolveScanConfig(self.__config.get("scan"))

            for config in scan:
                if type(config["paths"]) == str:
                    self.__addDir(config["paths"], config["regex"], config["type"], config["package"])
                else:
                    for path in config["paths"]:
                        self.__addDir(path, config["regex"], config["type"], config["package"])

        # Generate summary
        summary = []
        for section in self.items.keys():
            content = self.items[section]
            name, constructor = self.__resolveConstructor(section)
            if content:
                summary.append(Console.colorize("%s %s" % (len(content), name), "magenta"))

        # Print out
        if summary:
            Console.info("Content: %s" % (", ".join(summary)))

        self.scanned = True

        Console.outdent()



    def __createPathRe(self, path):
        if not "{" in path:
            return fnmatch.translate(path), os.path.dirname(path)

        start = path.index("{")
        end = path.index("}")
        expanders = [p.strip() for p in path[start+1:end].split(",")]

        prefix = path[:start]
        postfix = path[end+1:]

        pathres = [self.__createPathRe(prefix + element + postfix) for element in expanders]
        regex = "|".join(["(" + pathel + ")" for pathel, path in pathres])
        paths = set([path for pathel, path in pathres])

        return regex, paths


    def __resolveScanConfig(self, configs):
        scan = []

        for path, config in configs.items():
            if type(config) == str:
                config = {
                    "type": config,
                    "package": self.__package
                }

            else:
                config = copy.deepcopy(config)

            if not "type" in config:
                raise UserError("No type configured in jasyproject configuration (scan section)")

            if not "package" in config:
                config["package"] = self.__package

            if config["package"] == "":
                config["package"] = None

            config["origpath"] = path
            config["regex"], config["paths"] = self.__createPathRe(path)

            scan.append(config)


        def specificitySort(item):
            """ Sorts for specificy of given scan path """
            origPath = item["origpath"]

            if not "*" in origPath:
                num = 10000
            elif not origPath.endswith("*"):
                num = 1000
            else:
                num = 0

            num += len(origPath)
            return -num


        scan.sort(key=specificitySort)

        return scan



    def __resolveConstructor(self, itemType):
        construct = self.__session.getItemType(itemType)

        if not construct:
            raise UserError("Could not resolve item type %s" % itemType)

        return construct


    #
    # FILE SYSTEM INDEXER
    #

    def __hasDir(self, directory):
        full = os.path.join(self.__path, directory)
        if os.path.exists(full):
            if not os.path.isdir(full):
                raise UserError("Expecting %s to be a directory: %s" % full)

            return True

        return False


    def __addContent(self, content):
        Console.info("Adding manual content")

        Console.indent()
        for fileId in content:
            entry = content[fileId]
            if type(entry) is not dict:
                raise UserError("Invalid manual content section for file %s. Requires a dict with type and source definition!" % fileId)

            itemType = entry["type"]
            fileContent = entry["source"]

            if len(fileContent) == 0:
                raise UserError("Empty content!")

            # Support for joining text content
            if len(fileContent) == 1:
                filePath = os.path.join(self.__path, fileContent[0])
            else:
                filePath = [os.path.join(self.__path, filePart) for filePart in fileContent]

            name, construct = self.__resolveConstructor(itemType)
            item = construct(self, fileId).attach(filePath)
            Console.debug("Registering %s %s" % (item.kind, fileId))

            if not itemType in self.items:
                self.items[itemType] = {}

            # Check for duplication
            if fileId in self.items[itemType]:
                raise UserError("Item ID was registered before: %s" % fileId)

            self.items[itemType][fileId] = item

        Console.outdent()


    def __addDir(self, directory, regex, type, package):
        check = re.compile(regex)

        path = os.path.join(self.__path, directory)
        if not os.path.exists(path):
            return

        Console.debug("Scanning directory: %s" % directory)
        Console.indent()

        for dirPath, dirNames, fileNames in os.walk(path):
            for dirName in dirNames:
                # Filter dotted directories like .git, .bzr, .hg, .svn, etc.
                if dirName.startswith("."):
                    dirNames.remove(dirName)

            relDirPath = os.path.relpath(dirPath, path)

            for fileName in fileNames:

                if fileName[0] == ".":
                    continue

                relPath = os.path.normpath(os.path.join(relDirPath, fileName)).replace(os.sep, "/")

                if not check.match(os.path.join(directory, relPath).replace(os.sep, "/")):
                    continue

                fullPath = os.path.join(dirPath, fileName)
                self.addFile(relPath, fullPath, type, package)

        Console.outdent()


    def addFile(self, relPath, fullPath, itemType, package, override=False):

        fileName = os.path.basename(relPath)
        fileExtension = os.path.splitext(fileName)[1]

        name, construct = self.__resolveConstructor(itemType)
        item = construct.fromPath(self, relPath, package).attach(fullPath)
        fileId = item.getId()
        Console.debug("Registering %s %s" % (item.kind, fileId))

        if not itemType in self.items:
            self.items[itemType] = {}

        # Check for duplication
        if fileId in self.items[itemType] and not override:
            raise UserError("Item ID was registered before: %s" % fileId)

        self.items[itemType][fileId] = item



    #
    # ESSENTIALS
    #

    def hasRequires(self):
        return len(self.__requires) > 0


    def getRequires(self, checkoutDirectory="external", updateRepositories=True):
        """
        Return the project requirements as project instances
        """

        global projects

        result = []

        for entry in self.__requires:

            if type(entry) is dict:
                source = entry["source"]
                config = Util.getKey(entry, "config")
                version = Util.getKey(entry, "version")
                kind = Util.getKey(entry, "kind")
            else:
                source = entry
                config = None
                version = None
                kind = None

            # Versions are expected being string type
            if version is not None:
                version = str(version)

            revision = None

            if Repository.isUrl(source):
                kind = kind or Repository.getType(source)
                path = os.path.abspath(os.path.join(checkoutDirectory, Repository.getTargetFolder(source, version)))

                # Only clone and update when the folder is unique in this session
                # This reduces git/hg/svn calls which are typically quite expensive
                if not path in projects:
                    revision = Repository.update(source, version, path, updateRepositories)
                    if revision is None:
                        raise UserError("Could not update repository %s" % source)

            else:
                kind = "local"
                if not source.startswith(("/", "~")):
                    path = os.path.join(self.__path, source)
                else:
                    path = os.path.abspath(os.path.expanduser(source))

                path = os.path.normpath(path)

            if path in projects:
                project = projects[path]

            else:
                fullversion = []

                # Produce user readable version when non is defined
                if version is None and revision is not None:
                    version = "master"

                if version is not None:
                    if "/" in version:
                        fullversion.append(version[version.rindex("/")+1:])
                    else:
                        fullversion.append(version)

                if revision is not None:
                    # Shorten typical long revisions as used by e.g. Git
                    if type(revision) is str and len(revision) > 20:
                        fullversion.append(revision[:10])
                    else:
                        fullversion.append(revision)

                if fullversion:
                    fullversion = "-".join(fullversion)
                else:
                    fullversion = None

                project = Project(path, self.__session, config, fullversion)
                projects[path] = project

            result.append(project)

        return result


    def getFields(self):
        """ Return the project defined fields which may be configured by the build script """
        return self.__fields

    def getClassByName(self, className):
        """ Finds a class by its name."""

        try:
            return self.getClasses()[className]
        except KeyError:
            return None

    def getName(self):
        return self.__name

    def getPath(self):
        return self.__path

    def getPackage(self):
        return self.__package

    def getConfigValue(self, key, default=None):
        return self.__config.get(key, default)

    def toRelativeUrl(self, path, prefix="", subpath="source"):
        root = os.path.join(self.__path, subpath)
        relpath = os.path.relpath(path, root)

        if prefix:
            if not prefix[-1] == os.sep:
                prefix += os.sep

            relpath = os.path.normpath(prefix + relpath)

        return relpath.replace(os.sep, "/")

    def getRevision(self):
        """
        Returns the current revision of the project
        """

        return Repository.getRevision(self.__path) or "unknown"




    #
    # CACHE API
    #

    def getCache(self):
        """Returns the cache instance"""

        return self.__cache

    def clean(self):
        """Clears the cache of the project"""

        Console.info("Clearing cache of %s..." % self.__name)
        self.__cache.clear()

    def close(self):
        """Closes the project which deletes the internal caches"""

        if self.__cache:
            self.__cache.close()
            self.__cache = None

        self.classes = None
        self.assets = None
        self.docs = None
        self.translations = None

    def pause(self):
        """Pauses the project so that other processes could modify/access it"""

        self.__cache.close()

    def resume(self):
        """Resumes the paused project"""

        self.__cache.open()


    def isReady(self):
        return self.__cache is not None



    #
    # LIST ACCESSORS
    #

    def getItems(self, type):
        """ Returns all items of given type. """

        if not self.scanned:
            self.scan()

        if not type in self.items:
            return None

        return self.items[type]


    def getItem(self, type, name):
        """ Return item of given type and name """
        items = self.getItems(type)

        if items and name in items:
            return items[name]

        return None


    def addItem(self, type, item):
        """ Add item to item list of given type """

        if not type in self.items:
            self.items[type] = {}

        self.items[type][item.getId()] = item


    def getDocs(self):
        """Returns all package docs"""

        return self.getItems("jasy.Doc") or {}


    def getClasses(self):
        """ Returns all project classes. Requires all files to have a "js" extension. """

        return self.getItems("jasy.Class") or {}


    def getStyles(self):
        """ Returns all project style styles. Requires all files to have a "sht" extension. """

        return self.getItems("jasy.Style") or {}


    def getTranslations(self):
        """ Returns all translation objects """

        return self.getItems("jasy.Translation") or {}


    def getAssets(self):
        """ Returns all project asssets (images, stylesheets, static data, etc.). """

        return self.getItems("jasy.Asset") or {}

