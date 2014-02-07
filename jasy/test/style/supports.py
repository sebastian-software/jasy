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


    def test_outer(self):
        self.assertEqual(self.process(r'''
            @supports(-webkit-text-stroke: 1px black) {
              h1{
                -webkit-text-stroke: 1px black;
              }
            }
            '''), '@supports (-webkit-text-stroke:1px black){h1{-webkit-text-stroke:1px black;}}')


    def test_between(self):
        self.assertEqual(self.process(r'''
            body{
              @supports(-webkit-text-stroke: 1px black) {
                h1{
                  -webkit-text-stroke: 1px black;
                }
              }
            }
            '''), '@supports (-webkit-text-stroke:1px black){body h1{-webkit-text-stroke:1px black;}}')


    def test_inner(self):
        self.assertEqual(self.process(r'''
            body{
              h1{
                color: black;

                @supports(-webkit-text-stroke: 1px black) {
                  -webkit-text-stroke: 1px black;
                }
              }
            }
            '''), 'body h1{color:black;}@supports (-webkit-text-stroke:1px black){body h1{-webkit-text-stroke:1px black;}}')


    def test_combined(self):
        self.assertEqual(self.process(r'''
            body{
              @supports(-webkit-text-stroke: 1px black) {
                h1{
                  -webkit-text-stroke: 1px black;

                  @supports (color:black){
                    color: black;
                  }
                }
              }
            }
            '''), '@supports (-webkit-text-stroke:1px black){body h1{-webkit-text-stroke:1px black;}}@supports (color:black) and (-webkit-text-stroke:1px black){body h1{color:black;}}')


    def test_combined_inner(self):
        self.assertEqual(self.process(r'''
            body{
              @supports(-webkit-text-stroke: 1px black) {
                h1{
                  -webkit-text-stroke: 1px black;

                  @supports (color:black){
                    em{
                      color: black;
                    }
                  }
                }
              }
            }
            '''), '@supports (-webkit-text-stroke:1px black){body h1{-webkit-text-stroke:1px black;}}@supports (color:black) and (-webkit-text-stroke:1px black){body h1 em{color:black;}}')


    def test_atmedia(self):
        self.assertEqual(self.process(r'''
            @supports(color: black) {
              p{
                @media print, tv{
                  color: black;
                }

                @media screen{
                  color: #333;
                }
              }
            }
            '''), '@media print,tv{@supports (color:black){p{color:black;}}}@media screen{@supports (color:black){p{color:#333;}}}')


    def test_join(self):
        self.assertEqual(self.process(r'''
            @supports(color: black) {
              p{
                color: black;
              }
            }

            @supports(color: black) {
              span{
                color: #333;
              }
            }
            '''), '@supports (color:black){p{color:black;}span{color:#333;}}')


    def test_join_inside_atmedia(self):
        self.assertEqual(self.process(r'''
            @media screen{
              @supports(color: black) {
                p{
                  color: black;
                }
              }

              @supports(color: black) {
                span{
                  color: #333;
                }
              }
            }
            '''), '@media screen{@supports (color:black){p{color:black;}span{color:#333;}}}')


    def test_atmedia_deeper(self):
        self.assertEqual(self.process(r'''
            @media (min-width:800px) {
              @supports(color: black) {
                p{
                  @media print, tv{
                    color: black;
                  }

                  @media screen{
                    small{
                      color: #333;
                    }
                  }
                }
              }
            }
            '''), '''@media print and (min-width:800px),tv and (min-width:800px){@supports (color:black){p{color:black;}}}@media screen and (min-width:800px){@supports (color:black){p small{color:#333;}}}''')




if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

