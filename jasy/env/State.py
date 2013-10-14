#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

"""This module is used to pass a single session instance around to different modules"""

import jasy.core.Session as Session
import jasy.core.Profile as Profile

__all__ = ["session", "profile"]

session = Session.Session()
session.__doc__ = """Auto initialized session object based on jasy.core.Session"""

profile = Profile.Profile(session)
profile.__doc__ = """Auto initialized profile object based on jasy.core.Profile"""
