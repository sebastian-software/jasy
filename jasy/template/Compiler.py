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

__all__ = ["compile"]

import Parser

accessTags = [
    "#",      # go into section / loop start
    "?",      # if / has
    "^",       # if not / has not
    "$",       # insert variable
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


def walk(node, labels, nostrip):
    code = ""

    for current in node:
        if type(current) == str:
            code += 'buf+="' + escapeMatcher(current) + '";'
        elif current["tag"] == "\n":
            code += 'buf+="\\n";'
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
                    code += 'if(this._has(' + accessorCode + ')){' + innerCode + '}'
                elif tag == "^":
                    code += 'if(!this._has(' + accessorCode + ')){' + innerCode + '}'
                elif tag == "#":
                    code += 'this._section(' + accessorCode + ',partials,labels,function(data,partials,labels){' + innerCode + '});'
                elif tag == "=":
                    code += 'buf+=this._data(' + accessorCode + ');'
                elif tag == "$":
                    code += 'buf+=this._variable(' + accessorCode + ');';

            elif tag == ">":
                code += 'buf+=this._partial("' + escaped + '",data,partials,labels);'
            elif tag == "_":
                if labels and escaped in labels:
                    code += walk(Parser.parse(labels[escaped], True), labels);
                else:
                    code += 'buf+=this._label("' + escaped + '",data,partials,labels);'

    return code


def compile(text, labels=[], nostrip=False, name=None):
    tree = Parser.parse(text, nostrip)
    wrapped = escapeContent('var buf="";' + walk(tree, labels, nostrip) + 'return buf;');

    if name:
        name = escapeContent("\"%s\"" % name)
    else:
        name = "null"

    text = escapeContent(text)

    return "new core.template.Template(new Function('data', 'partials', 'labels', \"%s\"), \"%s\", %s);" % (wrapped, text, name)
