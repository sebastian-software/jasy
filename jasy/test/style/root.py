#!/usr/bin/env python3

import sys, os, unittest, logging, inspect

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.style.Engine as Engine

"""
SUPPORTS

h1{
  font-size: 20px;

  @root html.desktop &{
    font-size: 30px;
  }
}

"""

class Tests(unittest.TestCase):

    def process(self, code):
        callerName = inspect.stack()[1][3][5:]

        tree = Engine.getTree(code, callerName)
        tree = Engine.reduceTree(tree)
        return Engine.compressTree(tree)


    def test_basic(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            @root .bar {
              color: gray;
            }
          }
        '''), '.foo{color:red;}.bar{color:gray;}')


    def test_deep(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            @root .bar {
              .baz{
                color: gray;
              }
            }
          }
        '''), '.foo{color:red;}.bar .baz{color:gray;}')


    def test_parentreference_append(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            @root .bar & {
              color: gray;
            }
          }
        '''), '.foo{color:red;}.bar .foo{color:gray;}')


    def test_parentreference_inline_inner(self):
        self.assertEqual(self.process('''
          .date{
            color: black;
            background: white;

            @root{
              &__dialog{
                position: absolute;
              }
            }
          }
        '''), '.date{color:black;background:white;}.date__dialog{position:absolute;}')


    def test_parentreference_inline(self):
        self.assertEqual(self.process('''
          .date{
            color: black;
            background: white;

            @root &__dialog{
              position: absolute;
            }
          }
        '''), '.date{color:black;background:white;}.date__dialog{position:absolute;}')



if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

