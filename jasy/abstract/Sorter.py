#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import jasy.core.Console as Console

class SorterError(Exception):
    """
    Error which is throws when sorting could not be done because of circular dependencies.
    """

    pass


class AbstractSorter:
    """
    Sorts a final list of items according to their requirements.
    This class is not type depended e.g. is used for both scripts and styles.
    """

    def __init__(self, resolver):

        # Shorthand references
        self.resolver = resolver
        self.profile = resolver.profile
        self.permutation = resolver.permutation

        # Build item name dict (id => item)
        items = self.resolver.getIncluded()
        self.items = dict([(item.getId(), item) for item in items])

        # Initialize fields
        self.__loadDeps = {}
        self.__circularDeps = {}
        self.__sorted = []


    def getSorted(self):
        """
        Returns the sorted item list (caches result)
        """

        if not self.__sorted:
            Console.debug("Sorting items...")
            Console.indent()

            for itemId in self.items:
                self.__getLoadDeps(self.items[itemId])

            result = []
            required = self.resolver.getRequired()
            for item in required:
                if not item in result:
                    # Console.debug("Start adding with: %s", item)
                    self.__addSorted(item, result)

            Console.outdent()
            self.__sorted = result

        return self.__sorted


    def __addSorted(self, item, result, postponed=False):
        """
        Adds a single item and its dependencies to the sorted result list
        """

        loadDeps = self.__getLoadDeps(item)

        for depObj in loadDeps:
            if not depObj in result:
                self.__addSorted(depObj, result)

        if item in result:
            return

        # Console.debug("Adding item: %s", item)
        result.append(item)

        # Insert circular dependencies as soon as possible
        if item in self.__circularDeps:
            circularDeps = self.__circularDeps[item]
            for depObj in circularDeps:
                if not depObj in result:
                    self.__addSorted(depObj, result, True)


    def __getLoadDeps(self, item):
        """
        Returns load time dependencies of given item
        """

        if not item in self.__loadDeps:
            self.__getLoadDepsRecurser(item, [])

        return self.__loadDeps[item]


    def __getLoadDepsRecurser(self, item, stack):
        """
        This is the main routine which tries to control over a system
        of unsorted items. It directly tries to fullfil every dependency
        a item have, but has some kind of exception based loop protection
        to prevent circular dependencies from breaking the build.

        It respects break information given by file specific meta data, but
        also adds custom hints where it found recursions. This lead to a valid
        sort, but might lead to problems between exeactly the two affected items.
        Without doing an exact execution it's not possible to whether found out
        which of two each-other referencing items needs to be loaded first.
        This is basically only interesting in cases where one item needs another
        during the definition phase which is not the case that often.
        """

        if item in stack:
            stack.append(item)
            msg = " >> ".join([x.getId() for x in stack[stack.index(item):]])
            raise SorterError("Circular Dependency: %s" % msg)

        stack.append(item)

        itemDeps = self.getItemDependencies(item)
        itemBreaks = self.getItemBreaks(item)

        result = set()
        circular = set()

        # Respect manually defined breaks
        # Breaks are dependencies which are down-priorized to break
        # circular dependencies between items.
        for breakObj in itemBreaks:
            if breakObj.getId() in self.items:
                circular.add(breakObj)

        # Now process the deps of the given item
        loadDeps = self.__loadDeps
        for depObj in itemDeps:
            if depObj is item:
                continue

            depName = depObj.getId()

            if depObj in itemBreaks:
                Console.debug("Manual Break: %s => %s" % (item, depObj))
                pass

            elif depObj in loadDeps:
                result.update(loadDeps[depObj])
                result.add(depObj)

            else:
                current = self.__getLoadDepsRecurser(depObj, stack[:])

                result.update(current)
                result.add(depObj)

        # Sort dependencies by number of other dependencies
        # For performance reasions we access the __loadDeps
        # dict directly as this data is already stored
        result = sorted(result, key=lambda depObj: len(self.__loadDeps[depObj]))

        loadDeps[item] = result

        if circular:
            self.__circularDeps[item] = circular

        return result
