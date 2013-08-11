#!/usr/bin/env python3

import sys, os, unittest, logging, inspect

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.style.Engine as Engine



class Tests(unittest.TestCase):

    def process(self, code):
        callerName = inspect.stack()[1][3][5:]

        tree = Engine.getTree(code, callerName)
        tree = Engine.processTree(tree)
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

            $engine = @variable(jasy.engine);
            h2{
              content: $engine;
            }
            '''), 'h1{font-size:20px;}h1{outline:1px solid red;}p{color:red;}h2{content:"webkit";}')




if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)   

