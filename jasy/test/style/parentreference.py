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
        callerName = inspect.stack()[1][3][5:]

        tree = Engine.getTree(code, callerName)
        tree = Engine.reduceTree(tree)
        return Engine.compressTree(tree)

    def test_before(self):
        self.assertEqual(self.process('''
            h1{
              &:first-child{
                font-weight: bold;
              }
            }
            '''), 'h1:first-child{font-weight:bold;}')

    def test_after(self):
        self.assertEqual(self.process('''
            h1{
              .cssshadow &{
                text-shadow: 1px;
              }
            }
            '''), '.cssshadow h1{text-shadow:1px;}')

    def test_between(self):
        self.assertEqual(self.process('''
            h1{
              header &:first-child{
                color: red;
              }
            }
            '''), 'header h1:first-child{color:red;}')


    def test_attribute(self):
        self.assertEqual(self.process('''
            li{
              &[selected]{
                color: blue;
              }
            }
            '''), 'li[selected]{color:blue;}')


    def test_inside(self):
        self.assertEqual(self.process('''
            li{
              list-item-type: square;

              .&st-item{
                color: blue;
              }
            }
            '''), 'li{list-item-type:square;}.list-item{color:blue;}')


    def test_inside_variant(self):
        self.assertEqual(self.process('''
            header{
              list-item-type: square;

              .fullscreen,
              .&-fullscreen{
                color: blue;
              }
            }
            '''), 'header{list-item-type:square;}header .fullscreen,.header-fullscreen{color:blue;}')

    def test_bem(self):
        self.assertEqual(self.process('''
            .block {
                &__element {
                  color: red;
                }
                &--modifier {
                  color: blue;
                }
            }
            '''), '.block__element{color:red;}.block--modifier{color:blue;}')


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

