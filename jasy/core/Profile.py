#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import jasy

import time, socket, uuid, getpass, copy
import itertools, json, os

import jasy.core.Console as Console
import jasy.core.FileManager as FileManager
import jasy.core.Util as Util
import jasy.core.Permutation as Permutation
import jasy.core.Locale as Locale
import jasy.core.Project as Project

import jasy.asset.Manager as AssetManager
import jasy.item.Class as ClassItem

class Profile():
    """
    Configuration object for the build profile of the current task
    """

    #
    # CONFIGURATION DATA STRUCTURE
    #

    # Configuration data
    __data = None

    # Application fields
    __fields = None

    # Application parts
    __parts = None


    #
    # CURRENT STATE
    #

    # Current permutation
    __permutation = None

    # Current permutation bundle
    __translationBundle = None



    __timeStamp = None
    __timeHash = None


    def __init__(self, session):

        Console.info("Initializing profile...")
        Console.indent()

        # Reference to global session object
        self.__session = session

        # Initialize data instance
        self.__data = {}


        # Set default values (which require serialization)
        self.setJsOutputFolder("js")
        self.setCssOutputFolder("css")
        self.setAssetOutputFolder("asset")
        self.setTemplateOutputFolder("tmpl")

        self.setCompressionLevel(0)
        self.setFormattingLevel(100)



        # Enforce scan of projects
        session.scan()

        # Part registry holds information about all parts of the application to build
        self.__parts = {}

        # Copy fields and commands from session
        # This happens to have local access to all of them + being able to add and tweak data locally
        self.__fields = copy.copy(session.getFields())
        self.__commands = copy.copy(session.getCommands())

        # Behaves like Date.now() in JavaScript: UTC date in milliseconds
        self.__timeStamp = int(round(time.time() * 1000))
        self.__timeHash = Util.generateChecksum(str(self.__timeStamp))

        # Initialize objects
        fileManager = self.__fileManager = FileManager.FileManager(self)

        # Initialize asset manager
        Console.info("Initializing asset manager...")
        Console.indent()
        assetManager = self.__assetManager = AssetManager.AssetManager(self)

        # Registering assets
        for project in self.getProjects():
            assetManager.addProject(project)

        # Enable sprite sheets and image animations
        assetManager.processSprites()
        assetManager.processAnimations()

        Console.outdent()

        # Registering commands
        Console.info("Registering commands...")

        self.addCommand("asset.url", lambda fileId: assetManager.getAssetUrl(fileId), "url")
        self.addCommand("asset.width", lambda fileId: assetManager.getAssetWidth(fileId), "px")
        self.addCommand("asset.height", lambda fileId: assetManager.getAssetHeight(fileId), "px")

        self.addCommand("sprite.url", lambda fileId: assetManager.getSpriteUrl(fileId), "url")
        self.addCommand("sprite.left", lambda fileId: assetManager.getSpriteLeft(fileId), "px")
        self.addCommand("sprite.top", lambda fileId: assetManager.getSpriteTop(fileId), "px")
        self.addCommand("sprite.width", lambda fileId: assetManager.getSpriteWidth(fileId), "px")
        self.addCommand("sprite.height", lambda fileId: assetManager.getSpriteHeight(fileId), "px")

        self.addCommand("animation.columns", lambda fileId: assetManager.getAnimationColumns(fileId), "number")
        self.addCommand("animation.rows", lambda fileId: assetManager.getAnimationRows(fileId), "number")
        self.addCommand("animation.frames", lambda fileId: assetManager.getAnimationFrames(fileId), "number")

        Console.outdent()






    #
    # PROJECT API
    #

    def getProjects(self):
        """
        Returns all currently registered projects.
        Injects locale project when current permutation has configured a locale.
        """

        projects = self.__session.getProjects()

        localeProject = self.getCurrentLocaleProject()
        if localeProject:
            return projects + [localeProject]

        return projects



    #
    # OBJECT ACCESSORS
    #

    def getSession(self):
        return self.__session

    def getAssetManager(self):
        return self.__assetManager

    def getFileManager(self):
        return self.__fileManager




    #
    # PART MANAGEMENT
    #

    def getParts(self):
        return self.__parts


    def registerPart(self, name, className="", styleName="", templateName=""):
        if name in self.__parts:
            raise Exception("The part %s is already registered!")

        self.__parts[name] = {
            "class" : className,
            "style" : styleName,
            "template" : templateName
        }




    #
    # GENERIC STORAGE API
    #

    def setValue(self, key, value):
        if value is None:
            del self.__data[key]
        else:
            self.__data[key] = value

        # Invalidate ID
        self.__id = None

        return value

    def getValue(self, key, fallback=None):
        value = None

        if key in self.__data:
            value = self.__data[key]

        if value is None and fallback is not None:
            if callable(fallback):
                value = fallback()
            else:
                value = fallback

        return value

    def getMatchingValues(self, matcher, transformer=None):
        result = {}

        data = self.__data
        for key in data:
            if matcher(key):
                if transformer:
                    result[transformer(key)] = data[key]
                else:
                    result[key] = data[key]

        return result


    def setFlag(self, name, value):
        return self.setValue("enable-%s" % name, value)

    def getFlag(self, name, fallback=None):
        return self.getValue("enable-%s" % name, fallback)

    def setOutputFolder(self, type, value):
        return self.setValue("output-folder-%s" % type, value)

    def getOutputFolder(self, type, fallback=None):
        return self.getValue("output-folder-%s" % type, fallback)

    def getOutputFolders(self):
        return self.getMatchingValues(
            lambda key: key.startswith("output-folder-"),
            lambda key: key[14:]
        )



    #
    # DESTINATION SETUP
    #

    def getDestinationPath(self):
        """ Relative or path of the destination folder """
        return self.getValue("destination-path", self.__session.getCurrentTask())

    def setDestinationPath(self, path):
        self.setValue("destination-path", path)

    def getDestinationUrl(self):
        """ The same as destination folder but from the URL/server perspective """
        return self.getValue("destination-url")

    def setDestinationUrl(self, url):
        # Fix missing end slash
        if not url.endswith("/"):
            url += "/"

        self.setValue("destination-url", url)





    #
    # OUTPUT FOLDER NAMES
    #

    def getCssOutputFolder(self):
        """ Name of the folder inside the destination folder for storing generated style sheets """
        return self.getOutputFolder("css", "css")

    def setCssOutputFolder(self, folder):
        return self.setOutputFolder("css", folder)

    def getJsOutputFolder(self):
        """ Name of the folder inside the destination folder for storing generated script files """
        return self.getOutputFolder("js", "js")

    def setJsOutputFolder(self, folder):
        return self.setOutputFolder("js", folder)

    def getAssetOutputFolder(self):
        """ Name of the folder inside the destination folder for storing used assets """
        return self.getOutputFolder("asset", "asset")

    def setAssetOutputFolder(self, folder):
        return self.setOutputFolder("asset", folder)

    def getTemplateOutputFolder(self):
        """ Name of the folder inside the destination folder for storing compiled templates """
        return self.getOutputFolder("template", "tmpl")

    def setTemplateOutputFolder(self, folder):
        return self.setOutputFolder("template", folder)



    #
    # RUNTIME STATE
    #

    def getWorkingPath(self):
        return self.getValue("working-path")

    def setWorkingPath(self, path):
        return self.setValue("working-path", path)

    def getCurrentTranslation(self):
        return self.__translationBundle

    def getCurrentPermutation(self):
        """Returns current permutation object (useful during looping through permutations via permutate())."""
        return self.__permutation

    def resetCurrentPermutation(self):
        """Resets the current permutation object."""
        self.__permutation = None



    #
    # CONFIGURATION OPTIONS
    #

    def getHashAssets(self):
        return self.getFlag("hash-assets")

    def setHashAssets(self, enable):
        return self.setFlag("hash-assets", enable)

    def getCopyAssets(self):
        return self.getFlag("copy-assets")

    def setCopyAssets(self, enable):
        return self.setFlag("copy-assets", enable)

    def getUseSource(self):
        return self.getFlag("use-source")

    def setUseSource(self, enable):
        return self.setFlag("use-source", enable)




    #
    # OUTPUT FORMATTING/COMPRESSION SETTINGS
    #

    def getCompressionLevel(self):
        return self.getValue("compression-level")

    def setCompressionLevel(self, level):
        return self.setValue("compression-level", level)

    def getFormattingLevel(self):
        return self.getValue("formatting-level")

    def setFormattingLevel(self, level):
        return self.setValue("formatting-level", level)



    #
    # EXPORT DATA FOR CLIENT SIDE
    #

    def exportData(self):
        return {
            "root" : self.getDestinationUrl() or self.getDestinationFolder()
        }



    #
    # MAIN BUILD METHOD
    #

    def __getEnvironmentId(self):
        """
        Returns a build ID based on environment variables and state
        """

        hostName = socket.gethostname()
        hostId = uuid.getnode()
        userName = getpass.getuser()

        return "host:%s|id:%s|user:%s" % (hostName, hostId, userName)


    def getSetupClasses(self):
        """
        Returns a list of (virtual) classes which are relevant for initial setup.
        """

        setups = {}

        # Add user configured fields from session
        setups.update(self.getFieldSetupClasses())



        # Info about actual build

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.build.env",4,"%s"' % self.__getEnvironmentId())
        setups["jasy.build.env"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.build.rev",4,"%s"' % self.__session.getMain().getRevision())
        setups["jasy.build.rev"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.build.time",4,%s' % self.__timeStamp)
        setups["jasy.build.time"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        # Version of Jasy which was used for build

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.version",4,"%s"' % jasy.__version__)
        setups["jasy.version"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        # Destination URL e.g. CDN

        fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.url",4,"%s"' % (self.getDestinationUrl() or ""))
        setups["jasy.url"] = self.__session.getVirtualItem("jasy.generated.FieldData", ClassItem.ClassItem, fieldSetup, ".js")

        # Output folder names

        for key, value in self.getOutputFolders().items():

            fieldSetup = "jasy.Env.addField([%s]);" % ('"jasy.folder.%s",4,"%s"' % (key, value))
            setups["jasy.folder.%s" % key] = self.__session.getVirtualItem("jasy.generated.OutputFolder", ClassItem.ClassItem, fieldSetup, ".js")

        return setups





    #
    # Support for fields
    # Fields allow to inject data from the build into the running application
    #

    def setLocales(self, locales, default=None):
        """
        Store locales as a special built-in field with optional default value
        """

        self.__fields["locale"] = {
            "values" : locales,
            "default" : default or locales[0],
            "detect" : "core.detect.Locale"
        }


    def setDefaultLocale(self, locale):
        """
        Sets the default locale
        """

        if not "locale" in self.__fields:
            raise UserError("Define locales first!")

        self.__fields["locale"]["default"] = locale



    def getCurrentLocale(self):
        """Returns the current locale as defined in current permutation"""

        permutation = self.getCurrentPermutation()
        if permutation:
            locale = permutation.get("locale")
            if locale:
                return locale

        return None


    def getCurrentLocaleProject(self, update=False):
        """
        Returns a locale project for the currently configured locale.
        Returns None if locale is not set to a valid value.
        """

        locale = self.getCurrentLocale()
        if not locale:
            return None

        path = os.path.abspath(os.path.join(".jasy", "locale", locale))
        if not os.path.exists(path) or update:
            Locale.LocaleParser(locale).export(path)

        return Project.getProjectFromPath(path, self.__session)





    #
    # FIELD API
    #

    def setField(self, name, value):
        """
        Statically configure the value of the given field.

        This field is just injected into Permutation data and used for permutations, but as
        it only holds a single value all alternatives paths are removed/ignored.
        """

        if not name in self.__fields:
            raise Exception("Unsupported field (not defined by any project): %s" % name)

        entry = self.__fields[name]

        # Replace current value with single value
        entry["values"] = [value]

        # Additonally set the default
        entry["default"] = value

        # Delete detection if configured by the project
        if "detect" in entry:
            del entry["detect"]


    def permutateField(self, name, values=None, detect=None, default=None):
        """
        Adds the given key/value pair to the session for permutation usage.

        It supports an optional test. A test is required as soon as there is
        more than one value available. The detection method and values are typically
        already defined by the project declaring the key/value pair.
        """

        if not name in self.__fields:
            raise Exception("Unsupported field (not defined by any project): %s" % name)

        entry = self.__fields[name]

        if values:
            if type(values) != list:
                values = [values]

            entry["values"] = values

            # Verifying values from build script with value definition in project manifests
            if "check" in entry:
                check = entry["check"]
                for value in values:
                    if check == "Boolean":
                        if type(value) == bool:
                            continue
                    elif check == "String":
                        if type(value) == str:
                            continue
                    elif check == "Number":
                        if type(value) in (int, float):
                            continue
                    else:
                        if value in check:
                            continue

                    raise Exception("Unsupported value %s for %s" % (value, name))

            if default is not None:
                entry["default"] = default

        elif "check" in entry and entry["check"] == "Boolean":
            entry["values"] = [True, False]

        elif "check" in entry and type(entry["check"]) == list:
            entry["values"] = entry["check"]

        elif "default" in entry:
            entry["values"] = [entry["default"]]

        else:
            raise Exception("Could not permutate field: %s! Requires value list for non-boolean fields which have no defaults." % name)

        # Store class which is responsible for detection (overrides data from project)
        if detect:
            if not self.getClassByName(detect):
                raise Exception("Could not permutate field: %s! Unknown detect class %s." % detect)

            entry["detect"] = detect


    def __exportFieldDetects(self):
        """
        Returns a dict where the field points to the detection class
        which is being used to figure out the value on the client.
        """

        detects = {}

        for key in sorted(self.__fields):
            source = self.__fields[key]
            if "values" in source:
                values = source["values"]
                if "detect" in source and len(values) > 1:
                    detects[key] = source["detect"]
                else:
                    detects[key] = None

            # Has no relevance for permutation, just insert the test
            else:
                if "detect" in source:
                    detects[key] = source["detect"]
                elif "default" in source:
                    detects[key] = None

        return detects



    def getFieldSetupClasses(self):
        detects = self.__exportFieldDetects()
        setups = {}

        for fieldName in detects:
            fieldSetup = "jasy.Env.addField(%s);" % self.__exportField(fieldName)
            fieldSetupClass = self.__session.getVirtualItem("jasy.generated.FieldData", jasy.item.Class.ClassItem, fieldSetup, ".js")
            setups[fieldName] = fieldSetupClass

        return setups


    def __exportField(self, field):
        """
        Converts data for the given field into a compact data structure for being used to
        compute a checksum in JavaScript.

        Export structures:
        1. [ name, 1, test, [value1, ...] ]
        2. [ name, 2, value ]
        3. [ name, 3, test, default? ]
        4. [ name, 4, value ] (just data - non permutated - generated internally only)
        """

        source = self.__fields[field]

        content = []
        content.append("'%s'" % field)

        # We have available values to permutate for
        if "values" in source:
            values = source["values"]
            if "detect" in source and len(values) > 1:
                # EXPORT STRUCT 1
                content.append("1")
                content.append(source["detect"])

                if "default" in source:
                    # Make sure that default value is first in
                    values = values[:]
                    values.remove(source["default"])
                    values.insert(0, source["default"])

                content.append(json.dumps(values))

            else:
                # EXPORT STRUCT 2
                content.append("2")

                if "default" in source:
                    content.append(json.dumps(source["default"]))
                else:
                    content.append(json.dumps(values[0]))

        # Has no relevance for permutation, just insert the test
        else:
            if "detect" in source:
                # EXPORT STRUCT 3
                content.append("3")

                # Add detection class
                content.append(source["detect"])

                # Add default value if available
                if "default" in source:
                    content.append(json.dumps(source["default"]))

            elif "default" in source:
                # EXPORT STRUCT 2
                content.append("2")
                content.append(json.dumps(source["default"]))

            else:
                # Has no detection and no permutation. Ignore it completely
                pass

        return "[%s]" % ", ".join(content)



    #
    # State Handling / Looping
    #

    def __generatePermutations(self):
        """
        Combines all values to a set of permutations.
        These define all possible combinations of the configured settings
        """

        fields = self.__fields
        values = {}
        for key in fields:
            if "values" in fields[key]:
                values[key] = fields[key]["values"]
            elif "default" in fields[key] and not "detect" in fields[key]:
                values[key] = [fields[key]["default"]]

        # Thanks to eumiro via http://stackoverflow.com/questions/3873654/combinations-from-dictionary-with-list-values-using-python
        names = sorted(values)
        combinations = [dict(zip(names, prod)) for prod in itertools.product(*(values[name] for name in names))]
        permutations = [Permutation.getPermutation(combi) for combi in combinations]

        return permutations


    def permutate(self):
        """ Generator method for permutations for improving output capabilities """

        Console.info("Processing permutations...")
        Console.indent()

        permutations = self.__generatePermutations()
        length = len(permutations)

        for pos, current in enumerate(permutations):
            Console.info("Permutation %s/%s:" % (pos+1, length))
            Console.indent()

            self.__permutation = current
            self.__translationBundle = self.__session.getTranslationBundle(self.getCurrentLocale())

            yield current
            Console.outdent()

        Console.outdent()

        self.__permutation = None
        self.__translationBundle = None








    def getCurrentOptimization(self):
        return None

    def getCurrentFormatting(self):
        return None




    def setStaticPermutation(self, **argv):
        """
        Sets current permutation to a static permutation which contains all values hardly wired to
        static values using setField() or given via additional named parameters.
        """

        combi = {}

        for name in self.__fields:
            entry = self.__fields[name]
            if not "detect" in entry:
                combi[name] = entry["default"]

        for name in argv:
            combi[name] = argv[name]

        if not combi:
            self.__permutation = None
            return None

        permutation = Permutation.getPermutation(combi)
        self.__permutation = permutation

        return permutation





    def expandFileName(self, fileName):
        """
        Replaces placeholders inside the given filename and returns the result.
        The placeholders are based on the current state of the session.

        These are the currently supported placeholders:

        - {{locale}}: Name of current locale e.g. de_DE
        - {{permutation}}: SHA1 checksum of current permutation
        - {{id}}: SHA1 checksum based on permutation and repository branch/revision
        """

        if "{{destination}}" in fileName:
            fileName = fileName.replace("{{destination}}", self.getDestinationPath())

        if self.__permutation:
            if "{{permutation}}" in fileName:
                fileName = fileName.replace("{{permutation}}", self.__permutation.getChecksum())

            if "{{id}}" in fileName:
                buildId = "%s@%s" % (self.__permutation.getKey(), self.__session.getMain().getRevision())
                buildHash = Util.generateChecksum(buildId)
                fileName = fileName.replace("{{id}}", buildHash)

            if "{{locale}}" in fileName:
                locale = self.__permutation.get("locale")
                fileName = fileName.replace("{{locale}}", locale)

        elif "{{id}}" in fileName:
            fileName = fileName.replace("{{id}}", "none@%s" % (self.getMain().getRevision()))

        return fileName






    def addCommand(self, name, func, restype=None):
        """
        Registers the given function as a new command
        """

        if len(name.split(".")) != 2:
            raise Exception("Command names should always match namespace.name! Tried with: %s!" % name)

        commands = self.__commands

        if name in commands:
            raise Exception("Overwriting commands is not supported! Command=%s" % name)

        commands[name] = {
            "func" : func,
            "restype" : restype
        }


    def executeCommand(self, command, params=None):
        """
        Executes the given command and returns the result
        """

        commands = self.__commands

        # Delegate unknown commands to the Session instance
        if not command in commands:
            return self.__session.executeCommand(command, params)

            raise UserError("Unsupported command %s" % command)

        entry = commands[command]
        restype = entry["restype"]

        if params:
            result = entry["func"](*params)
        else:
            result = entry["func"]()

        return result, restype



    def getId(self):
        id = self.__id
        if id is None:

            all = {
                "parts" : self.__parts,
                "permutation" : str(self.__permutation),
                "data" : self.__data
            }

            serialized = json.dumps(all, sort_keys=True, indent=2, separators=(',', ': '))
            # Console.info("Re-generating ID: %s" % serialized)
            id = self.__id = jasy.core.Util.generateChecksum(serialized)
            Console.info("Re-generated profile ID: %s" % id)

        return id
