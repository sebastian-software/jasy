#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

import jasy.js.Sorter as Sorter
import jasy.core.Console as Console
import jasy.item.Class as Class

__all__ = ["Resolver"]

class Resolver():
    """Resolves dependencies between JavaScript files"""

    def __init__(self, session):
        
        # Keep session reference
        self.__session = session

        # Keep permutation reference
        self.__permutation = session.getCurrentPermutation()

        # Keep fields data locally
        self.__fields = session.getFieldSetupClasses()

        # Required classes by the user
        self.__required = []

        # Hard excluded classes (used for filtering previously included classes etc.)
        self.__excluded = []
        
        # Included classes after dependency calculation
        self.__included = []

        # Collecting all available classes
        self.__classes = {}
        for project in session.getProjects():
            self.__classes.update(project.getClasses())
        

    def addClass(self, classNameOrItem, prepend=False):
        """
        Adds a class by its name or via the ClassItem instance
        """

        if type(classNameOrItem) is str:
            if not classNameOrItem in self.__classes:
                raise Exception("Unknown Class: %s" % classNameOrItem)

            # Replace variable with ClassItem instance
            classNameOrItem = self.__classes[classNameOrItem]

        elif not isinstance(classNameOrItem, Class.ClassItem):
            raise Exception("Invalid class item: %s" % classNameOrItem)

        if prepend:
            self.__required.insert(0, classNameOrItem)
        else:
            self.__required.append(classNameOrItem)
        
        # Invalidate included list
        self.__included = None
        
        return self

        
    def addClassName(self, className):
        """ Adds a class to the initial dependencies """
        
        return self.addClass(className)


    def removeClass(self, classNameOrItem):
        for classObj in self.__required:
            if classObj is classNameOrItem or classObj.getId() == classNameOrItem:
                self.__required.remove(classObj)
                if self.__included:
                    self.__included = []
                return True
                
        return False



    def removeClassName(self, className):
        """ Removes a class name from dependencies """
        
        return self.removeClass(className)


    def excludeClasses(self, classObjects):
        """ Excludes the given class objects (just a hard-exclude which is applied after calculating the current dependencies) """
        
        self.__excluded.extend(classObjects)
        
        # Invalidate included list
        self.__included = None
        
        return self
        

    def addVirtualClass(self, className, text):
        """
        Adds a virtual aka generated class to the resolver with
        the given className and text. 

        Please note: The file name is modified to 
        contain a checksum of the content as a postfix. This keeps
        caches in-tact when using different contents for the same
        file name aka different sets of assets, translations, etc.
        The classname itself (which is modified here as said) is not
        so much of relevance because of the situation that the virtual
        class object is automatically added to the resolver (and sorter).
        """

        classItem = self.__session.getVirtualItem(className, Class.ClassItem, text, ".js")
        return self.addClass(classItem)


    def getRequiredClasses(self):
        """ Returns the user added classes - the so-called required classes. """
        
        return self.__required


    def getIncludedClasses(self):
        """ Returns a final set of classes after resolving dependencies """

        if self.__included:
            return self.__included
                
        collection = set()
        for classObj in self.__required:
            self.__resolveDependencies(classObj, collection)
            
        # Filter excluded classes
        for classObj in self.__excluded:
            if classObj in collection:
                collection.remove(classObj)
        
        self.__included = collection

        return self.__included
        
        
    def getSortedClasses(self):
        """ Returns a list of sorted classes """

        return Sorter.Sorter(self, self.__session).getSortedClasses()


    def __resolveDependencies(self, classObj, collection):
        """ Internal resolver engine which works recursively through all dependencies """
        
        collection.add(classObj)
        dependencies = classObj.getDependencies(self.__permutation, classes=self.__classes, fields=self.__fields)
        
        for depObj in dependencies:
            if not depObj in collection:
                self.__resolveDependencies(depObj, collection)
                    