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

$width = 300px;

"""

class Tests(unittest.TestCase):

    def process(self, code):
        callerName = inspect.stack()[1][3][5:]

        tree = Engine.getTree(code, callerName)
        tree = Engine.processTree(tree)
        return Engine.compressTree(tree)

    def test_unused(self):
        self.assertEqual(self.process('''
            $width = 300px;
            '''), '')

    def test_unused_operation(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $height = 200px;
            $size = $width * $height;
            '''), '')
        
    def test_value_simple(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $height = 200px;

            .box{
              width: $width;
              height: $height;
            }
            '''), '.box{width:300px;height:200px;}')


    def test_value_simple_math(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $height = 200px;

            .box{
              $padding = 10px;
              padding: $padding;
              width: $width - $padding * 2;
              height: $height - $padding * 2;
            }
            '''), '.box{padding:10px;width:280px;height:180px;}')


    def test_define_override(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $width += 20;

            .box{
              width: $width;
            }
            '''), '')



    def test_value_operator_math(self):
        self.assertEqual(self.process('''
            $base = 30px;
            $larger = $base * 1.3;
            $smaller = $base * 0.6;
            $reallysmall = $smaller - 10;

            // snap
            $larger = $larger - $larger % 5;

            h1{
              font-size: $larger;
            }

            p{
              font-size: $base;
            }

            small{
              font-size: $smaller;
            }

            footer{
              font-size: $reallysmall;
            }
            '''), 'h1{font-size:35px;}p{font-size:30px;}small{font-size:18px;}footer{font-size:8px;}')






if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)   

