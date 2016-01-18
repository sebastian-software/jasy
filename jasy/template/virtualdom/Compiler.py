#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Fastner
#
# Based upon
# Core - JavaScript Foundation
# Copyright 2010-2012 Zynga Inc.
# Copyright 2012-2014 Sebastian Werner
#
# Based upon
# Hogan.JS by Twitter, Inc.
# https://github.com/twitter/hogan.js
# Licensed under the Apache License, Version 2.0
#

__all__ = ("compile")

import jasy.template.virtualdom.Parser as Parser
import json

accessTags = [
    "#",     # go into section / loop start
    "?",     # if / has
    "^",     # if not / has not
    "$",     # insert variable
    "="      # insert raw / non escaped
]

# Tags which support children
innerTags = [
    "#",
    "?",
    "^"
]


def escapeContent(content):
    return content.replace("\"", "\\\"").replace("\n", "\\n")


def escapeMatcher(str):
    return str.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\\n").replace("\r", "\\\r")


def flattenProperties(obj):
    code = []

    for key in obj:
        current = obj[key]
        if (isinstance(current, str)):
            code.append("'%s':%s" % (key, current))
        else:
            code.append("'%s':%s" % (key, flattenProperties(current)))

    return "{%s}" % ",".join(code)


def walk(node, labels, nostrip):
    code = []

    for current in node:
        if isinstance(current,str):
            code.append("'%s'" % escapeMatcher(current))
        elif "html" in current:
            children = ""
            if "children" in current:
                children = ",[%s]" % walk(current["children"], labels, nostrip)

            properties = {}
            for (key, value) in current["props"]:
                parsedValue = walk(value, labels, nostrip)
                if "," in parsedValue:
                    properties[key] = "[{}].join('')".format(parsedValue)
                else:
                    properties[key] = parsedValue

            if len(current["attrs"]) > 0:
                if not "attributes" in properties:
                    properties["attributes"] = {}

                for (key, value) in current["attrs"]:
                    properties["attributes"][key] = walk(value, labels, nostrip)

            if len(current["vattrs"]) > 0:
                if not "virtualAttributes" in properties:
                    properties["virtualAttributes"] = {}

                for (key, value) in current["vattrs"]:
                    properties["virtualAttributes"][key] = walk(value, labels, nostrip)

            if "svg" in current:
                code.append("hsvg('%(tag)s', %(props)s%(children)s)" % {
                    "tag": current["html"],
                    "props": flattenProperties(properties),
                    "children": children
                })
            else:
                code.append("h('%(tag)s', %(props)s%(children)s)" % {
                    "tag": current["html"],
                    "props": flattenProperties(properties),
                    "children": children
                })
        elif False and current["tag"] == "\n":
            #code += 'buf+="\\n";\n'
            pass
        else:
            tag = current["tag"]
            name = current["name"]
            escaped = escapeMatcher(name)

            if tag in accessTags:
                if name == ".":
                    accessor = 2
                elif "." in name:
                    accessor = 1
                else:
                    accessor = 0

                accessorCode = '"' + escaped + '",' + str(accessor) + ',data'

                if tag in innerTags:
                    innerCode = walk(current["nodes"], labels, nostrip)

                if tag == "?":
                    code.append('this._has(' + accessorCode + ')?[' + innerCode + ']:""')
                elif tag == "^":
                    code.append( 'this._has(' + accessorCode + ')?"":[' + innerCode + ']' )
                elif tag == "#":
                    code.append( 'this._section(' + accessorCode + ',partials,labels,function(data,partials,labels){\nreturn [' + innerCode + '];\n})' )
                elif tag == "=":
                    code.append( 'this._data(' + accessorCode + ')' )
                elif tag == "$":
                    code.append( 'this._variable(' + accessorCode + ')' )

            elif tag == ">":
                code.append( 'this._partial("' + escaped + '",data,partials,labels)' )
            elif tag == "_":
                if labels and escaped in labels:
                    code.append( walk(Parser.parse(labels[escaped], True), labels) )
                else:
                    code.append( 'this._label("' + escaped + '",data,partials,labels)' )

    return ",".join(code)


def compile(text, labels=[], nostrip=False, name=None):
    tree = Parser.parse(text, nostrip)
    wrapped = 'var h=core.vdom.HyperScript.h;var hsvg=core.vdom.HyperScript.svg;return core.Array.flatten([' + walk(tree, labels, nostrip) + ']);'
    
    if name is None:
        name = "null"

    return "new core.template.Template(function(data, partials, labels){%s}, null, %s)" % (wrapped, name)
