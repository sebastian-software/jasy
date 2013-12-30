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


    def test_named(self):
        self.assertEqual(self.process('''
            @keyframes bump {
              from {
                color: red;
              }
              to {
                color: white;
              }
            }
            '''), '@keyframes bump{from{color:red;}to{color:white;}}')


    def test_percent(self):
        self.assertEqual(self.process('''
            @keyframes bump {
              0% {
                color: red;
              }
              100% {
                color: white;
              }
            }
            '''), '@keyframes bump{0%{color:red;}100%{color:white;}}')


    def test_multistep(self):
        self.assertEqual(self.process('''
            @keyframes bump {
              0%, 100% {
                font-size: 10px;
              }
              50% {
                font-size: 12px;
              }
            }
            '''), '@keyframes bump{0%,100%{font-size:10px;}50%{font-size:12px;}}')










if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

