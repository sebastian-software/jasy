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


    def test_single(self):
        self.assertEqual(self.process('''
            @font-face{
              font-family: FiraSans;
              src: url(FiraSans-Bold.woff);
              font-style: normal;
              font-weight: bold;
            }
            '''), '@font-face{font-family:FiraSans;src:url(FiraSans-Bold.woff);font-style:normal;font-weight:bold;}')


    def test_double(self):
        self.assertEqual(self.process('''
            @font-face{
              font-family: FiraSans;
              src: url(FiraSans-Bold.woff);
              font-style: normal;
              font-weight: bold;
            }

            @font-face{
              font-family: FiraSans;
              src: url(FiraSans-BoldItalic.woff);
              font-style: italic;
              font-weight: bold;
            }
            '''), '@font-face{font-family:FiraSans;src:url(FiraSans-Bold.woff);font-style:normal;font-weight:bold;}@font-face{font-family:FiraSans;src:url(FiraSans-BoldItalic.woff);font-style:italic;font-weight:bold;}')




if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

