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


    def test_basic(self):
        self.assertEqual(self.process(r'''
            .foo{
              content: "Hello";
            }
            '''), '.foo{content:"Hello";}')


    def test_quotes(self):
        self.assertEqual(self.process(r'''
            .foo{
              quotes: "\201E" "\201C" "\201A" "\2018";
            }
            '''), r'.foo{quotes:"\201E" "\201C" "\201A" "\2018";}')


    def test_single(self):
        self.assertEqual(self.process(r'''
            .foo{
              content: 'Hello "Frank"';
            }
            '''), '.foo{content:\'Hello "Frank"\';}')




if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

