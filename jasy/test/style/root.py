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
              .deeper{
                color: gray;
              }
            }
          }
        '''), '.foo{color:red;}.bar .deeper{color:gray;}')


    def test_deep_multidist(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            @root .bar, .baz {
              .deeper{
                color: gray;
              }
            }
          }
        '''), '.foo{color:red;}.bar .deeper,.baz .deeper{color:gray;}')


    def test_parentreference_append(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            @root .bar & {
              color: gray;
            }
          }
        '''), '.foo{color:red;}.bar .foo{color:gray;}')


    def test_parentreference_append_multiroot(self):
        self.assertEqual(self.process('''
          .foo,
          h1 .innerfoo {
            color: red;

            @root .bar & {
              color: gray;
            }
          }
        '''), '.foo,h1 .innerfoo{color:red;}.bar .foo,.bar h1 .innerfoo{color:gray;}')


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


    def test_parentreference_inline_multiroot(self):
        self.assertEqual(self.process('''
          .date,
          .color{
            color: black;
            background: white;

            @root &__dialog{
              position: absolute;
            }
          }
        '''), '.date,.color{color:black;background:white;}.date__dialog,.color__dialog{position:absolute;}')


    def test_parentreference_inline_multiroot_multidist(self):
        self.assertEqual(self.process('''
          .date,
          .color{
            color: black;
            background: white;

            @root &__dialog, &__overlay{
              position: absolute;
            }
          }
        '''), '.date,.color{color:black;background:white;}.date__dialog,.date__overlay,.color__dialog,.color__overlay{position:absolute;}')



    def test_parentreference_inline_extend(self):
        self.assertEqual(self.process('''
          $field{
            color: black;
            background: white;

            @root &__dialog{
              position: absolute;
            }
          }

          .date{
            $field;
          }

          .color{
            $field;
          }
        '''), '.date,.color{color:black;background:white;}.date__dialog,.color__dialog{position:absolute;}')


    def test_parentreference_inline_multidist_extend(self):
        self.assertEqual(self.process('''
          $field{
            color: black;
            background: white;

            @root &__dialog, &__overlay{
              position: absolute;
            }
          }

          .date{
            $field;
          }

          .color{
            $field;
          }
        '''), '.date,.color{color:black;background:white;}.date__dialog,.date__overlay,.color__dialog,.color__overlay{position:absolute;}')


    def test_parentreference_inline_multidist_extend_content(self):
        self.assertEqual(self.process('''
          $field{
            color: black;
            background: white;

            @root &__dialog, &__overlay{
              position: absolute;
              @content;
            }
          }

          .date{
            $field < {
              width: 100px;
              height: 50px;
            }
          }

          .color{
            $field < {
              width: 200px;
              height: 200px;
            }
          }
        '''), '')



if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

