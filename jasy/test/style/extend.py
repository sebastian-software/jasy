#!/usr/bin/env python3

import sys, os, unittest, logging, inspect

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.style.Engine as Engine

from jasy.env.State import session

session.init()

import jasy.core.Profile as Profile

profile = Profile.Profile(session)

profile.addCommand("jasy.asset", lambda fileId: "resolved/%s" % fileId, "url")
profile.addCommand("jasy.width", lambda fileId: 42, "px")
profile.addCommand("jasy.height", lambda fileId: 38, "px")

class Tests(unittest.TestCase):

    def process(self, code):
        callerName = inspect.stack()[1][3][5:]

        tree = Engine.getTree(code, callerName)
        tree = Engine.reduceTree(tree, profile)
        return Engine.compressTree(tree)

    def test_basic(self):
        self.assertEqual(self.process('''
            $font{
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            h1{
              $font;
              color: blue;
            }

            h2{
              $font;
              color: red;
            }
            '''), 'h1,h2{font-family:Arial,sans-serif;font-size:15px;}h1{color:blue;}h2{color:red;}')


    def test_double(self):
        self.assertEqual(self.process('''
            $family{
              font-family: Arial, sans-serif;
            }

            $big{
              $family;
              font-size: 30px;
            }

            $small{
              $family;
              font-size: 15px;
            }

            h1{
              $big;
              color: blue;
            }

            h2{
              $small;
              color: red;
            }

            header{
              $big;
            }

            small, p.small{
              $family;
              font-size: 10px;
            }
            '''), 'h1,header,h2,small,p.small{font-family:Arial,sans-serif;}h1,header{font-size:30px;}h2{font-size:15px;}h1{color:blue;}h2{color:red;}small,p.small{font-size:10px;}')



    def test_atmedia(self):
        self.assertEqual(self.process('''
            $font{
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            @media screen{
              h1{
                $font;
                color: blue;
              }
            }

            h1{
              $font;
              color: black;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:15px;}@media screen{h1{font-family:Arial,sans-serif;font-size:15px;color:blue;}}h1{color:black;}')


    def test_atsupport(self):
        self.assertEqual(self.process('''
            $font{
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            @supports (color:blue){
              h1{
                $font;
                color: blue;
              }
            }

            h1{
              $font;
              color: black;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:15px;}@supports (color:blue){h1{font-family:Arial,sans-serif;font-size:15px;color:blue;}}h1{color:black;}')


    def test_content_simple(self):
        self.assertEqual(self.process('''
            $inlineblock(){
              display: inline-block;
              zoom: 1;

              @content;
            }

            h1{
              $inlineblock() < {
                margin-right: 2px;
              }
            }

            p{
              $inlineblock();
            }
            '''), 'h1,p{display:inline-block;zoom:1;}h1{margin-right:2px;}')


    def test_content_simple_double(self):
        self.assertEqual(self.process('''
            $inlineblock(){
              display: inline-block;
              zoom: 1;

              @content;
            }

            h1{
              $inlineblock() < {
                margin-right: 2px;
              }
            }

            p{
              $inlineblock() < {
                margin-right: 1px;
              }
            }
            '''), 'h1,p{display:inline-block;zoom:1;}h1{margin-right:2px;}p{margin-right:1px;}')



    def test_content_without_call(self):
        self.assertEqual(self.process('''
            $inlineblock(){
              display: inline-block;
              zoom: 1;

              @content;
            }

            h1{
              $inlineblock < {
                margin-right: 2px;
              }
            }

            p{
              $inlineblock();
            }
            '''), 'h1,p{display:inline-block;zoom:1;}h1{margin-right:2px;}')


    def test_content_with_supports_in_call(self):
        self.assertEqual(self.process('''
            $inlineblock(){
              display: inline-block;
              zoom: 1;

              @content;
            }

            h1{
              $inlineblock() < {
                margin-right: 2px;
              }
            }

            p{
              @supports (display:inline-block){
                $inlineblock();
              }
            }
            '''), 'h1{display:inline-block;zoom:1;margin-right:2px;}@supports (display:inline-block){p{display:inline-block;zoom:1;}}')


    def test_content_with_supports_in_mixin(self):
        self.assertEqual(self.process('''
            $inlineblock(){
              @supports (display:inline-block){
                display: inline-block;
              }
              zoom: 1;

              @content;
            }

            h1{
              $inlineblock() < {
                margin-right: 2px;
              }
            }

            p{
              $inlineblock();
            }
            '''), 'h1,p{zoom:1;}@supports (display:inline-block){h1,p{display:inline-block;}}h1{margin-right:2px;}')


    def test_content_with_media_in_call(self):
        self.assertEqual(self.process('''
            $inlineblock(){
              display: inline-block;
              zoom: 1;

              @content;
            }

            h1{
              $inlineblock() < {
                margin-right: 2px;
              }
            }

            p{
              @media (min-width: 800px){
                $inlineblock();
              }
            }
            '''), 'h1{display:inline-block;zoom:1;margin-right:2px;}@media (min-width:800px){p{display:inline-block;zoom:1;}}')


    def test_content_with_preceding(self):
        self.assertEqual(self.process('''
            $inlineblock(){
              display: inline-block;
              zoom: 1;

              @content;
            }

            h1{
              zoom: 2;
            }

            h1{
              $inlineblock() < {
                margin-right: 2px;
              }

              color: red;
            }

            p{
              $inlineblock();
              text-decoration:underline;
            }
            '''), 'h1,p{display:inline-block;zoom:1;}h1{margin-right:2px;zoom:2;color:red;}p{text-decoration:underline;}')


    def test_content_with_followup(self):
        self.assertEqual(self.process('''
            $inlineblock(){
              display: inline-block;
              zoom: 1;

              @content;
            }

            h1{
              $inlineblock() < {
                margin-right: 2px;
              }

              color: red;
            }

            h1{
              zoom: 2;
            }

            p{
              $inlineblock();
              text-decoration:underline;
            }
            '''), 'h1,p{display:inline-block;zoom:1;}h1{margin-right:2px;color:red;zoom:2;}p{text-decoration:underline;}')


    def test_content_with_media_in_mixin(self):
        self.assertEqual(self.process('''
            $inlineblock(){
              @media (min-width: 800px){
                display: inline-block;
              }
              zoom: 1;

              @content;
            }

            h1{
              $inlineblock() < {
                margin-right: 2px;
              }
            }

            p{
              $inlineblock();
            }
            '''), 'h1,p{zoom:1;}@media (min-width:800px){h1,p{display:inline-block;}}h1{margin-right:2px;}')


    def test_content_media_and_supports(self):
        self.assertEqual(self.process('''
            $autowidth(){
              width: auto;

              @media (min-width: 30em){
                width: 30em;
              }

              @media (min-width: 50em){
                width: 50em;

                @supports (width: intrinsic){
                  width: intrinsic;
                }
              }

              margin-left: auto;
              margin-right: auto;
            }

            h1{
              color: blue;
              $autowidth;
            }

            p{
              $autowidth;
              color: red;
            }
            '''), 'h1,p{width:auto;margin-left:auto;margin-right:auto;}@media (min-width:30em){h1,p{width:30em;}}@media (min-width:50em){h1,p{width:50em;}@supports (width:intrinsic){h1,p{width:intrinsic;}}}h1{color:blue;}p{color:red;}')


    def test_content_deeper(self):
        self.assertEqual(self.process('''
            $icon(){
              &::before{
                display: inline-block;
                @content;
              }
            }

            h1{
              $icon() < {
                margin-right: 2px;
              }
            }

            p{
              $icon() < {
                margin-right: 4px;
              }
            }
            '''), 'h1::before,p::before{display:inline-block;}h1::before{margin-right:2px;}p::before{margin-right:4px;}')


    def test_def_as_func(self):
        self.assertEqual(self.process('''
            $font(){
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            h1{
              $font;
              color: blue;
            }

            h2{
              $font;
              color: red;
            }
            '''), 'h1,h2{font-family:Arial,sans-serif;font-size:15px;}h1{color:blue;}h2{color:red;}')


    def test_call(self):
        self.assertEqual(self.process('''
            $font(){
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            h1{
              $font();
              color: blue;
            }

            h2{
              $font();
              color: red;
            }
            '''), 'h1,h2{font-family:Arial,sans-serif;font-size:15px;}h1{color:blue;}h2{color:red;}')


    def test_local(self):
        self.assertEqual(self.process('''
            h1{
              $font{
                font-family: Arial, sans-serif;
                font-size: 15px;
              }

              $font;
              color: blue;

              span {
                $font;
                font-size: 70%;
              }
            }
            '''), 'h1,h1 span{font-family:Arial,sans-serif;font-size:15px;}h1{color:blue;}h1 span{font-size:70%;}')


    def test_local_with_atmedia(self):
        self.assertEqual(self.process('''
          h1{
            $font{
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            $font;

            @media print{
              font-size: 20pt;
              color: #111;
            }

            color: #333;
          }
          '''), 'h1{font-family:Arial,sans-serif;font-size:15px;color:#333;}@media print{h1{font-size:20pt;color:#111;}}')


    def test_local_with_atsupports(self):
        self.assertEqual(self.process('''
          h1{
            $font{
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            $font;

            @supports (color:lightgreen){
              font-size: 20pt;
              color: lightgreen;
            }

            color: #333;
          }
          '''), 'h1{font-family:Arial,sans-serif;font-size:15px;color:#333;}@supports (color:lightgreen){h1{font-size:20pt;color:lightgreen;}}')


    def test_local_with_inner_atmedia(self):
        self.assertEqual(self.process('''
          h1{
            $font{
              font-family: Arial, sans-serif;
              font-size: 15px;

              @media print{
                font-size: 20pt;
                color: #111;
              }
            }

            $font;
            color: #333;

            small{
              $font;
              color: red;
            }
          }
          '''), 'h1,h1 small{font-family:Arial,sans-serif;font-size:15px;}h1{color:#333;}@media print{h1,h1 small{font-size:20pt;color:#111;}}h1 small{color:red;}')


    def test_local_with_inner_atsupports(self):
        self.assertEqual(self.process('''
          h1{
            $font{
              font-family: Arial, sans-serif;
              font-size: 15px;

              @supports (color:lightgreen){
                font-size: 20pt;
                color: lightgreen;
              }
            }

            $font;
            color: #333;

            small{
              $font;
              color: red;
            }
          }
          '''), 'h1,h1 small{font-family:Arial,sans-serif;font-size:15px;}h1{color:#333;}@supports (color:lightgreen){h1,h1 small{font-size:20pt;color:lightgreen;}}h1 small{color:red;}')


    def test_local_complex(self):
        self.assertEqual(self.process('''
            h1{
              $font{
                font-family: Arial, sans-serif;
                font-size: 15px;
              }

              $font;
              color: blue;

              span {
                $font;
                font-size: 70%;

                small{
                  $font;
                  font-size: 50%;
                }
              }

              background: blue;
              font-weight: bold;
            }
            '''), 'h1,h1 span,h1 span small{font-family:Arial,sans-serif;font-size:15px;}h1{color:blue;background:blue;font-weight:bold;}h1 span{font-size:70%;}h1 span small{font-size:50%;}')


    def test_local_deeper(self):
        self.assertEqual(self.process('''
            h1{
              color: black;
              text-decoration: underline;

              strong{
                $font{
                  font-family: Arial, sans-serif;
                  font-size: 30px;
                }

                $font;
                color: black;
              }

              small{
                $font{
                  font-family: Arial, sans-serif;
                  font-size: 20px;
                }

                $font;
                color: grey;
              }

            }
            '''), 'h1 strong{font-family:Arial,sans-serif;font-size:30px;}h1 small{font-family:Arial,sans-serif;font-size:20px;}h1{color:black;text-decoration:underline;}h1 strong{color:black;}h1 small{color:grey;}')


    def test_local_override(self):
        self.assertEqual(self.process('''
            $icon(){
              &::after{
                content: "u1929";
                font-family: Icons;
              }
            }

            h1{
              $icon {
                margin-right: 2px;
                margin-top: 1px;
              }

              $icon;
            }
            '''), 'h1{margin-right:2px;margin-top:1px;}')


    def test_extend_or_mixin(self):
        self.assertEqual(self.process('''
            $box($color=red) {
              color: $color;
              border: 1px solid $color;
            }

            .errorbox{
              $box;
            }

            .seconderrorbox{
              $box;
            }

            .messagebox{
              $box(green);
            }
            '''), '.errorbox,.seconderrorbox{color:red;border:1px solid red;}.messagebox{color:green;border:1px solid green;}')


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

