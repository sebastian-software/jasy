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

      self.assertRaises(Parser.ParseError, wrapper)


    def test_charset_wrong_syntax(self):
        def wrapper():
          self.process(r'''
/* Invalid as it requires quotes */
@charset iso-8859-15;
          ''')

        self.assertRaises(Parser.ParseError, wrapper)


    def test_page(self):
        self.assertEqual(self.process(r'''
          @page{
            margin-left: 2cm;
            margin-right: 2cm;
          }
        '''), '@page{margin-left:2cm;margin-right:2cm;}')


    def test_page_selector_left(self):
        self.assertEqual(self.process(r'''
          @page :left {
            margin-left: 4cm;
            margin-right: 3cm;
          }
        '''), '@page :left{margin-left:4cm;margin-right:3cm;}')


    def test_page_selector_right(self):
        self.assertEqual(self.process(r'''
          @page :right {
            margin-left: 3cm;
            margin-right: 4cm;
          }
        '''), '@page :right{margin-left:3cm;margin-right:4cm;}')


    def test_page_selector_first(self):
        self.assertEqual(self.process(r'''
          @page :first {
            margin-left: 1cm;
            margin-right: 1cm;
            page-break: avoid;
          }
        '''), '@page :first{margin-left:1cm;margin-right:1cm;page-break:avoid;}')


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

