#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

import os

from jasy import UserError
import jasy.core.File as File

class AbstractItem:

    id = None
    project = None
    kind = "item"
    mtime = None

    __path = None
    __cache = None
    __text = None

    def __init__(self, project, id=None):
        self.id = id
        self.project = project

    def attach(self, path):
        self.__path = path

        entry = None

        try:
            if type(path) is list:
                mtime = 0
                for entry in path:
                    entryTime = os.stat(entry).st_mtime
                    if entryTime > mtime:
                        mtime = entryTime

                self.mtime = mtime

            else:
                entry = path
                self.mtime = os.stat(entry).st_mtime

        except OSError as oserr:
            raise UserError("Invalid item path: %s" % entry)

        return self

    def getId(self):
        """Returns a unique identify of the class. Typically as it is stored inside the project."""
        return self.id

    def setId(self, id):
        self.id = id
        return self

    def getProject(self):
        """Returns the project which the class belongs to"""
        return self.project

    def getPath(self):
        """Returns the exact position of the class file in the file system."""
        return self.__path

    def getModificationTime(self):
        """Returns last modification time of the class"""
        return self.mtime

    def setText(self, text):
        """Stores text from custom reader"""
        self.__text = text


    def saveText(self, text, path, encoding="utf-8"):
        """
        Saves the given text under the given path and stores both for future access

        This is mainly useful for "virtual" files which are not edited by the developer
        but which are created dynamically during runtime.
        """

        self.__text = text
        self.__path = path

        if not File.exists(path) or File.read(path) != text:
            File.write(path, text)

        self.mtime = os.stat(path).st_mtime


    def getText(self, encoding="utf-8"):
        """Reads the file (as UTF-8) and returns the text"""

        if self.__text is not None:
            return self.__text

        if self.__path is None:
            return None

        if type(self.__path) == list:
            return "".join([open(filename, mode="r", encoding=encoding).read() for filename in self.__path])
        else:
            return open(self.__path, mode="r", encoding=encoding).read()

    def getChecksum(self, mode="rb"):
        """Returns the SHA1 checksum of the item"""

        return File.sha1(open(self.getPath(), mode))


    # Map Python built-ins
    __repr__ = getId
    __str__ = getId

