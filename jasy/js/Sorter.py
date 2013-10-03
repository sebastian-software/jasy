#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013 Sebastian Werner
#

import jasy.abstract.Sorter as AbstractSorter

class Sorter(AbstractSorter.AbstractSorter):
    
    def __init__(self, resolver, session):
        super().__init__(resolver, session)

        self.fields = session.getFieldSetupClasses()


    def getItemDependencies(self, item):
        return item.getDependencies(self.permutation, classes=self.names, fields=self.fields, warnings=False)


    def getItemBreaks(self, item):
        return item.getBreaks(self.permutation, classes=self.names)

