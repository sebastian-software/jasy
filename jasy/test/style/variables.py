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
$height = $width * .5;
$width += 20px;
$content = "Hello" + "World";
$negative = -100px;

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
            $width = 400px;

            .box{
              width: $width;
            }
            '''), '.box{width:400px;}')


    def test_define_unary(self):
        self.assertEqual(self.process('''
            $negative = -100px;

            .box{
              left: $negative;
            }
            '''), '.box{left:-100px;}')


    def test_define_color_hex(self):
        self.assertEqual(self.process('''
            $hex = #39FC20;

            .box{
              color: $hex;
            }
            '''), '.box{color:#39FC20;}')


    def test_define_color_hex3(self):
        self.assertEqual(self.process('''
            $hex = #3F2;

            .box{
              color: $hex;
            }
            '''), '.box{color:#3F2;}')


    def test_define_multi(self):
        import jasy.style.parse.Parser as Parser

        def wrapper():
            self.assertEqual(self.process('''
                $inner = 20px 10px;

                .box{
                  padding: $inner;
                }
                '''), '.box{padding: 20px 10px}')        

        self.assertRaises(Parser.SyntaxError, wrapper)


    def test_define_assignop_plus(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $width += 53;

            .box{
              width: $width;
            }
            '''), '.box{width:353px;}')


    def test_define_assignop_multi(self):
        self.assertEqual(self.process('''
            $width = 20px;
            $columns = 12;

            $width *= $columns;

            .box{
              width: $width;
            }
            '''), '.box{width:240px;}')


    def test_math_operation(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $width = $width * 1.3;
            $width *= .5 + .213;

            .box{
              width: $width;
            }
            '''), '.box{width:278.07px;}')


    def test_string_operation(self):
        self.assertEqual(self.process('''
            $text = "Hello {{name}}.";
            $text += "Welcome to my site!";
            $text = "<p>" + $text + "</p>";

            .box{
              content: $text;
            }
            '''), '.box{content:"<p>Hello {{name}}.Welcome to my site!</p>";}')


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

