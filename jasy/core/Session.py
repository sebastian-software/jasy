#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import atexit, os, zlib, shutil

import jasy.core.Config as Config
import jasy.core.Project as Project
import jasy.core.Util as Util
import jasy.core.Console as Console

import jasy.item.Asset
import jasy.item.Class
import jasy.item.Doc
import jasy.item.Style
import jasy.item.Translation

from jasy import UserError


class Session():
    """
    Manages all projects.
    """

    # Environment object used for executing jasyscript.py.
    # Contains all items from the main projects jasyscript.py +
    # all shared (namespaced) commands from all jasylibrary.py files.
    __scriptEnvironment = None

    # List of all projects in priority order
    __projects = None

    # Virtual project to store dynamically created classes
    __virtualProject = None

    # Whether repositories should be auto updated before projects should be initialized
    __updateRepositories = True

    # All (active) fields as defined by the active projects
    __fields = None

    # Dictionary which maps command names to the implementation function
    __commands = None

    # Translation bundles created by merged data from active projects
    __translationBundles = None




    #
    # Core
    #

    def __init__(self):

        atexit.register(self.close)

        self.__projects = []
        self.__fields = {}
        self.__commands = {}
        self.__translationBundles = {}
        self.__postscans = []
        self.__itemType = {}

        self.addItemType("jasy.Asset", "Assets", jasy.item.Asset.AssetItem)
        self.addItemType("jasy.Class", "Classes", jasy.item.Class.ClassItem)
        self.addItemType("jasy.Doc", "Docs", jasy.item.Doc.DocItem)
        self.addItemType("jasy.Style", "Styles", jasy.item.Style.StyleItem)
        self.addItemType("jasy.Translation", "Translations", jasy.item.Translation.TranslationItem)


    def init(self, autoInitialize=True, updateRepositories=True, scriptEnvironment=None):
        """
        Initialize the actual session with projects

        :param autoInitialize: Whether the projects should be automatically added when the current folder contains a valid Jasy project.
        :param updateRepositories: Whether to update repositories of all project dependencies.
        :param scriptEnvironment: API object as being used for loadLibrary to add Python features offered by projects.
        :param commandEnvironment: API object as being used for loadCommands to add Python features for any item nodes.
        """

        self.__scriptEnvironment = scriptEnvironment
        self.__updateRepositories = updateRepositories

        if autoInitialize and Config.findConfig("jasyproject"):

            Console.info("Initializing session...")
            Console.indent()

            try:
                self.addProject(Project.getProjectFromPath(".", self))

            except UserError as err:
                Console.outdent(True)
                Console.error(err)
                raise UserError("Critical: Could not initialize session!")

            self.getVirtualProject()

            Console.debug("Active projects (%s):", len(self.__projects))
            Console.indent()

            for project in self.__projects:
                if project.version:
                    Console.debug("%s @ %s", Console.colorize(project.getName(), "bold"), Console.colorize(project.version, "magenta"))
                else:
                    Console.debug(Console.colorize(project.getName(), "bold"))

            Console.outdent()
            Console.outdent()



    def setCurrentTask(self, name=None):
        if name:
            Console.header(name)

        self.__currentTask = name


    def getCurrentTask(self):
        return self.__currentTask


    def scan(self):
        """ Scans all registered projects """

        Console.info("Scanning projects...")
        Console.indent()

        for project in self.__projects:
            project.scan()

        for postscan in self.__postscans:
            postscan()

        Console.outdent()


    def clean(self):
        """Clears all caches of all registered projects"""

        if not self.__projects:
            return

        Console.info("Cleaning session...")
        Console.indent()

        for project in self.__projects:
            project.clean()

        path = os.path.abspath(os.path.join(".jasy", "locale"))
        if os.path.exists(path):
            Console.info("Cleaning up locale project...")
            shutil.rmtree(path)

        path = os.path.abspath(os.path.join(".jasy", "virtual"))
        if os.path.exists(path):
            Console.info("Cleaning up virtual project...")
            shutil.rmtree(path)

        Console.outdent()


    def close(self):
        """Closes the session and stores cache to the harddrive."""

        if not self.__projects:
            return

        Console.debug("Closing session...")
        Console.indent()

        for project in self.__projects:
            project.close()

        self.__projects = None

        Console.outdent()


    def pause(self):
        """
        Pauses the session. This release cache files etc. and makes
        it possible to call other jasy processes on the same projects.
        """

        Console.info("Pausing session...")

        for project in self.__projects:
            project.pause()


    def resume(self):
        """Resumes the session after it has been paused."""

        Console.info("Resuming session...")

        for project in self.__projects:
            project.resume()


    def getFields(self):
        return self.__fields


    def getClassByName(self, className):
        """
        Queries all currently registered projects for the given class and returns the class item.
        Returns None when no matching class item was found.

        :param className: Any valid classname from any of the projects.
        :type className: str
        """

        for project in self.__projects:
            classes = project.getClasses()
            if className in classes:
                return classes[className]

        return None


    def getStyleByName(self, styleName):
        """
        Queries all currently registered projects for the given style and returns the style item.
        Returns None when no matching style item was found.

        :param styleName: Any valid styleName from any of the projects.
        :type styleName: str
        """

        for project in self.__projects:
            styles = project.getStyles()
            if styleName in styles:
                return styles[styleName]

        return None

    #
    # Item type handling
    #
    def addItemType(self, itemType, name, cls):
        self.__itemType[itemType] = (name, cls)


    def getItemType(self, itemType):
        if not itemType in self.__itemType:
            return None

        return self.__itemType[itemType]


    def getItemTypes(self):
        return self.__itemType


    #
    # Project Managment
    #

    def addProject(self, project):
        """
        Adds the given project to the list of known projects. Projects should be added in order of
        their priority. This adds the field configuration of each project to the session fields.
        Fields must not conflict between different projects (same name).

        :param project: Instance of Project to append to the list
        :type project: object
        """

        result = Project.getProjectDependencies(project, "external", self.__updateRepositories)
        for project in result:

            Console.info("Adding %s...", Console.colorize(project.getName(), "bold"))
            Console.indent()

            # Append to session list
            self.__projects.append(project)

            # Import library methods
            libraryPath = os.path.join(project.getPath(), "jasylibrary.py")
            if os.path.exists(libraryPath):
                self.loadLibrary(project.getName(), libraryPath, doc="Library of project %s" % project.getName())

            # Import command methods
            commandPath = os.path.join(project.getPath(), "jasycommand.py")
            if os.path.exists(commandPath):
                self.loadCommands(project.getName(), commandPath)

            # Import project defined fields which might be configured using "activateField()"
            fields = project.getFields()
            for name in fields:
                entry = fields[name]

                if name in self.__fields:
                    raise UserError("Field '%s' was already defined!" % (name))

                if "check" in entry:
                    check = entry["check"]
                    if check in ["Boolean", "String", "Number"] or type(check) == list:
                        pass
                    else:
                        raise UserError("Unsupported check: '%s' for field '%s'" % (check, name))

                self.__fields[name] = entry


            Console.outdent()


    def loadLibrary(self, objectName, fileName, encoding="utf-8", doc=None):
        """
        Creates a new object inside the user API (jasyscript.py) with the given name
        containing all @share'd functions and fields loaded from the given file.
        """

        if objectName in self.__scriptEnvironment:
            raise UserError("Could not import library %s as the object name %s is already used." % (fileName, objectName))

        # Create internal class object for storing shared methods
        class Shared(object): pass
        exportedModule = Shared()
        exportedModule.__doc__ = doc or "Imported from %s" % os.path.relpath(fileName, os.getcwd())
        counter = 0

        # Method for being used as a decorator to share methods to the outside
        def share(func):
            nonlocal counter
            setattr(exportedModule, func.__name__, func)
            counter += 1

            return func

        def itemtype(type, name):
            def wrap(cls):
                id = "%s.%s" % (objectName, type[0].upper() + type[1:])
                self.addItemType(id, name, cls)
                return cls
            return wrap

        def postscan():
            def wrap(f):
                self.__postscans.append(f)
                return f
            return wrap

        # Execute given file. Using clean new global environment
        # but add additional decorator for allowing to define shared methods
        # and the session object (self).
        code = open(fileName, "r", encoding=encoding).read()
        exec(compile(code, os.path.abspath(fileName), "exec"), {"share" : share, "itemtype": itemtype, "postscan": postscan, "session" : self})

        # Export destination name as global
        self.__scriptEnvironment[objectName] = exportedModule

        Console.info("Imported %s.", Console.colorize("%s methods" % counter, "magenta"))

        return counter



    def loadCommands(self, objectName, fileName, encoding="utf-8"):
        """
        Loads new commands into the session wide command registry.
        """

        counter = 0
        commands = self.__commands

        # Method for being used as a decorator to share methods to the outside
        def share(func):
            name = "%s.%s" % (objectName, func.__name__)
            if name in commands:
                raise Exception("Command %s already exists!" % name)

            commands[name] = func

            nonlocal counter
            counter += 1

            return func

        # Execute given file. Using clean new global environment
        # but add additional decorator for allowing to define shared methods
        # and the session object (self).
        code = open(fileName, "r", encoding=encoding).read()
        exec(compile(code, os.path.abspath(fileName), "exec"), {"share" : share, "session" : self})

        # Export destination name as global
        Console.info("Imported %s.", Console.colorize("%s commands" % counter, "magenta"))

        return counter


    def addCommand(self, name, func, restype=None):
        """ Registers the given function as a new command """

        if len(name.split(".")) != 2:
            raise Exception("Command names should always match namespace.name! Tried with: %s!" % name)

        commands = self.__commands

        if name in commands:
            raise Exception("Command %s already exists!" % name)

        commands[name] = {
            "func" : func,
            "restype" : restype
        }


    def getCommands(self):
        """ Returns a dictionary of all commands """

        return self.__commands



    def getProjects(self):
        """
        Returns all currently registered projects.
        """

        return self.__projects


    def getProjectByName(self, name):
        """Returns a project by its name"""

        for project in self.__projects:
            if project.getName() == name:
                return project

        return None


    def getRelativePath(self, project):
        """Returns the relative path of any project to the main project"""

        mainPath = self.__projects[0].getPath()
        projectPath = project.getPath()

        return os.path.relpath(projectPath, mainPath)


    def getMain(self):
        """
        Returns the main project which is the first project added to the
        session and the one with the highest priority.
        """

        if self.__projects:
            return self.__projects[0]
        else:
            return None


    def getVirtualProject(self):
        """
        Returns the virtual project for this application. The project
        offers storage for dynamically created JavaScript classes and
        other files. Storage is kept intact between different Jasy sessions.
        """

        # Create only once per session
        if self.__virtualProject:
            return self.__virtualProject

        # Place virtual project in application's ".jasy" folder
        path = os.path.abspath(os.path.join(".jasy", "virtual"))

        # Set package to empty string to allow for all kind of namespaces in this virtual project
        jasy.core.File.write(os.path.join(path, "jasyproject.yaml"), 'name: virtual\npackage: ""\n')

        # Generate project instance from path, store and return
        project = Project.getProjectFromPath(path, self)
        self.__virtualProject = project
        self.__projects.append(project)

        return project


    def getVirtualItem(self, baseName, itemClass, text, extension):
        virtualProject = self.getVirtualProject()

        # Tweak name by content checksum to make all results of the
        # same content being cachable by the normal infrastructure.
        checksum = zlib.adler32(text.encode("utf-8"))
        fileId = "%s-%s" % (baseName, checksum)

        # Try to reuse existing item e.g. from previous run
        item = virtualProject.getClassByName(fileId)
        if item:
            return item

        # Generate path from file ID.
        # Put file into "src" folder
        filePath = os.path.join(virtualProject.getPath(), "src", fileId.replace(".", os.sep)) + extension

        # Create a class dynamically and add it to both,
        # the virtual project and our requirements list.
        item = itemClass(virtualProject, fileId)
        item.saveText(text, filePath)

        return item




    #
    # Translation Support
    #

    def getAvailableTranslations(self):
        """
        Returns a set of all available translations

        This is the sum of all projects so even if only one
        project supports "fr_FR" then it will be included here.
        """

        supported = set()
        for project in self.__projects:
            supported.update(project.getTranslations().keys())

        return supported


    def getTranslationBundle(self, language=None):
        """
        Returns a translation object for the given language containing
        all relevant translation files for the current project set.
        """

        if language is None:
            return None

        if language in self.__translationBundles:
            return self.__translationBundles[language]

        Console.info("Creating translation bundle: %s", language)
        Console.indent()

        # Initialize new Translation object with no project assigned
        # This object is used to merge all seperate translation instances later on.
        combined = jasy.item.Translation.TranslationItem(None, id=language)
        relevantLanguages = self.__expandLanguage(language)

        # Loop structure is build to prefer finer language matching over project priority
        for currentLanguage in reversed(relevantLanguages):
            for project in self.__projects:
                for translation in project.getTranslations().values():
                    if translation.getLanguage() == currentLanguage:
                        Console.debug("Adding %s entries from %s @ %s...", len(translation.getTable()), currentLanguage, project.getName())
                        combined += translation

        Console.info("Combined number of translations: %s", len(combined.getTable()))
        Console.outdent()

        self.__translationBundles[language] = combined
        return combined


    def __expandLanguage(self, language):
        """Expands the given language into a list of languages being used in priority order (highest first)"""

        # Priority Chain:
        # de_DE => de => C (default language) => code

        all = [language]
        if "_" in language:
            all.append(language[:language.index("_")])
        all.append("C")

        return all


