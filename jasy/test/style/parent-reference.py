#!/usr/bin/env python3

import sys, os, unittest, logging

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.style.parse.Parser as Parser
import jasy.style.output.Compressor as Compressor

"""
SUPPORTS

h1{

  &:first-child{
    font-weight: bold;
  }

  .cssshadow &{
    text-shadow: 1px;
  }

  header &:first-child{
    color: red;
  }

}

"""

class Tests(unittest.TestCase):

    def process(self, code):
        return Compressor.Compressor().compress(Parser.parse(code))

    def test_reference_before(self):
        self.assertEqual(self.process('''
            h1{
              &:first-child{
                font-weight: bold;
              }
            }
            '''), '')
        
    def test_reference_after(self):
        self.assertEqual(self.process('''
            h1{
              .cssshadow &{
                text-shadow: 1px;
              }
            }
            '''), '')

    def test_reference_between(self):
        self.assertEqual(self.process('''
            h1{
              header &:first-child{
                color: red;
              }
            }
            '''), '')        




if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)   

