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

$font{
  font-family: Arial, sans-serif;
  font-size: 15px;
}

h1{
  $font;
  color: blue;
}

h2{
  $font;
  color: red;
}
"""

class Tests(unittest.TestCase):

    def process(self, code):
        callerName = inspect.stack()[1][3][5:]

        tree = Engine.getTree(code, callerName)
        tree = Engine.processTree(tree)
        return Engine.compressTree(tree)

    def test_extend(self):
        self.assertEqual(self.process('''
            $font{
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            h1{
              $font;
              color: blue;
            }

            h2{
              $font;
              color: red;
            }
            '''), 'h1,h2{font-family:Arial,sans-serif;font-size:15px;}h1{color:blue;}h2{color:red;}')
        
    def test_extend_def_as_func(self):
        self.assertEqual(self.process('''
            $font(){
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            h1{
              $font;
              color: blue;
            }

            h2{
              $font;
              color: red;
            }
            '''), 'h1,h2{font-family:Arial,sans-serif;font-size:15px;}h1{color:blue;}h2{color:red;}')


    def test_extend_call(self):
        self.assertEqual(self.process('''
            $font(){
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            h1{
              $font();
              color: blue;
            }

            h2{
              $font();
              color: red;
            }
            '''), 'h1,h2{font-family:Arial,sans-serif;font-size:15px;}h1{color:blue;}h2{color:red;}')


    def test_mixin_param(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(2);
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:30px;color:red;}')


    def test_mixin_param_toomany(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(2, 3);
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:30px;color:red;}')  


    def test_mixin_param_missing(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font();
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:30px;color:red;}')          




if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)   

