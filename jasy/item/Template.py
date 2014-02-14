#
# Jasy - Web Tooling Framework
# Copyright 2014 Sebastian Werner
#

import os

from jasy import UserError

import jasy.core.Console as Console
import jasy.item.Abstract as AbstractItem
import jasy.item.Class as ClassItem
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
        self.getClassItem()

        return result


    def getClassItem(self):
        """
        Returns a class representation for the template instance
        """

        classId = self.getId() + "Template"

        session = self.project.getSession()
        virtualProject = session.getVirtualProject()
        classItem = virtualProject.getItem("jasy.Class", classId)

        if classItem is None:
            classItem = ClassItem.ClassItem(virtualProject, classId)
            classItem.setTextFilter(templateFilter)
            classItem.setPath(session.getVirtualFilePathFromId(classId, ".js"))

            virtualProject.addItem("jasy.Class", classItem)

        # Be sure that class item is up-to-date
        if classItem.mtime != self.mtime:
            classItem.mtime = self.mtime
            classItem.setText(self.getText())

        return classItem
