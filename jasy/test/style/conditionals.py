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


    def test_if(self):
        self.assertEqual(self.process('''
            h1{
              font-size: 20px;
            }

            @if jasy.debug == true{
              h1{
                outline: 1px solid red;
              }

              p{
                color:red;
              }
            }
            '''), 'h1{font-size:20px;outline:1px solid red;}p{color:red;}')


    def test_if_else_true(self):
        self.assertEqual(self.process('''
            h1{
              font-size: 20px;
            }

            @if jasy.debug == true{
              h1{
                outline: 1px solid red;
              }

              p{
                color:red;
              }
            }
            @else
            {
              h1{
                outline: none;
              }

              p{
                color: black;
              }
            }
            '''), 'h1{font-size:20px;outline:1px solid red;}p{color:red;}')


    def test_if_else_false(self):
        self.assertEqual(self.process('''
            h1{
              font-size: 20px;
            }

            @if jasy.debug == false
            {
              h1{
                outline: 1px solid red;
              }

              p{
                color:red;
              }
            }
            @else
            {
              h1{
                outline: none;
              }

              p{
                color: black;
              }
            }
            '''), 'h1{font-size:20px;outline:none;}p{color:black;}')


    def test_if_else_false_paren(self):
        self.assertEqual(self.process('''
            h1{
              font-size: 20px;
            }

            @if (jasy.debug == false)
            {
              h1{
                outline: 1px solid red;
              }

              p{
                color:red;
              }
            }
            @else
            {
              h1{
                outline: none;
              }

              p{
                color: black;
              }
            }
            '''), 'h1{font-size:20px;outline:none;}p{color:black;}')


    def test_if_else_false_paren_notoper(self):
        self.assertEqual(self.process('''
            h1{
              font-size: 20px;
            }

            @if (jasy.debug == !false)
            {
              h1{
                outline: 1px solid red;
              }

              p{
                color:red;
              }
            }
            @else
            {
              h1{
                outline: none;
              }

              p{
                color: black;
              }
            }
            '''), 'h1{font-size:20px;outline:1px solid red;}p{color:red;}')


    def test_field(self):
        self.assertEqual(self.process('''
            h2{
              content: @field(jasy.engine);
            }
            '''), 'h2{content:"gecko";}')


    def test_field_as_variable(self):
        self.assertEqual(self.process('''
            $engine = @field(jasy.engine);
            h2{
              content: $engine;
            }
            '''), 'h2{content:"gecko";}')



if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

