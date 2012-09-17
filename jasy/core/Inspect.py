#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

import types, inspect, textwrap


def highlightArgs(value, inClassOrObject=False):

    argsspec = inspect.getfullargspec(value)     

    if inClassOrObject:
        del argsspec.args[0]

    argmsg = "(%s" % ", ".join(argsspec.args)

    if argsspec.varkw is not None:
        if argsspec.args:
            argmsg += ", "

        argmsg += "..."

    argmsg += ")"

    return Console.colorize(argmsg, "cyan")    


def extractDoc(value, limit=75, indent=2):

    doc = value.__doc__

    if not doc:
        return None

    doc = doc.strip("\n\t ")

    if ". " in doc:
        doc = doc[:doc.index(". ")]

    if ".\n" in doc:
        doc = doc[:doc.index(".\n")]

    doc = doc.replace("\n", " ")
    doc = re.sub(" +", " ", doc)

    doc = doc.strip()

    if len(doc) > limit:
        doc = doc[0:limit] + "..."

    if doc:
        return ":\n%s%s" % (indent * " ", doc)
    else:
        return None


def extractType(value):
    if inspect.isclass(value):
        return "Class"
    elif inspect.ismodule(value):
        return "Module"
    elif type(value) in (types.FunctionType, types.LambdaType):
        return "Function"
    elif isinstance(value, object):
        return "Object"

    return None


def generateApi(api):
    """Returns a stringified output for the given API set"""

    import jasy.env.Task as Task

    result = []

    for key in sorted(api):

        if key.startswith("__"):
            continue

        value = api[key]

        if type(value) is Task.Task:
            continue

        msg = Console.colorize(key, "bold")

        if inspect.isfunction(value):
            msg += Console.colorize(highlightArgs(value), "bold")
        elif inspect.isclass(value):
            msg += Console.colorize(highlightArgs(value.__init__, True), "bold")

        humanType = extractType(value)
        if humanType:
            msg += Console.colorize(" [%s]" % extractType(value), "magenta")

        msg += extractDoc(value) or ""

        result.append(msg)

        if level == 0 and not type(value) in (types.FunctionType, types.LambdaType):

            if inspect.isclass(value):
                sprefix = ""
            elif inspect.ismodule(value) or isinstance(value, object):
                sprefix = "%s." % key
            else:
                sprefix = ""

            smembers = dict(inspect.getmembers(value))

            for skey in sorted(smembers):
                if not "__" in skey:
                    svalue = smembers[skey]
                    if inspect.ismethod(svalue) or inspect.isfunction(svalue):
                        msg = "  - %s%s" % (sprefix, Console.colorize(skey, "bold"))
                        msg += highlightArgs(svalue, humanType in ("Class", "Object"))
                        msg += extractDoc(svalue, indent=6) or ""
                        result.append(msg)

        result.append("")

    return "\n".join(result)    

