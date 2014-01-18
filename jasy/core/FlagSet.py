#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

class FlagSet:
    """
    Configures an formatting object which can be used to compress classes afterwards.
    The optimization set is frozen after initialization which also generates the unique
    key based on the given formatting options.
    """

    __key = None


    def __init__(self, *args):
        self.__data = set()

        for identifier in args:
            self.__data.add(identifier)

        self.__key = "+".join(sorted(self.__data))


    def has(self, key):
        """
        Whether the given formatting is enabled.
        """

        return key in self.__data


    def enable(self, flag):
        self.__data.add(flag)
        self.__key = None


    def disable(self, flag):
        self.__data.remove(flag)
        self.__key = None


    def getKey(self):
        """
        Returns a unique key to identify this formatting set
        """

        if self.__key is None:
            self.__key = "+".join(sorted(self.__data))

        return self.__key


    # Map Python built-ins
    __repr__ = getKey
    __str__ = getKey


