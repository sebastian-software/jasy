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
        
    def test_selector_tag(self):
        self.assertEqual(self.process('h1 { color: red }'), 'h1{color:red;}')

    def test_selector_classname(self):
        self.assertEqual(self.process('.important { background: rgb(200,20,20) }'), '.important{background:rgb(200,20,20);}')

    def test_selector_id(self):
        self.assertEqual(self.process('#header { background-color: #fff }'), '#header{background-color:#fff;}')

    def test_selector_pseudo_class_invalidcss(self):
        # That's not really valid CSS though...
        self.assertEqual(self.process(':first-child { font-weight: bold }'), ':first-child{font-weight:bold;}')

    def test_selector_pseudo_element_invalidcss(self):
        # That's not really valid CSS though...
        self.assertEqual(self.process('::after { content: "AFTER" }'), '::after{content:"AFTER";}')

    def test_selector_pseudo_class(self):
        # That's not really valid CSS though...
        self.assertEqual(self.process('span:first-child { font-weight: bold }'), 'span:first-child{font-weight:bold;}')

    def test_selector_pseudo_element(self):
        # That's not really valid CSS though...
        self.assertEqual(self.process('span::after { content: "AFTER" }'), 'span::after{content:"AFTER";}')

    def test_selector_tag_multi(self):
        self.assertEqual(self.process('h1, h2 { color: red }'), 'h1,h2{color:red;}')

    def test_selector_class_multi(self):
        self.assertEqual(self.process('.message,.info { font-weight: normal }'), '.message,.info{font-weight:normal;}')

    def test_selector_id_multi(self):
        self.assertEqual(self.process('#header, #footer { background: #333 }'), '#header,#footer{background:#333;}')

    def test_selector_method(self):
        self.assertEqual(self.process('ul li:nth-child(2n) { background: lightgrey }'), 'ul li:nth-child(2n){background:lightgrey;}')

    def test_selector_attribute(self):
        self.assertEqual(self.process('ul li[selected] { background: blue }'), 'ul li[selected]{background:blue;}')

    def test_selector_child_combinator(self):
        self.assertEqual(self.process('ul > li { color: red }'), 'ul>li{color:red;}')

    def test_selector_adjacent_sibling_combinator(self):
        self.assertEqual(self.process('ul + li { color: red }'), 'ul+li{color:red;}')

    def test_selector_general_sibling_combinator(self):
        self.assertEqual(self.process('h1 ~ h2 { font-style: italic }'), 'h1~h2{font-style:italic;}')


"""
*
E[foo]
E[foo="bar"]
E[foo~="bar"]
E[foo^="bar"]
E[foo$="bar"]
E[foo*="bar"]
E[foo|="en"]
E:root
E:nth-child(n)
E:nth-last-child(n)
E:nth-of-type(n)
E:nth-last-of-type(n)
E:lang(fr)
E:enabled
E:disabled
E:checked
E::first-line
E::first-letter
E::before
E::after
E.warning
E:not(s)
E#myid

## DONE:

E
E F
E > F
E + F
E ~ F

E:first-child
E:last-child
E:first-of-type
E:last-of-type
E:only-child
E:only-of-type
E:empty
E:link
E:visited
E:active
E:hover
E:focus
E:target


"""



if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)   

