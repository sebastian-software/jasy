#
# Jasy - Web Tooling Framework
# Copyright 2013-2014 Sebastian Werner
#

import jasy.core.FlagSet as FlagSet

class Formatting(FlagSet.FlagSet):
    """
    Configures an formatting object which can be used to compress classes afterwards.
    The optimization set is frozen after initialization which also generates the unique
    key based on the given formatting options.
    """
