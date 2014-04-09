#!/usr/bin/env python3

import sys
import os
import unittest
import logging
import pkg_resources
import tempfile

# Extend PYTHONPATH with local 'lib' folder
jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir))
sys.path.insert(0, jasyroot)

import jasy.asset.ImageInfo as ImageInfo



class Tests(unittest.TestCase):


    def createGIF(self, path):
        filePath = os.path.join(path, "giffile.gif")
        handle = open(filePath, mode="wb")
        # x: 16; y: 16
        handle.write(
            b'GIF89a\x10\x00\x10\x00\xe6l\x00\x00\x00\xb5\xff\xff\xff\x01\x00\x00\x02\x05\x00\x00\x00 \x03\x00\x00\x01\x01\x00\x00\x00\'\xca\xc9\xcf\x00\x00I\x04\x00\x00\x00\x00"\x00\x00\x1c\n\x0c\x1b\r\x08\x0c\x00\x00\t\x05\x00\'\x00\x00G\x00\x00:\x00\x00)\x01\x00\x02\x00\x00S\xf7\xfc\xff\xcf\xcf\xd9\x00\x02\x00\x00\x00>\xf4\xf5\xff\x04\x07\x00\x00\x00V\x00\x00\x1e\xbf\xc6\xb4\xb3\xb0\xc3\x00\x02\x12\x01\x00C\xfc\xfc\xff\x00\x00Y\xfb\xfe\xff\xf0\xf3\xff\x03\x02<\x04\t&\xd5\xd4\xd2\xfb\xff\xf6\x17\x14\r\xfe\xff\xff\xc5\xc7\xbc\xc7\xc9\xb3\xd0\xcd\xe8\x02\x03;\xbd\xbc\xc4\xba\xbc\xaf\xcc\xcf\xbe\xfe\xfa\xff\xc3\xc4\xbf\xfc\xf9\xff\xfc\xfe\xf9\xf4\xf7\xff\xd1\xd1\xdb\xf6\xf4\xff\xdb\xdc\xd6\xb7\xb4\xbf\x00\x00\x19\x0c\x06"\xc9\xc3\xf3\xca\xc9\xdb\x00\x05\'\x01\x00,\xcc\xcd\xc8\x00\x00c\x02\x00F\x00\x005\x04\x04\x06\xbb\xbd\xb2\x05\x00\\\x0b\x07\x04\xfc\xff\xff\x00\x00L\x00\x01\x00\xf0\xf2\xff\xda\xe2\xd3\xfb\xff\xfa\x00\x00\\\x07\x01\'\xdb\xde\xcd\x03\x01\x00\x00\x00,\x00\x02\x18\x01\x03\x02\x00\x00\x04\xb5\xb3\xc8\xda\xe0\xd4\x00\x00#\xb5\xb8\xb1\x07\x02<\xfc\xff\xf8\xfc\xfe\xff\x0e\x08P\x00\x00\x00\x00\x00+\x03\x00\x07\xbe\xbe\xbc\x00\x00Q\x04\x06\x00\xfc\xfa\xff\x00\x00\x13\x04\x002\x01\x00\x0e\xfa\xfa\xff\xc8\xc8\xc0\xf2\xf7\xd7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00l\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x07\xb3\x80l\x82l\x03\x85W\r\r\x0fL\x1b\x18\x83\x83e-G\x17X?8c:F\x8e\x82\x024+j^7J6[V`*\x8eg.\x1a\x16O)N]Y\x1eRSb=\x07E\x19D!/\x07\x0b\'\x1d\x04Z<\x14T\x00\xc6\xc7\xc8\xc8Q&\x00\x01\xce\xcd\xc6\x01\xd1\xceA\x0c\xd0\xd2\xcf\xd8\xc7\x04 \xcd\xd9\xde\xd7\x01\x04U\xd0\xd1\xe6\xd2\xcda@\xe5\xe5\xe8\xce\x01\x13\\\xc9\xf3\xc7\x0c\x10h\x12KPC#d\t\x11\t\x90T\xe0\xf0%\x8d\xa3\x05>j\x88(A\xa2\x89\x99\x1c3>\x14p\xe4`\x07\x02\x162b\x08A\x00\x03\xc5\x1a\x05\x8e\x14$)P\xc0\x80\x01\x01(\x05\x18`\x13\x08\x00;')
        handle.close()
        return filePath

    def createPNG(self, path):
        filePath = os.path.join(path, "pngfile.png")
        handle = open(filePath, mode="wb")
        # x: 16; y: 16
        handle.write(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x03\x00\x00\x00(-\x0fS\x00\x00\x00\x07tIME\x07\xd4\x07\x02\n&,\xa1\xc3\x8a\x13\x00\x00\x00\tpHYs\x00\x00\x0b\x12\x00\x00\x0b\x12\x01\xd2\xdd~\xfc\x00\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00\x01\x98PLTE\xfb\xfb\xfb\x94\x94\xad\xc6\xc6\xd5\xf0\xf0\xf4\xe8\xe8\xee\xe6\xe6\xed\xe4\xe4\xeb\xe0\xe0\xe9\xdf\xdf\xe8\xdc\xdc\xe5\xda\xda\xe4\xd7\xd7\xe2\xf3\xf3\xf6\xe7\xe7\xee\xe5\xe5\xec\xe1\xe1\xe9\xdb\xdb\xe5mnnvc`\x94\x8a\x89\xa6\xa8\xa9\xb5\xb5\xb4\xa4\xa3\xa4\x8e\x8e\x8f\x80\x80\x80rrr__aXZq\x96\x95\x95\xb4pc\xd3\xbb\xb2\xdb\xe0\xe1\xd7\xd7\xd7\xc6\xc6\xc5\xb3\xb2\xb2\xa8\xa8\xa8\x95\x95\x95\x86\x86\x86OQf\xb4\xb6\xb4\xec\x8f\x7f\xe9\xab\xa3\xf3\xfc\xfe\xdf\xdf\xdf\xce\xce\xcd\xc7\xc7\xc7\xb6\xb4\xb5\xa1\x9f\xa0\x94\x94\x94]_u\xd9\xd9\xe3\xd6\xd6\xe1\xb7\xc1\xc3\xe0\x9a\x90\xcega\xf3\xef\xef\xc1\xd2\xdf\x8a\x9a\xad\xc1\xbd\xbc\x92\x9a\x98y~~\x8c\x89\x8b_`u\xba\xb6\xb3\xe6t\\\xbe72\xe5\xd4\xd5\x8d\xce\xe4Kx\xa3\x9b\x9f\xa3w\xa7r@}Mu{z_`v\xd4\xd4\xe0\xd2\xd2\xde\xbb\x85}\xed[:\xc56*\xca\x97\x9cn\xcd\xeb4\x85\xb8x\x7f\x97|\xbcg8\xa16Mp]__v\xd1\xd1\xdd\xce\xce\xdb\xc1}s\xf3\x91n\xdcN;\x9e@Lb\xc3\xe3=\x98\xc6DZ\x8a\xa0\xc5\x9ab\xbb[8yNTUj\xcb\xcb\xd9\xc8\xc8\xd6\xafZY\xf7\xca\xb7\xf4\x8cp\xafCG\x98\xd5\xea\\\xba\xde>q\x9d\xbf\xd5\xc3\x9f\xd7\x96@\\nORv\xd0\xd0\xdc\xc4\xc4\xd3\xc2\xc2\xd1\xccb`\xc2@;\xbc\x88\x93\x8c\xc4\xdbQ\xb4\xda\xa8\xca\xd9\xd3\xe3\xca\x91\xc5\x8e\xa6\xb1\xb0\xcd\xcd\xda\xbf\xbf\xd0\xfb\xfb\xfc\xf8\xf8\xfa\xf5\xf5\xf8\xee\xee\xf2\xed\xed\xf2\xc9\xc9\xd7\xf4\xf4\xf7\xea\xea\xf0\xde\xde\xe7\xe6\xf1\xac\xf6\x00\x00\x00\x01tRNS\x00@\xe6\xd8f\x00\x00\x00\xd1IDATx\xdac````\x82\x02F\x06(`\xaaohmjkg\x87\x8b\x00\x05\x1a\x99\x9b\xf9\xd9\x99Z\x18\x91\x04\x9a\xd8\xd8\x19\x81\x00\xc8-)-+\xaf\xa8\xac\xaa\xae\xe1\x10\xa8\xad\x03\n\xa4\xa5gdfe\xe7\xe4\xe6\xe5\x17\x14\x16\x15\x03\x05"\xa3\xa2cb\xe3\xe2\x13\x12\x93\x92SRA\xc6\xfa\xf8\xfa\xf9\x07\x04\x06\x05\x87\x84\x86y\x87G\x00\x05\xec\x1d\x1c\x9d\x9c]\\\xdd\xdc=<\x8d\xbd\xbc\x81\x02&\xa6f\xe6\x16\x96V\xd66\xb6v\\\xdc\xc6@\x01u\rM-m\x1d]=}\x03C\x01#\x90\x80\x8c\xac\x9c\xbc\x82\xa2\x92\xb2\x8a\xaa\x1a\'\x177P@PHXDTL\\BRJ\x1a"\x00r)\x0f\x0b/\x1f\x1b?\x87\x00\\\x80\x99\x85\x85\x95\x8d\x9d\x03\xae\x82\x11\t0\x00\x00\xcc\x16(\x9e^\xe8\x01\xfd\x00\x00\x00\x00IEND\xaeB`\x82')
        handle.close()
        return filePath

    def createJPG(self, path):
        filePath = os.path.join(path, "jpgfile.jpg")
        handle = open(filePath, mode="wb")
        # x: 32; y: 32
        handle.write(
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x02\x00\x00d\x00d\x00\x00\xff\xec\x00\x11Ducky\x00\x01\x00\x04\x00\x00\x00<\x00\x00\xff\xee\x00\x0eAdobe\x00d\xc0\x00\x00\x00\x01\xff\xdb\x00\x84\x00\x06\x04\x04\x04\x05\x04\x06\x05\x05\x06\t\x06\x05\x06\t\x0b\x08\x06\x06\x08\x0b\x0c\n\n\x0b\n\n\x0c\x10\x0c\x0c\x0c\x0c\x0c\x0c\x10\x0c\x0e\x0f\x10\x0f\x0e\x0c\x13\x13\x14\x14\x13\x13\x1c\x1b\x1b\x1b\x1c\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x01\x07\x07\x07\r\x0c\r\x18\x10\x10\x18\x1a\x15\x11\x15\x1a\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\x1f\xff\xc0\x00\x11\x08\x00 \x00 \x03\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x80\x00\x00\x03\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x06\x07\x04\x02\x08\x01\x00\x02\x03\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x04\x00\x03\x06\x01\x05\x10\x00\x02\x02\x01\x03\x03\x04\x03\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x11\x00!\x05\x12\x13\x061Q"\x07A2\x14qB\x11\x00\x01\x02\x04\x04\x04\x05\x05\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x11!\x03\x041AQ\x12"B\x05\x06\xf0a\xa12\x13q\x81\x91\xb1\xc1\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xaaV\xfb[\xc8n\xf26\xe8S\xa9L\xcbQ\x1aI\x1aN\xf0R\x16E\x8b\xfe:\xf1\xf2pIl*\x8c\x96 \ry\xc2\xed\xc4\x90\x00\x92\xd9\xd4\xed\xca\x14\xe9\xb5\xefs\xe0\xe3\tm\xd0\x9c\xe1\xa6S&@E.V\xf2o\'\xb74\x0b^\xc8\x92Y\xd29%\x8cOm\x9a\x1e\xfdG\xbb\x12\xb2\xac$\xbb<Q6\x04]{\xed\xa8/\x1ep\r\xf5\xd2> \x8e\xa7nZ\xb0\x12\xe7T\x00\x129\'\xb5\xe1\x86\x13\x90\x0e#\xdd\xb6SA(}\xb5\xcfI\xe55xt\x92Pd\xb1,rJ&\x9b\x04A\x1c\x92\x92\x11\xd5\x1b\xe5\xda\xc6\x19A\xdfq\xa2\xb7\xbcuG\xed *z\xcfn\xd1\xb4\xb6\x15\x9a\xe7\x12H\x91\xdb\x9f\xd3\xf8a\xe6\xbd\x0b^\xd4\xf1X\x14\xeen\xed\x9e\xc4\xe0`H\x07\xe0\xfb0\xd3\xeb\x1e\xa4\xf6~\x85\xf2\t&\xbf$~SV8\xef\xf5,\xc8x\xb7rc2\xac\xc1z\x8d\xdf\xc3\xc6\xa7 \x0fM l\x1b9\x99\xadk{\xb6\xa8\r\x1b\x1b\xc1\x84\xce\x85\xbf\xa2Px\xbe\xae\xf3[\xd4\xe1C\xe55b\x8c\xc0"\x02>%\x15\x9a3Y\xab(\x91\x96\xc2\xb4\x85`\x91\x91K\x92W;cDlA\xe6>\x9aA\x03{\xa5\xc0\x93\xf16$\xc7\xdc\xfcw\x07\xcb\x8a\\@\x13\x0csX</\xe99\xe8y\x9b\xde\xb1\xcd\xa5\xb1\xc1\xcaU\xebGT\xc4d\xfe\x8a\x8c\xa0\x96\xfe\x89::{\xde\xc78\xd4\xb6\xb6k\x1e`p]\xeb]r\xad\xcd\xbbC\xda\x00|\xe5\x1c\x89\x1ft\xf6\xfcP\xe2\xec\t\xa8f\xbbDD\x98_\xd4\xf4o\x86\x19\xc1\xd3\xf0YEQo\xd4\xff\x00\x9a\x15\x12r\xf20q\xbc46d\x1drv#\xec@?y$*\x02\xa2\x8fvb\x06\xb8\xf7m\x11W\xdb\xd05^\x1a0\xcc\xe85Bj\xd7\xe4\xeb\x9a\xf6*IR>Q\xe4\x92;\xad4\xc0\xa5\x89\\\xb4\xd2\xc5\xd1\x18f\xea\x8b\xa5\xba7\xca\xa89\x18\xce\xa9k\x1c&1\xcdz5.h:-qq\xa7\xcb\x016\xc0@c\xaf0\xcdgn[\x90\xb4\xd2\xa5\xca\xd1G\x98\xe5)5y;\xb1\x16BQ\x94>\x06\xe1\x81\xf5\xc1\xdb\xd3V\xb1\xce\xc0\x84\x9d\xc5*!\xbb\xa9\xb8\xbay\x88\x15OoC\xa2I\xa9\x9bs^%^\xe4\x13[\x96\xeb_\xa9\x14p\xb4\x06\x95\xd7\x8a9#^\x92T\xa4\x05I\xdc\xee\x18\x8fm\x0e\xc1\x18\xa6\x05\xd3\x85?\x8cH\x1f\xca\x9c\xdb\xafg\xfa\x9ax/JC\xda\x96\xf1H\xaa\xf2\x95\xb1-\x90\xe2\xc2\x0e\xdc\x1b\x99\x15\xc2wve\x00\xe0|\x8e\x8e)u\xcf\x8f\xc1\xcc\xa71U&\xb9rx:\xe4\xcc\x0b\r\xe5I\'\x98\xb1i\\K\x08@$/\x92\x99\n\xac:\x81\xdd\xb5\xd8\xa8\xbf\xff\xd9')
        handle.close()
        return filePath


    def test_img_file_classes(self):
        tempdir = tempfile.TemporaryDirectory().name
        os.makedirs(tempdir)
        gifpath = self.createGIF(tempdir)
        pngpath = self.createPNG(tempdir)
        jpgpath = self.createJPG(tempdir)

        gif = ImageInfo.GifFile(gifpath)
        png = ImageInfo.PngFile(pngpath)
        jpg = ImageInfo.JpegFile(jpgpath)

        self.assertTrue(gif.verify())
        self.assertEqual(gif.type(), 'gif')
        self.assertEqual(gif.size(), (16, 16))

        self.assertTrue(png.verify())
        self.assertEqual(png.type(), 'png')
        self.assertEqual(png.size(), (16, 16))

        self.assertTrue(jpg.verify())
        self.assertEqual(jpg.type(), 'jpeg')
        self.assertEqual(jpg.size(), (32, 32))


    def test_type_correction(self):
        tempdir = tempfile.TemporaryDirectory().name
        os.makedirs(tempdir)
        gifpath = self.createGIF(tempdir)
        pngpath = self.createPNG(tempdir)
        jpgpath = self.createJPG(tempdir)

        jpg = ImageInfo.GifFile(gifpath)
        gif = ImageInfo.PngFile(pngpath)
        png = ImageInfo.JpegFile(jpgpath)

        self.assertTrue(gif.verify())
        self.assertEqual(gif.type(), 'png')
        self.assertEqual(gif.size(), (16, 16))

        self.assertTrue(png.verify())
        self.assertEqual(png.type(), 'jpeg')
        self.assertEqual(png.size(), (32, 32))

        self.assertTrue(jpg.verify())
        self.assertEqual(jpg.type(), 'gif')
        self.assertEqual(jpg.size(), (16, 16))


    def test_img_info_class(self):
        tempdir = tempfile.TemporaryDirectory().name
        os.makedirs(tempdir)
        gifpath = self.createGIF(tempdir)
        pngpath = self.createPNG(tempdir)
        jpgpath = self.createJPG(tempdir)

        gifInfo = ImageInfo.ImgInfo(gifpath)
        pngInfo = ImageInfo.ImgInfo(pngpath)
        jpgInfo = ImageInfo.ImgInfo(jpgpath)

        self.assertEqual(gifInfo.getSize(), (16, 16))
        self.assertEqual(pngInfo.getSize(), (16, 16))
        self.assertEqual(jpgInfo.getSize(), (32, 32))

        self.assertEqual(gifInfo.getInfo(), (16, 16, 'gif'))
        self.assertEqual(pngInfo.getInfo(), (16, 16, 'png'))
        self.assertEqual(jpgInfo.getInfo(), (32, 32, 'jpeg'))




if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)
