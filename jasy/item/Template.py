#
# Jasy - Web Tooling Framework
# Copyright 2014 Sebastian Werner
#

import os

from jasy import UserError

import jasy.core.Console as Console
import jasy.item.Abstract as AbstractItem
import jasy.item.Script as ScriptItem
import jasy.template.Compiler as Compiler


def templateFilter(text, item):
    Console.info("Creating template class %s", item.getId())
    return 'core.Main.declareNamespace("%(name)s", %(content)s);' % {
        "name": item.getId(),
        "content" : Compiler.compile(text)
    }


def escapeContent(content):
    return content.replace("\"", "\\\"").replace("\n", "\\n")


class TemplateItem(AbstractItem.AbstractItem):

    kind = "jasy.Template"

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
        result = super().attach(path)

        # Force adding an matching class item to the registry
        self.getScriptItem()

        return result


    def getScriptItem(self):
        """
        Returns a class representation for the template instance
        """

        classId = self.getId() + "Template"

        session = self.project.getSession()
        virtualProject = session.getVirtualProject()
        scriptItem = virtualProject.getItem("jasy.Script", classId)

        if scriptItem is None:
            scriptItem = ScriptItem.ScriptItem(virtualProject, classId)
            scriptItem.setTextFilter(templateFilter)
            scriptItem.setPath(session.getVirtualFilePathFromId(classId, ".js"))

            virtualProject.addItem("jasy.Script", scriptItem)

        # Be sure that class item is up-to-date
        if scriptItem.mtime != self.mtime:
            scriptItem.mtime = self.mtime
            scriptItem.setText(self.getText())

        return scriptItem
