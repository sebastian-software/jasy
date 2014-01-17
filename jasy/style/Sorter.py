#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import jasy.abstract.Sorter as AbstractSorter

class Sorter(AbstractSorter.AbstractSorter):
    """
    Sorter for Style items
    """

    def __init__(self, resolver):
        super().__init__(resolver)


    def getItemDependencies(self, item):
        return item.getDependencies(self.permutation, items=self.items, warnings=False)


    def getItemBreaks(self, item):
        return item.getBreaks(self.permutation, items=self.items)

