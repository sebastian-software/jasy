#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

import os, shutil, json
import jasy.core.Console as Console


class FileManager:
    """
    Summarizes utility methods for operations in filesystem.
    """

    def __init__(self, profile=None):

        self.__profile = profile


    def removeDir(self, dirname):
        """Removes the given directory"""

        if self.__profile:
            dirname = self.__profile.expandFileName(dirname)

        if os.path.exists(dirname):
            Console.info("Deleting folder %s" % dirname)
            shutil.rmtree(dirname)


    def removeFile(self, filename):
        """Removes the given file"""

        if self.__profile:
            filename = self.__profile.expandFileName(filename)

        if os.path.exists(filename):
            Console.info("Deleting file %s" % filename)
            os.remove(filename)


    def makeDir(self, dirname):
        """Creates missing hierarchy levels for given directory"""

        if dirname == "":
            return

        if self.__profile:
            dirname = self.__profile.expandFileName(dirname)

        if not os.path.exists(dirname):
            os.makedirs(dirname)


    def copyDir(self, src, dst):
        """
        Copies a directory to a destination directory.
        Merges the existing directory structure with the folder to copy.
        """

        if self.__profile:
            dst = self.__profile.expandFileName(dst)

        srcLength = len(src)
        counter = 0

        visitedPaths = []

        for rootFolder, dirs, files in os.walk(src,followlinks=True):
            
            # Prevent infinite loops by removing already visited subdirs
            # This only happens by using recursive links
            subdirs = dirs[:]
            for subdir in subdirs:
                realPath = os.path.realpath(os.path.join(rootFolder, subdir))
                if realPath in visitedPaths:
                    dirs.remove(subdir)
                else:
                    visitedPaths.append(realPath)

            # figure out where we're going
            destFolder = dst + rootFolder[srcLength:]

            # loop through all files in the directory
            for fileName in files:

                # compute current (old) & new file locations
                srcFile = os.path.join(rootFolder, fileName)
                dstFile = os.path.join(destFolder, fileName)

                if self.updateFile(srcFile, dstFile):
                    counter += 1

        return counter


    def copyFile(self, src, dst):
        """Copy src file to dst file. Both should be filenames, not directories."""

        if not os.path.isfile(src):
            raise Exception("No such file: %s" % src)

        if self.__profile:
            dst = self.__profile.expandFileName(dst)

        # First test for existance of destination directory
        self.makeDir(os.path.dirname(dst))

        # Finally copy file to directory
        try:
            shutil.copy2(src, dst)
        except IOError as ex:
            Console.error("Could not write file %s: %s" % (dst, ex))

        return True


    def updateFile(self, src, dst):
        """Same as copyFile() but only do copying when source file is newer than target file"""

        if not os.path.isfile(src):
            raise Exception("No such file: %s" % src)

        if self.__profile:
            dst = self.__profile.expandFileName(dst)

        try:
            dst_mtime = os.path.getmtime(dst)
            src_mtime = os.path.getmtime(src)

            # Only accecpt equal modification time as equal as copyFile()
            # syncs over the mtime from the source.
            if src_mtime == dst_mtime:
                return False

        except OSError:
            # destination file does not exist, so mtime check fails
            pass

        return self.copyFile(src, dst)


    def writeFile(self, dst, content):
        """Writes the content to the destination file name"""

        if self.__profile:
            dst = self.__profile.expandFileName(dst)

        # First test for existance of destination directory
        self.makeDir(os.path.dirname(dst))

        # Open file handle and write
        handle = open(dst, mode="w", encoding="utf-8")
        handle.write(content)
        handle.close()

