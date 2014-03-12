#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import jasy.abstract.Resolver as AbstractResolver
import jasy.item.Script as ScriptItem
import jasy.script.Sorter as Sorter


class Resolver(AbstractResolver.Resolver):

    def __init__(self, profile):
        super().__init__(profile)

        self.fields = profile.getFieldSetupScripts()

        for project in profile.getProjects():
            self.items.update(project.getScripts())


    def getItemDependencies(self, item):
        return item.getDependencies(self.permutation, items=self.items, fields=self.fields)


    def getSorted(self):
        """ Returns a list of sorted classes """

        return Sorter.Sorter(self).getSorted()


    def addVirtual(self, name, text):
        """
        Adds a virtual aka generated class to the resolver with
        the given name and text.

        Please note: The file name is modified to
        contain a checksum of the content as a postfix. This keeps
        caches in-tact when using different contents for the same
        file name aka different sets of assets, translations, etc.
        The classname itself (which is modified here as said) is not
        so much of relevance because of the situation that the virtual
        class object is automatically added to the resolver (and sorter).
        """

        ScriptItem = self.profile.getVirtualItem(name, ScriptItem.ScriptItem, text, ".js")
        return self.add(ScriptItem)
