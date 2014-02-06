#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import polib, json, os

import jasy.item.Abstract as AbstractItem
import jasy.core.Console as Console


def generateMessageId(basic, plural=None, context=None):
    """
    Returns a unique message ID based on info typically stored in the code: id, plural, context
    """

    result = basic

    if context is not None:
        result += "[C:%s]" % context
    elif plural:
        result += "[N:%s]" % plural

    return result


class TranslationItem(AbstractItem.AbstractItem):

    kind = "jasy.Translation"

    def __add__(self, other):

        self.table.update(other.getTable())
        return self


    def __init__(self, project, id=None, package=None, table=None):

        # Call AbstractItem's init method first
        super().__init__(project, id, package)

        # Initialize translation table
        self.table = table or {}


    def setId(self, id):

        # Overridden to set the language based on the fileId automatically
        super().setId(id)

        # Extract language from file ID
        # Thinking of that all files are named like de.po, de.txt, de.properties, etc.
        lang = self.id
        if "." in lang:
            lang = lang[lang.rfind(".")+1:]

        self.language = lang


    def generateId(self, relpath, package):
        """
        Generates the fileId of this item as being used by other modules
        """

        if package:
            fileId = "%s/" % package
        else:
            fileId = ""

        return (fileId + os.path.splitext(relpath)[0]).replace("/", ".")


    def attach(self, path):

        # Call AbstractItem's attach method first
        super().attach(path)

        Console.debug("Loading translation file: %s", path)
        Console.indent()

        # Flat data strucuture where the keys are unique
        table = {}
        path = self.getPath()

        # Decide infrastructure/parser to use based on file name
        po = polib.pofile(path)
        Console.debug("Translated messages: %s=%s%%", self.language, po.percent_translated())

        for entry in po.translated_entries():
            entryId = generateMessageId(entry.msgid, entry.msgid_plural, entry.msgctxt)
            if not entryId in table:
                if entry.msgstr != "":
                    table[entryId] = entry.msgstr
                elif entry.msgstr_plural:
                    # This field contains all different plural cases (type=dict)
                    table[entryId] = entry.msgstr_plural

        Console.debug("Translation of %s entries ready" % len(table))
        Console.outdent()

        self.table = table

        return self


    def export(self, classes, formatted=True):
        """
        Exports the translation table as JSON based on the given set of classes
        """

        # Based on the given class list figure out which translations are actually used
        relevantTranslations = set()
        for classObj in classes:
            classTranslations = classObj.getTranslations()
            if classTranslations:
                relevantTranslations.update(classTranslations)

        # Produce new table which is filtered by relevant translations
        table = self.table
        result = { translationId: table[translationId] for translationId in relevantTranslations if translationId in table }

        if result:
            if formatted:
                return json.dumps(result, indent=2, sort_keys=True)
            else:
                return json.dumps(result, sort_keys=True)


    def getTable(self):
        """
        Returns the translation table
        """

        return self.table


    def getLanguage(self):
        """
        Returns the language of the translation file
        """

        return self.language

