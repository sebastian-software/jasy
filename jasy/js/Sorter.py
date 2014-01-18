#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import jasy.abstract.Sorter as AbstractSorter

class Sorter(AbstractSorter.AbstractSorter):
    """
    Sorter for Script items
    """

    def __init__(self, resolver):
        super().__init__(resolver)

        self.fields = self.profile.getFieldSetupClasses()


    def getItemDependencies(self, item):
        return item.getDependencies(self.permutation, items=self.items, fields=self.fields, warnings=False)


    def getItemBreaks(self, item):
        return item.getBreaks(self.permutation, items=self.items)

