#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

import jasy.core.FlagSet as FlagSet

import jasy.js.optimize.CryptPrivates as CryptPrivates
import jasy.js.optimize.BlockReducer as BlockReducer
import jasy.js.optimize.LocalVariables as LocalVariables
import jasy.js.optimize.CombineDeclarations as CombineDeclarations
import jasy.js.optimize.ClosureWrapper as ClosureWrapper


class Error(Exception):
    """
    Error object which is raised whenever an optimization could not be applied correctly.
    """

    def __init__(self, msg):
        self.__msg = msg

    def __str__(self):
        return "Error during optimization! %s" % (self.__msg)



class Optimization(FlagSet.FlagSet):
    """
    Configures an optimization object which can be used to compress classes afterwards.
    The optimization set is frozen after initialization which also generates the unique
    key based on the given optimizations.
    """

    def apply(self, tree):
        """
        Applies the configured optimizations to the given node tree. Modifies the tree in-place
        to be sure to have a deep copy if you need the original one. It raises an error instance
        whenever any optimization could not be applied to the given tree.
        """

        if self.has("wrap"):
            try:
                ClosureWrapper.optimize(tree)
            except CryptPrivates.Error as err:
                raise Error(err)

        if self.has("declarations"):
            try:
                CombineDeclarations.optimize(tree)
            except CombineDeclarations.Error as err:
                raise Error(err)

        if self.has("blocks"):
            try:
                BlockReducer.optimize(tree)
            except BlockReducer.Error as err:
                raise Error(err)

        if self.has("variables"):
            try:
                LocalVariables.optimize(tree)
            except LocalVariables.Error as err:
                raise Error(err)

        if self.has("privates"):
            try:
                CryptPrivates.optimize(tree, tree.fileId)
            except CryptPrivates.Error as err:
                raise Error(err)
