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


    def test_print(self):
        self.assertEqual(self.process('''
            @media print{
              body{
                color: black;
              }
            }
            '''), '@media print{body{color:black;}}')


    def test_comma(self):
        self.assertEqual(self.process('''
            @media handheld, tv{
              body{
                background-color: yellow;
              }
            }
            '''), '@media handheld{body{background-color:yellow;}}')


    def test_size(self):
        self.assertEqual(self.process('''
            @media (max-width: 600px) {
              .sidebar {
                display: none;
              }
            }
            '''), '@media (max-width:600px){.sidebar{display:none;}}')


    def test_and(self):
        self.assertEqual(self.process('''
            @media tv and (min-width: 700px) and (orientation: landscape) {
              .headline {
                float: left;
              }
            }
            '''), '@media tv and (min-width:700px) and (orientation:landscape){.headline{float:left;}}')


    def test_ratio(self):
        self.assertEqual(self.process('''
            @media screen and (min-aspect-ratio: 1/1) {
              body{
                 font-size: 16px;
              }
            }
            '''), '@media screen and (min-aspect-ratio:1/1){body{font-size:16px;}}')



    def test_comma_and(self):
        self.assertEqual(self.process('''
            @media handheld and (min-width: 20em), screen and (min-width: 20em) {
              header{
                height: 30px;
              }
            }
            '''), '@media handheld and (min-width:20em){header{height:30px;}}')


    def test_reallife_pixel(self):
        self.assertEqual(self.process('''
            @media (-webkit-min-device-pixel-ratio: 2), /* Webkit-based browsers */
              (min--moz-device-pixel-ratio: 2),         /* Older Firefox browsers (prior to Firefox 16) */
              (min-resolution: 2dppx),                  /* The standard way */
              (min-resolution: 192dpi)                  /* dppx fallback */
            {
              button{
                background-size: 60px 20px;
              }
            }
            '''), '@media (-webkit-min-device-pixel-ratio:2){button{background-size:60px 20px;}}')







if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

