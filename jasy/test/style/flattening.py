#!/usr/bin/env python3

import sys, os, unittest, logging, inspect

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.style.Engine as Engine
import jasy.core.Permutation as Permutation



class Tests(unittest.TestCase):

    def process(self, code):
        callerName = inspect.stack()[1][3][5:]

        permutation = Permutation.Permutation({
            "jasy.engine" : "gecko",
            "jasy.debug" : True
        })

        tree = Engine.getTree(code, callerName)
        tree = Engine.permutateTree(tree, permutation)
        tree = Engine.reduceTree(tree)

        return Engine.compressTree(tree)


    def test_media_with_one_selector(self):
        self.assertEqual(self.process('''
            @media print{
              body{
                color: black;
              }
            }

            @media screen{
              body{
                color: #333;
              }
            }
            '''), '@media print{body{color:black;}}@media screen{body{color:#333;}}')


    def test_order(self):
        self.assertEqual(self.process('''

            .rule1{
              color: black;
            }

            @media print{
              .rule2a{
                color: green;
              }

              .rule2b{
                color: blue;
              }
            }

            .rule3{
              color: grey;
            }

            @media screen{
              .rule4a{
                color: orange;
              }

              .rule4b{
                color: red;
              }
            }

            .rule5{
              color: white;
            }
            '''), '.rule1{color:black;}@media print{.rule2a{color:green;}.rule2b{color:blue;}}.rule3{color:grey;}@media screen{.rule4a{color:orange;}.rule4b{color:red;}}.rule5{color:white;}')


    def test_order_inner_media(self):
        self.assertEqual(self.process('''

            .rule1{
              color: black;
            }

            .rule2a{
              @media print{
                color: green;
              }
            }

            .rule2b{
              @media print{
                color: blue;
              }
            }

            .rule3{
              color: grey;
            }

            .rule4a{
              @media screen{
                color: orange;
              }
            }

            .rule4b{
              @media screen{
                color: red;
              }
            }

            .rule5{
              color: white;
            }
            '''), '.rule1{color:black;}@media print{.rule2a{color:green;}.rule2b{color:blue;}}.rule3{color:grey;}@media screen{.rule4a{color:orange;}.rule4b{color:red;}}.rule5{color:white;}')


    def test_merge_media(self):
        self.assertEqual(self.process('''
            @media print{
              body{
                color: black;
              }
            }

            @media print{
              header{
                color: #333;
              }
            }
            '''), '@media print{body{color:black;}header{color:#333;}}')


    def test_merge_selector(self):
        self.assertEqual(self.process('''
            body{
              color: black;
            }

            body{
              font-weight: normal;
            }
            '''), 'body{color:black;font-weight:normal;}')


    def test_merge_media_and_selector(self):
        self.assertEqual(self.process('''
            @media print{
              body{
                color: black;
              }
            }

            @media print{
              body{
                color: #333;
              }
            }
            '''), '@media print{body{color:black;color:#333;}}')


    def test_merge_media_and_selector_conditional(self):
        self.assertEqual(self.process('''
            @media print{
              body{
                color: black;
              }
            }

            @if jasy.debug{
              @media print{
                body{
                  color: #333;
                }
              }
            }
            '''), '@media print{body{color:black;color:#333;}}')






if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

