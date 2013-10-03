#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.style.Sorter as Sorter
import jasy.core.Console as Console
import jasy.item.Style as Style

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
        self.__styles = {}
        for project in session.getProjects():
            self.__styles.update(project.getStyles())


    def add(self, styleNameOrItem, prepend=False):
        """
        Adds a style by its name or via the Style item instance
        """

        if type(styleNameOrItem) is str:
            if not styleNameOrItem in self.__styles:
                raise Exception("Unknown Style: %s" % styleNameOrItem)

            # Replace variable with StyleItem instance
            styleNameOrItem = self.__styles[styleNameOrItem]

        elif not isinstance(styleNameOrItem, Style.StyleItem):
            raise Exception("Invalid style item: %s" % styleNameOrItem)

        if prepend:
            self.__required.insert(0, styleNameOrItem)
        else:
            self.__required.append(styleNameOrItem)
        
        # Invalidate included list
        self.__included = None
        
        return self

