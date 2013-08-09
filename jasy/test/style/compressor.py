#!/usr/bin/env python3

import sys, os, unittest, logging

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.style.parse.Parser as Parser
import jasy.style.output.Compressor as Compressor


class Tests(unittest.TestCase):

    def process(self, code):
        return Compressor.Compressor().compress(Parser.parse(code))
        
    def test_basic_tag(self):
        self.assertEqual(self.process('h1 { color: red }'), 'h1{color:red;}')

    def test_basic_classname(self):
        self.assertEqual(self.process('.important { background: rgb(200,20,20) }'), '.important{background:rgb(200,20,20);}')

    def test_basic_id(self):
        self.assertEqual(self.process('#header { background-color: #fff }'), '#header{background-color:#fff;}')

    def test_basic_pseudo_class(self):
        self.assertEqual(self.process('span:first-child { font-weight: bold }'), '')

    def test_basic_pseudo_element(self):
        self.assertEqual(self.process('div::after { content: "AFTER" }'), '')






if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)   

