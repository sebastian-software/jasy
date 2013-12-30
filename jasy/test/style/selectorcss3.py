#!/usr/bin/env python3

import sys, os, unittest, logging, inspect

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.style.Engine as Engine

"""
SUPPORTED CSS SELECTORS
LIST FROM: http://www.w3.org/TR/css3-selectors/

*

E
E#myid
E.warning

E F
E > F
E + F
E ~ F

E:enabled
E:disabled
E:checked
E:root
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

E::first-line
E::first-letter
E::before
E::after

E[foo]
E[foo="bar"]
E[foo~="bar"]
E[foo^="bar"]
E[foo$="bar"]
E[foo*="bar"]
E[foo|="en"]

E:nth-child(n)
E:nth-last-child(n)
E:nth-of-type(n)
E:nth-last-of-type(n)
E:lang(fr)
E:not(s)
"""

class Tests(unittest.TestCase):

    def process(self, code):
        callerName = inspect.stack()[1][3][5:]

        tree = Engine.getTree(code, callerName)
        return Engine.compressTree(tree)

    def test_star(self):
        self.assertEqual(self.process('* { box-sizing: border-box }'), '*{box-sizing:border-box;}')

    def test_tag(self):
        self.assertEqual(self.process('h1 { color: red }'), 'h1{color:red;}')

    def test_classname(self):
        self.assertEqual(self.process('.important { background: rgb(200,20,20) }'), '.important{background:rgb(200,20,20);}')

    def test_id(self):
        self.assertEqual(self.process('#header { background-color: #fff }'), '#header{background-color:#fff;}')

    def test_tag_id(self):
        self.assertEqual(self.process('div#header { background-color: #fff }'), 'div#header{background-color:#fff;}')

    def test_pseudo_class(self):
        self.assertEqual(self.process('span:first-child { font-weight: bold }'), 'span:first-child{font-weight:bold;}')

    def test_pseudo_element(self):
        self.assertEqual(self.process('span::after { content: "AFTER" }'), 'span::after{content:"AFTER";}')

    def test_pseudo_element_dashed(self):
        self.assertEqual(self.process('span::first-line { content: "AFTER" }'), 'span::first-line{content:"AFTER";}')

    def test_tag_child(self):
        self.assertEqual(self.process('h1 span { font-size: 0.6em }'), 'h1 span{font-size:0.6em;}')

    def test_tag_multi(self):
        self.assertEqual(self.process('h1, h2 { color: red }'), 'h1,h2{color:red;}')

    def test_class_multi(self):
        self.assertEqual(self.process('.message,.info { font-weight: normal }'), '.message,.info{font-weight:normal;}')

    def test_id_multi(self):
        self.assertEqual(self.process('#header, #footer { background: #333 }'), '#header,#footer{background:#333;}')

    def test_methodlike_noarg(self):
        self.assertEqual(self.process('ul li:nth-child() { background: lightgrey }'), 'ul li:nth-child(){background:lightgrey;}')

    def test_methodlike_posarg(self):
        self.assertEqual(self.process('ul li:nth-child(2) { background: lightgrey }'), 'ul li:nth-child(2){background:lightgrey;}')

    def test_methodlike_iterarg(self):
        self.assertEqual(self.process('ul li:nth-child(2n) { background: lightgrey }'), 'ul li:nth-child(2n){background:lightgrey;}')

    def test_methodlike_lang(self):
        self.assertEqual(self.process('ul li:lang(de) { background: lightgrey }'), 'ul li:lang(de){background:lightgrey;}')

    def test_methodlike_not(self):
        self.assertEqual(self.process('ul li:not(:first-child) { background: lightgrey }'), 'ul li:not(:first-child){background:lightgrey;}')

    def test_attribute(self):
        self.assertEqual(self.process('ul li[selected] { background: blue }'), 'ul li[selected]{background:blue;}')

    def test_attribute_equal(self):
        self.assertEqual(self.process('ul li[selected="bar"] { background: blue }'), 'ul li[selected="bar"]{background:blue;}')

    def test_attribute_compare1(self):
        self.assertEqual(self.process('ul li[selected~="bar"] { background: blue }'), 'ul li[selected~="bar"]{background:blue;}')

    def test_attribute_compare2(self):
        self.assertEqual(self.process('ul li[selected^="bar"] { background: blue }'), 'ul li[selected^="bar"]{background:blue;}')

    def test_attribute_compare3(self):
        self.assertEqual(self.process('ul li[selected$="bar"] { background: blue }'), 'ul li[selected$="bar"]{background:blue;}')

    def test_attribute_compare4(self):
        self.assertEqual(self.process('ul li[selected*="bar"] { background: blue }'), 'ul li[selected*="bar"]{background:blue;}')

    def test_attribute_compare5(self):
        self.assertEqual(self.process('ul li[selected|="en"] { background: blue }'), 'ul li[selected|="en"]{background:blue;}')

    def test_child_combinator(self):
        self.assertEqual(self.process('ul > li { color: red }'), 'ul>li{color:red;}')

    def test_adjacent_sibling_combinator(self):
        self.assertEqual(self.process('ul + li { color: red }'), 'ul+li{color:red;}')

    def test_general_sibling_combinator(self):
        self.assertEqual(self.process('h1 ~ h2 { font-style: italic }'), 'h1~h2{font-style:italic;}')




if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

