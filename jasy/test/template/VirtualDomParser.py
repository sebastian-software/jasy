#!/usr/bin/env python3

import sys
import os
import unittest
import logging
import inspect

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.template.virtualdom.Parser as Parser

"""
SUPPORTS

h1{

  &:first-child{
    font-weight: bold;
  }

  .cssshadow &{
    text-shadow: 1px;
  }

  header &:first-child{
    color: red;
  }

}

"""


class Tests(unittest.TestCase):
    def process(self, code):
        #callerName = inspect.stack()[1][3][5:]

        return Parser.parse(code)

    def test_div(self):
        tree = self.process('''
            <div>test</div>
        ''')
        
        self.assertEqual(tree[0]["tag"] == "div")