#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import jasy.core.Console as Console
import jasy.item.Abstract as AbstractItem

class ResolverError(Exception):
    """
    Error which is throws when resolving items could be be finished because of
    items which could not be found or are of an unexpected type.
    """

    pass


class Resolver():
    """
    Resolves dependencies between items.
    This class is not type depended e.g. is used for both scripts and styles.
    """

    def __init__(self, profile):

        # Keep profile reference
        self.profile = profile

        # Keep permutation reference
        self.permutation = profile.getCurrentPermutation()

        # Collecting all available items
        self.items = {}

        # Required classes by the user
        self.__required = []

        # Hard excluded classes (used for filtering previously included classes etc.)
        self.__excluded = []

        # Included classes after dependency calculation
        self.__included = []


    def add(self, nameOrItem, prepend=False):
        """
        Adds an item by its name or via the item instance
        """

        if type(nameOrItem) is str:
            if not nameOrItem in self.items:
                raise ResolverError("Unknown item: %s" % nameOrItem)

            # Replace variable with item instance
            nameOrItem = self.items[nameOrItem]

        elif not isinstance(nameOrItem, AbstractItem.AbstractItem):
            raise ResolverError("Invalid item: %s" % nameOrItem)

        if prepend:
            self.__required.insert(0, nameOrItem)
        else:
            self.__required.append(nameOrItem)

        # Invalidate included list
        self.__included = None

        return self


    def remove(self, nameOrItem):
        """
        Removes an item via its name or via the item instance
        """

        for item in self.__required:
            if item is nameOrItem or item.getId() == nameOrItem:
                self.__required.remove(item)
                if self.__included:
                    self.__included = []
                return True

        return False


    def exclude(self, items):
        """
        Excludes the given items (just a hard-exclude which is
        applied after calculating the current dependencies)
        """

        self.__excluded.extend(items)

        # Invalidate included list
        self.__included = None

        return self


    def getRequired(self):
        """ Returns the user added classes - the so-called required classes. """

        return self.__required


    def getIncluded(self):
        """ Returns a final set of classes after resolving dependencies """

        if self.__included:
            return self.__included

        collection = set()
        for item in self.__required:
            self.__resolveDependencies(item, collection)

        # Filter excluded classes
        for item in self.__excluded:
            if item in collection:
                collection.remove(item)

        self.__included = collection

        return self.__included


    def __resolveDependencies(self, item, collection):
        """ Internal resolver engine which works recursively through all dependencies """

        collection.add(item)
        dependencies = self.getItemDependencies(item)

        for depObj in dependencies:
            if not depObj in collection:
                self.__resolveDependencies(depObj, collection)


