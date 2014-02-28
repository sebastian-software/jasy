#!/usr/bin/env python3

import sys, os, unittest, logging, inspect

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.style.Engine as Engine
import jasy.core.Permutation as Permutation
import jasy.style.parse.Parser as Parser


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


    def test_charset(self):
        self.assertEqual(self.process(r'''
/* Set the encoding of the style sheet to Unicode UTF-8 - dropped with warning */
@charset "UTF-8";
'''), '')


    def test_charset_invalid(self):
      def wrapper():
        self.process(r'''
/* Set the encoding of the style sheet to Latin-9 (Western European languages, with euro sign) - throws error */
@charset 'iso-8859-15';
        ''')

      self.assertRaises(Parser.SyntaxError, wrapper)


    def test_charset_wrong_syntax(self):
        def wrapper():
          self.process(r'''
/* Invalid as it requires quotes */
@charset iso-8859-15;
          ''')

        self.assertRaises(Parser.SyntaxError, wrapper)





if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

