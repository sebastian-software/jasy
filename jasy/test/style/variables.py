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

$width = 300px;
$height = $width * .5;
$width = 300px, $height = 200px;
$width += 20px;
$content = "Hello" + "World";
$negative = -100px;
$list = 20px 30px;
$listoper = $list * 20;

"""

class Tests(unittest.TestCase):

    def process(self, code):
        callerName = inspect.stack()[1][3][5:]

        tree = Engine.getTree(code, callerName)
        tree = Engine.reduceTree(tree)
        return Engine.compressTree(tree)

    def test_unused(self):
        self.assertEqual(self.process('''
            $width = 300px;
            '''), '')


    def test_condition_redefine(self):
        self.assertEqual(self.process('''
            $width = 300px;

            @if $width > 200{
                $width = 200px;
            }

            h1{
                width: $width;
            }
            '''), 'h1{width:200px;}')


    def test_condition_strcomp(self):
        self.assertEqual(self.process('''
            $color = "red";

            @if $color == "red"{
                $bg = "white";
            } @else {
                $bg = "black";
            }

            h1{
                color: $color;
                background-color: $bg;
            }
            '''), 'h1{color:"red";background-color:"white";}')


    def test_condition_redefine_deep(self):
        self.assertEqual(self.process('''
            $width = 301px;

            @if $width > 200{
                @if $width % 2 == 0{
                    $width = 200px;
                } @else {
                    $width = 199px;
                }
            }

            h1{
                width: $width;
            }
            '''), 'h1{width:199px;}')


    def test_condition_redefine_override(self):
        self.assertEqual(self.process('''
            $width = 300px;

            @if $width > 200{
                $width = 200px;
            }

            $width = 100px;

            h1{
                width: $width;
            }
            '''), 'h1{width:100px;}')


    def test_condition_define_new(self):
        self.assertEqual(self.process('''
            $width = 300px;

            @if $width > 200{
                $height = $width / 2;
            } @else {
                $height = $width * 2;
            }

            h1{
                width: $width;
                height: $height;
            }
            '''), 'h1{width:300px;height:150px;}')


    def test_condition_define_new_override(self):
        self.assertEqual(self.process('''
            $width = 300px;

            @if $width > 200{
                $height = $width / 2;
            } @else {
                $height = $width * 2;
            }

            $width = 75px;

            h1{
                width: $width;
                height: $height;
            }
            '''), 'h1{width:75px;height:150px;}')





    def test_unused_operation(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $height = 200px;
            $size = $width * $height;
            '''), '')

    def test_value_simple(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $height = 200px;

            .box{
              width: $width;
              height: $height;
            }
            '''), '.box{width:300px;height:200px;}')


    def test_value_simple_scope(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $height = 200px;

            .box{
              $width = 40px;
              $height = 20px;

              width: $width;
              height: $height;
            }

            header{
              width: $width;
              height: $height;
            }

            '''), '.box{width:40px;height:20px;}header{width:300px;height:200px;}')


    def test_value_simple_namespaced(self):
        self.assertEqual(self.process('''
            $box.width = 300px;
            $box.height = 200px;

            .box{
              width: $box.width;
              height: $box.height;
            }
            '''), '.box{width:300px;height:200px;}')


    def test_value_simple_multi(self):
        self.assertEqual(self.process('''
            $width = 300px, $height = 200px;

            .box{
              width: $width;
              height: $height;
            }
            '''), '.box{width:300px;height:200px;}')


    def test_value_simple_math(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $height = 200px;

            .box{
              $padding = 10px;
              padding: $padding;
              width: @expr($width - $padding * 2);
              height: @expr($height - $padding * 2);
            }
            '''), '.box{padding:10px;width:280px;height:180px;}')



    def test_define_override(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $width = 400px;

            .box{
              width: $width;
            }
            '''), '.box{width:400px;}')


    def test_define_unary(self):
        self.assertEqual(self.process('''
            $negative = -100px;

            .box{
              left: $negative;
            }
            '''), '.box{left:-100px;}')


    def test_define_color_hex(self):
        self.assertEqual(self.process('''
            $hex = #39FC20;

            .box{
              color: $hex;
            }
            '''), '.box{color:#39FC20;}')


    def test_define_color_hex3(self):
        self.assertEqual(self.process('''
            $hex = #3F2;

            .box{
              color: $hex;
            }
            '''), '.box{color:#3F2;}')


    def test_define_color_rgb(self):
        self.assertEqual(self.process('''
            $rgb = rgb(200, 100, 50);

            .box{
              color: $rgb;
            }
            '''), '.box{color:rgb(200,100,50);}')


    def test_define_multi(self):
        self.assertEqual(self.process('''
            $inner = 20px 10px;

            .box{
              padding: $inner;
            }
            '''), '.box{padding:20px 10px;}')


    def test_define_multi_plus_operation_decl(self):
        self.assertEqual(self.process('''
            $inner = 20px * 3 10px * 2;

            .box{
              padding: $inner;
            }
            '''), '.box{padding:60px 20px;}')


    def test_define_multi_mutation_end(self):
        self.assertEqual(self.process('''
            $inner = 20px 10px;

            .box{
              padding: @expr($inner * 2);
            }
            '''), '.box{padding:40px 20px;}')


    def test_define_multi_mutation_begin(self):
        self.assertEqual(self.process('''
            $inner = 20px 10px;

            .box{
              padding: @expr(.5 * $inner);
            }
            '''), '.box{padding:10px 5px;}')


    def test_define_multi_mutation_plex(self):
        self.assertEqual(self.process('''
            $inner = 20px 10px;
            $outer = 2 3;

            .box{
              padding: @expr($inner * $outer);
            }
            '''), '.box{padding:40px 30px;}')


    def test_define_assignop_plus(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $width += 53;

            .box{
              width: $width;
            }
            '''), '.box{width:353px;}')


    def test_define_assignop_multi(self):
        self.assertEqual(self.process('''
            $width = 20px;
            $columns = 12;

            $width *= $columns;

            .box{
              width: $width;
            }
            '''), '.box{width:240px;}')


    def test_math_operation(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $width = $width * 1.3;
            $width *= .5 + .213;

            .box{
              width: $width;
            }
            '''), '.box{width:278.07px;}')


    def test_math_operation_percent(self):
        self.assertEqual(self.process('''
            $columns = 12;
            $width = 100% / $columns;
            $pxwidth = 960px * $width;

            .box{
              width: $width;
              height: $pxwidth;
            }
            '''), '.box{width:8.3333%;height:80px;}')


    def test_string_operation(self):
        self.assertEqual(self.process('''
            $text = "Hello {{name}}.";
            $text += "Welcome to my site!";
            $text = "<p>" + $text + "</p>";

            .box{
              content: $text;
            }
            '''), '.box{content:"<p>Hello {{name}}.Welcome to my site!</p>";}')


    def test_mixed_operation(self):
        self.assertEqual(self.process('''
            $text = "Hello ";
            $text += 42;

            .box{
              content: $text;
            }
            '''), '.box{content:"Hello 42";}')


    def test_nonequal(self):
        self.assertEqual(self.process('''
            $freeuser = true;
            $enabled = !$freeuser;

            .box{
              content: $enabled;
            }
            '''), '.box{content:false;}')


    def test_nonequal_combined(self):
        self.assertEqual(self.process('''
            $freeuser = true;
            $enabled = $freeuser && !false;

            .box{
              content: $enabled;
            }
            '''), '.box{content:true;}')


    def test_nonequal_combined_human(self):
        self.assertEqual(self.process('''
            $freeuser = true;
            $enabled = $freeuser and not false;

            .box{
              content: $enabled;
            }
            '''), '.box{content:true;}')


    def test_nonequal_combined_parens(self):
        self.assertEqual(self.process('''
            $freeuser = true;
            $enabled = $freeuser && (!false and true);

            .box{
              content: $enabled;
            }
            '''), '.box{content:true;}')


    def test_value_operator_math(self):
        self.assertEqual(self.process('''
            $base = 30px;
            $larger = $base * 1.3;
            $smaller = $base * 0.6;
            $reallysmall = $smaller - 10;

            // snap
            $larger = $larger - $larger % 5;

            h1{
              font-size: $larger;
            }

            p{
              font-size: $base;
            }

            small{
              font-size: $smaller;
            }

            footer{
              font-size: $reallysmall;
            }
            '''), 'h1{font-size:35px;}p{font-size:30px;}small{font-size:18px;}footer{font-size:8px;}')


    def test_default_available(self):
        self.assertEqual(self.process('''
            $width = 300px;
            $width ?= 400px;

            .box{
              width: $width;
            }
            '''), '.box{width:300px;}')


    def test_default_new(self):
        self.assertEqual(self.process('''
            $width ?= 400px;

            .box{
              width: $width;
            }
            '''), '.box{width:400px;}')



    def test_variable_usedonly_in_selector(self):
        self.assertEqual(self.process('''
            $align = left;

            .box-$align{
              display: inline-block;
            }
            '''), '.box-left{display:inline-block;}')


    def test_variable_usedonly_in_property(self):
        self.assertEqual(self.process('''
            $edge = left;

            .box{
              margin-$edge: 20px;
            }
            '''), '.box{margin-left:20px;}')


    def test_variable_property(self):
        self.assertEqual(self.process('''
            $align = left;

            .box{
              float: $align;
              margin-${align}: 10px;
              $align: 20px;
              border-color-$align: 1px solid red;
            }
            '''), '.box{float:left;margin-left:10px;left:20px;border-color-left:1px solid red;}')


    def test_variable_selector(self):
        self.assertEqual(self.process('''
            $align = left;

            .text-${align}{
              text-align: ${align};
            }

            .box-$align{
              float: $align;
              display: inline-block;
            }
            '''), '.text-left{text-align:left;}.box-left{float:left;display:inline-block;}')


    def test_variable_selector_complex(self):
        self.assertEqual(self.process('''
            $cell = 4;

            .box:nth-child(${cell}n){
              color: red;
            }
            '''), '.box:nth-child(4n){color:red;}')


    def test_complex_font_setting(self):
        self.assertEqual(self.process('''
            html {
                font: 300 1.125em/1.5 sans-serif;
            }
        '''), 'html{font:300 1.125em / 1.5 sans-serif;}')


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

