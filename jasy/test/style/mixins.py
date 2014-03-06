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


    def test_param(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: @expr(15px * $size);
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(2);
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:30px;color:red;}')


    def test_param_forcall(self):
        self.assertEqual(self.process('''
            $icon($fullywild){
              background: @jasy.asset($fullywild);
            }

            h1{
              $icon("foo/bar.gif");
              color: blue;
            }

            h2{
              $icon("foo/rotate.gif");
              color: red;
            }
            '''), 'h1{background:url(resolved/foo/bar.gif);color:blue;}h2{background:url(resolved/foo/rotate.gif);color:red;}')


    def test_param_toomany(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: @expr(15px * $size);
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(2, 3);
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:30px;color:red;}')


    def test_param_missing(self):
        import jasy.style.process.Executer as Executer

        def wrapper():
            self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: @expr(15px * $size);
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font();
              color: red;
            }
            ''')

        self.assertRaises(Executer.ExecuterError, wrapper)


    def test_default_param(self):
        self.assertEqual(self.process('''
            $font($size=2){
              font-family: Arial, sans-serif;
              font-size: @expr(15px * $size);
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font();
              color: red;
            }
            '''), 'h2{font-family:Arial,sans-serif;font-size:30px;}h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{color:red;}')


    def test_default_param_two_extends(self):
        self.assertEqual(self.process('''
            $font($size=2){
              font-family: Arial, sans-serif;
              font-size: @expr(15px * $size);
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font();
              color: red;
            }

            h3{
              $font();
              color: green;
            }
            '''), 'h2,h3{font-family:Arial,sans-serif;font-size:30px;}h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{color:red;}h3{color:green;}')


    def test_param_transparent_units(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: @expr(15px * $size);
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(2px);
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:30px;color:red;}')


    def test_param_mixed_units(self):
        import jasy.style.process.Operation as Operation

        def wrapper():
            self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: @expr(15px * $size);
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(3rem);
              color: red;
            }
            ''')

        self.assertRaises(Operation.OperationError, wrapper)


    def test_param_with_compution(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: @expr(15px * $size);
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(1+1.5);
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:37.5px;color:red;}')


    def test_param_with_mixed_compution(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: @expr(15px * $size);
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font( 2 + 3px );
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:75px;color:red;}')


    def test_param_uses_extend(self):
        self.assertEqual(self.process('''
            $arial{
              font-family: Arial, sans-serif;
            }

            $font($size){
              $arial;
              font-size: @expr(15px * $size);
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(2);
              color: red;
            }
            '''), 'h1,h2{font-family:Arial,sans-serif;}h1{font-size:45px;color:blue;}h2{font-size:30px;color:red;}')


    def test_param_name_conflicts(self):
        self.assertEqual(self.process('''
            $style($size, $color){
              font-size: @expr(15px * $size);
              color: $color;
            }

            h1{
              $color = yellow;
              $style(3, blue);
              background: $color;
            }
            '''), 'h1{font-size:45px;color:blue;background:yellow;}')


    def test_param_name_conflicts_default_ignore(self):
        self.assertEqual(self.process('''
            $style($size, $color=red){
              font-size: @expr(15px * $size);
              color: $color;
            }

            h1{
              $color = yellow;
              $style(3, blue);
              background: $color;
            }
            '''), 'h1{font-size:45px;color:blue;background:yellow;}')


    def test_param_name_conflicts_default_use(self):
        self.assertEqual(self.process('''
            $style($size, $color=red){
              font-size: @expr(15px * $size);
              color: $color;
            }

            h1{
              $color = yellow;
              $style(3);
              background: $color;
            }
            '''), 'h1{font-size:45px;color:red;background:yellow;}')


    def test_param_name_default_from_outer(self):
        self.assertEqual(self.process('''
            $titleColor = orange;

            $style($size, $color=$titleColor){
              font-size: @expr(15px * $size);
              color: $color;
              border-bottom: 1px solid $titleColor;
            }

            h1{
              $style(3);
            }
            '''), 'h1{font-size:45px;color:orange;border-bottom:1px solid orange;}')


    def test_wrong_place_call(self):
        import jasy.style.parse.Parser as Parser

        def wrapper():
            self.process('''
            $style($color){
              color: $color;
            }

            h1{
              color: $style(red);
            }
            ''')

        self.assertRaises(Parser.ParseError, wrapper)


    def test_wrong_place_variable(self):
        import jasy.style.process.Executer as Executer

        def wrapper():
            self.process('''
            $style(){
              color: red;
            }

            h1{
              color: $style;
            }
            ''')

        self.assertRaises(Executer.ExecuterError, wrapper)


    def test_double(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: $size;
            }

            $big($size=30px){
              $font($size);
              text-transform: uppercase;
            }

            $small($size=15px){
              $font($size);
              text-transform: lowercase;
            }

            h1{
              $big;
              color: blue;
            }

            h2{
              $small(10px);
              color: red;
            }

            p{
              $font(15px);
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:30px;text-transform:uppercase;color:blue;}h2{font-family:Arial,sans-serif;font-size:10px;text-transform:lowercase;color:red;}p{font-family:Arial,sans-serif;font-size:15px;}')


    def test_content_simple(self):
        self.assertEqual(self.process('''
            $icon($align){
              &::before{
                display: inline-block;
                vertical-align: $align;
                @content;
              }
            }

            h1{
              $icon(left) < {
                margin-right: 2px;
              }
            }

            p{
              $icon(top) < {
                margin-right: 4px;
              }
            }
            '''), 'h1::before{display:inline-block;vertical-align:left;margin-right:2px;}p::before{display:inline-block;vertical-align:top;margin-right:4px;}')


    def test_content_none(self):
        self.assertEqual(self.process('''
            $icon(){
              &::before{
                display: inline-block;
                @content;
              }
            }

            h2{
              $icon;
              color: blue;
            }
            '''), 'h2::before{display:inline-block;}h2{color:blue;}')


    def test_content_complex(self):
        self.assertEqual(self.process('''
            $icon(){
              &::before{
                content: "u1929";
                font-family: Icons;
                width: 22px;
                height: 22px;
                display: inline-block;

                @content;
              }
            }

            h1{
              $icon() < {
                margin-right: 2px;
                margin-top: 1px;
              }
            }

            h2{
              $icon();

              color: blue;
            }
            '''), 'h1::before,h2::before{content:"u1929";font-family:Icons;width:22px;height:22px;display:inline-block;}h1::before{margin-right:2px;margin-top:1px;}h2{color:blue;}')


    def test_content_double(self):
        self.assertEqual(self.process('''
            $virtual(){
              &::before{
                @content;
              }

              &::after{
                @content;
              }
            }

            h1{
              $virtual() < {
                content: "|";
              }
            }
            '''), 'h1::after{content:"|";}h1::before{content:"|";}')


    def test_content_with_param(self):
        self.assertEqual(self.process('''
            $icon(){
              &::before{
                content: "u1929";
                font-family: Icons;
                width: 22px;
                height: 22px;
                display: inline-block;

                @content;
              }
            }

            h1{
              $icon(x) < {
                margin-right: 2px;
                margin-top: 1px;
              }
            }
            '''), 'h1::before{content:"u1929";font-family:Icons;width:22px;height:22px;display:inline-block;margin-right:2px;margin-top:1px;}')


    def test_content_with_param_double(self):
        self.assertEqual(self.process('''
            $virtual($width, $height){
              &::before{
                width: $width;
                height: $height;

                @content;
              }

              &::after{
                width: $width;
                height: $height;

                @content;
              }
            }

            h1{
              $virtual(24px, 30px) < {
                content: "|";
              }
            }
            '''), 'h1::before{width:24px;height:30px;content:"|";}h1::after{width:24px;height:30px;content:"|";}')


    def test_content_mediaquery_case(self):
        self.assertEqual(self.process('''
            $respond-to($media) {
              @if $media == "small" {
                @media only screen and (max-width: 480px) {
                  @content;
                }
              }
              @elif $media == "medium" {
                @media only screen and (min-width: 481px) and (max-width: 768px) {
                  @content;
                }
              }
              @elif $media == "large" {
                @media only screen and (min-width: 769px) {
                  @content;
                }
              }
            }

            $respond-to("small") < {
              h1{
                font-size: 20px;
              }
            }

            $respond-to("medium") < {
              h1{
                font-size: 25px;
              }
            }

            $respond-to("large") < {
              h1{
                font-size: 30px;
              }
            }
        '''), '@media only screen and (max-width:480px){h1{font-size:20px;}}@media only screen and (min-width:481px) and (max-width:768px){h1{font-size:25px;}}@media only screen and (min-width:769px){h1{font-size:30px;}}')


    def test_local_override(self):
        self.assertEqual(self.process('''
            $icon(){
              &::after{
                content: "u1929";
                font-family: Icons;
              }
            }

            h1{
              $icon($size) {
                margin-right: $size;
                margin-top: @expr($size/2);
              }

              $icon(2px);
            }
            '''), 'h1{margin-right:2px;margin-top:1px;}')


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

