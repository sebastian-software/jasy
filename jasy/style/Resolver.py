#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import jasy.abstract.Resolver as AbstractResolver
import jasy.item.Style as Style
import jasy.style.Sorter as Sorter


class Resolver(AbstractResolver.Resolver):

    def __init__(self, profile):
        super().__init__(profile)

        for project in profile.getProjects():
            self.items.update(project.getStyles())


    def getItemDependencies(self, item):
        return item.getDependencies(self.permutation, items=self.items)


    def getSorted(self):
        """ Returns a list of sorted classes """

        return Sorter.Sorter(self).getSorted()

