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

__all__ = ("tokenize", "parse")

import re
import collections
from html.parser import HTMLParser

tagSplitter = r"(\{\{[^\{\}}]*\}\})"
tagMatcher = r"^\{\{\s*([#\^\/\?\!\<\>\$\=_]?)\s*([^\{\}}]*?)\s*\}\}$"


class JasyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.ast = {}
        self.currentAst = self.ast


    def _get_tag_obj(self, tag, attrs, parent):
        htmlattrs = []
        virtualattrs = []
        props = []
        for (key,value) in attrs:
            if key == "class":
                props.append(("className", tokenize(value)))
            elif key == "id":
                props.append(("id", tokenize(value)))
            elif key.startswith("virtual-"):
                virtualattrs.append((key[8:], tokenize(value)))
            else:
                htmlattrs.append((key,tokenize(value)))

        return {
            "html": "%s" % tag,
            "props": props,
            "attrs": htmlattrs,
            "vattrs": virtualattrs,
            "parent": parent
        }

    def handle_starttag(self, tag, attrs):
        if not "children" in self.currentAst:
            self.currentAst["children"] = []
        
        oldCurrent = self.currentAst
        current = self._get_tag_obj(tag, attrs, oldCurrent)

        if tag == "svg" or "svg" in current["parent"]:
            current["svg"] = True

        self.currentAst["children"].append(current)
        self.currentAst = current

    def handle_endtag(self, tag):
        parent = self.currentAst["parent"]
        del self.currentAst["parent"]
        self.currentAst = parent

    def handle_data(self, data):
        if not "children" in self.currentAst:
            self.currentAst["children"] = []

        self.currentAst["children"].extend(tokenize(data))



    def get_code(self, start=None):
        return self.ast["children"]



def buildTree(tokens, stack):
    """
    Processes a list of @tokens {String[]} to create a tree.
    Optional @stack {Array?} is used internally during recursion.
    """

    instructions = []

    while len(tokens) > 0:
        token = tokens.popleft()

        if isinstance(token, str):
            instructions.append(token)
        elif "html" in token:
            instructions.append(token)
            if "children" in token:
                token["children"] = buildTree(collections.deque(token["children"]), collections.deque())
        elif token["tag"] == "#" or token["tag"] == "^" or token["tag"] == "?":
            stack.append(token)
            token["nodes"] = buildTree(tokens, stack)
            instructions.append(token)
        elif token["tag"] == "/":
            opener = stack.pop()
            return instructions
        else:
            instructions.append(token)

    return instructions


def tokenize(text, nostrip=False):
    """
    Tokenizer for template @text {String}. Returns an array of tokens
    where tags are returned as an object with the keys `tag` and `name` while
    normal strings are kept as strings.

    Optionally you can keep white spaces (line breaks,
    leading, trailing, etc.) by enabling @nostrip {Boolean?false}.
    """

    if not nostrip:
        text = "".join([line.strip() for line in text.split("\n")])

    tokens = []
    splitted = re.split(tagSplitter, text)

    for segment in splitted:
        if len(segment) > 0:
            if segment[0] == "{":
                matched = re.match(tagMatcher, segment)
                if matched:
                    tag = matched.group(1)  # || "$"
                    if not tag:
                        tag = "$"
                    if tag != "!":
                        tokens.append({
                            "tag": tag,
                            "name": matched.group(2)
                        })

                elif segment != "":
                    tokens.append(segment)
            elif segment != "":
                tokens.append(segment)

    return tokens



def parse(text, nostrip=False):
    """
    Returns the token tree of the given template @text {String}.

    A token holds the following information:

    - `tag`: tag of the token
    - `name`: name of the token
    - `nodes`: children of the node

    Optionally you can keep white spaces (line breaks,
    leading, trailing, etc.) by enabling @nostrip {Boolean?false}.
    """

    #return buildTree(collections.deque(tokenize(text, nostrip)), collections.deque())
    if not nostrip:
        text = "".join([line.strip() for line in text.split("\n")])
    parser = JasyHTMLParser()
    parser.feed(text)
    return buildTree(collections.deque(parser.get_code()), collections.deque())
