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

h1{
  font-size: 20px;

  @root html.desktop &{
    font-size: 30px;
  }
}

"""

class Tests(unittest.TestCase):

    def process(self, code):
        callerName = inspect.stack()[1][3][5:]

        tree = Engine.getTree(code, callerName)
        tree = Engine.reduceTree(tree)
        return Engine.compressTree(tree)


    def test_basic(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            @root .bar {
              color: gray;
            }
          }
        '''), '.foo{color:red;}.bar{color:gray;}')



    def test_basic_supports(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            @root .bar {
              @supports(color:gray){
                color: gray;
              }
            }
          }
        '''), '.foo{color:red;}@supports (color:gray){.bar{color:gray;}}')


    def test_basic_media(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            @root .bar {
              @media screen{
                color: gray;
              }

              @media print{
                color: black;
              }
            }
          }
        '''), '.foo{color:red;}@media screen{.bar{color:gray;}}@media print{.bar{color:black;}}')


    def test_deep(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            @root .bar {
              .deeper{
                color: gray;
              }
            }
          }
        '''), '.foo{color:red;}.bar .deeper{color:gray;}')


    def test_deep_multidist(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            @root .bar, .baz {
              .deeper{
                color: gray;
              }
            }
          }
        '''), '.foo{color:red;}.bar .deeper,.baz .deeper{color:gray;}')


    def test_parentreference_append(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            @root .bar & {
              color: gray;
            }
          }
        '''), '.foo{color:red;}.bar .foo{color:gray;}')


    def test_parentreference_between(self):
        self.assertEqual(self.process('''
          .message {
            color: red;

            @root & .title-bar {
              background: gray;
              font-weight: bold;
            }
          }
        '''), '.message{color:red;}.message .title-bar{background:gray;font-weight:bold;}')


    def test_parentreference_generatedcontent(self):
        self.assertEqual(self.process('''
          .foo {
            color: red;

            &::after{
              content: "DESKTOP";
            }

            @root html.mobile &::after {
              content: "MOBILE";
            }
          }
        '''), '.foo{color:red;}.foo::after{content:"DESKTOP";}html.mobile .foo::after{content:"MOBILE";}')


    def test_parentreference_append_multiroot(self):
        self.assertEqual(self.process('''
          .foo,
          h1 .innerfoo {
            color: red;

            @root .bar & {
              color: gray;
            }
          }
        '''), '.foo,h1 .innerfoo{color:red;}.bar .foo,.bar h1 .innerfoo{color:gray;}')


    def test_parentreference_inline_inner(self):
        self.assertEqual(self.process('''
          .date{
            color: black;
            background: white;

            @root{
              &__dialog{
                position: absolute;
              }
            }
          }
        '''), '.date{color:black;background:white;}.date__dialog{position:absolute;}')


    def test_parentreference_inline(self):
        self.assertEqual(self.process('''
          .date{
            color: black;
            background: white;

            @root &__dialog{
              position: absolute;
            }
          }
        '''), '.date{color:black;background:white;}.date__dialog{position:absolute;}')


    def test_parentreference_inline_multiroot(self):
        self.assertEqual(self.process('''
          .date,
          .color{
            color: black;
            background: white;

            @root &__dialog{
              position: absolute;
            }
          }
        '''), '.date,.color{color:black;background:white;}.date__dialog,.color__dialog{position:absolute;}')


    def test_parentreference_inline_multiroot_multidist(self):
        self.assertEqual(self.process('''
          .date,
          .color{
            color: black;
            background: white;

            @root &__dialog, &__overlay{
              position: absolute;
            }
          }
        '''), '.date,.color{color:black;background:white;}.date__dialog,.date__overlay,.color__dialog,.color__overlay{position:absolute;}')



    def test_parentreference_inline_extend(self):
        self.assertEqual(self.process('''
          $field{
            color: black;
            background: white;

            @root &__dialog{
              position: absolute;
            }
          }

          .date{
            $field;
          }

          .color{
            $field;
          }
        '''), '.date,.color{color:black;background:white;}.date__dialog,.color__dialog{position:absolute;}')


    def test_parentreference_inline_multidist_extend(self):
        self.assertEqual(self.process('''
          $field{
            color: black;
            background: white;

            @root &__dialog, &__overlay{
              position: absolute;
            }
          }

          .date{
            $field;
          }

          .color{
            $field;
          }
        '''), '.date,.color{color:black;background:white;}.date__dialog,.date__overlay,.color__dialog,.color__overlay{position:absolute;}')



    def test_parentreference_extend_content_single(self):
        self.assertEqual(self.process('''
          $field{
            @root &__dialog{
              @content;
            }
          }

          .date{
            $field < {
              width: 100px;
            }
          }
        '''), '.date__dialog{width:100px;}')



    def test_parentreference_extend_content_double(self):
        self.assertEqual(self.process('''
          $field{
            @root &__dialog{
              @content;
            }
          }

          .date{
            $field < {
              width: 100px;
            }
          }

          .color{
            $field < {
              width: 200px;
            }
          }
        '''), '.date__dialog{width:100px;}.color__dialog{width:200px;}')



    def test_parentreference_extend_content_double_deeper(self):
        self.assertEqual(self.process('''
          $field{
            @root &__dialog{
              @content;
            }
          }

          .date{
            $field < {
              width: 100px;
            }
          }

          .color{
            $field < {
              width: 200px;

              .button{
                border: 2px solid red;
              }
            }
          }
        '''), '.date__dialog{width:100px;}.color__dialog{width:200px;}.color__dialog .button{border:2px solid red;}')


    def test_parentreference_extend_content_double_multi(self):
        self.assertEqual(self.process('''
          $field{
            border: 1px solid black;

            @root &__dialog, &__overlay{
              position: absolute;
              @content;
            }
          }

          .date{
            background: blue;

            $field < {
              width: 100px;
              height: 50px;
            }
          }

          .color{
            background: red;

            $field < {
              width: 200px;
              height: 200px;
            }
          }
        '''), '.date,.color{border:1px solid black;}.date__dialog,.date__overlay,.color__dialog,.color__overlay{position:absolute;}.date__dialog,.date__overlay{width:100px;height:50px;}.color__dialog,.color__overlay{width:200px;height:200px;}.date{background:blue;}.color{background:red;}')



if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

