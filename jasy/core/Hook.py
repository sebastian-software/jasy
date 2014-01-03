#
# Jasy - Web Tooling Framework
# Copyright 2014 Sebastian Fastner
#

__all__ = ["register", "call"]


class Hooks():
    """
    Simple register/callback hook system
    """

    # Dict of registered hooks
    __hooks = {}

    def register(self, name, callback):
        """Register a callback to be executed at specific execution point with internal states"""

        # If hook name not registered create empty list for hook
        if not name in self.__hooks:
            self.__hooks[name] = []

        # Append hook callback to list
        self.__hooks[name].append(callback)


    def call(self, name, *args):
        """Call registered hook callbacks with given arguments"""

        # List of results
        result = []
        if name in self.__hooks:
            for hook in self.__hooks[name]:
                res = hook(*args)
                if res != None:
                    result.append(res)

            return result
        else:
            return None

# Create global hook registry
hooks = Hooks()

# Exported API
register = hooks.register
call = hooks.call