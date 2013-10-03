#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.abstract.Sorter as AbstractSorter

class Sorter(AbstractSorter.AbstractSorter):
    
    def __init__(self, resolver, session):
        super().__init__(resolver, session)


    def getItemDependencies(self, item):
        return item.getDependencies(self.permutation, classes=self.names, warnings=False)


    def getItemBreaks(self, item):
        return item.getBreaks(self.permutation, classes=self.names)

