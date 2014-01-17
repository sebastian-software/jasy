#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013-2014 Sebastian Werner
#

from jasy import UserError
import jasy.core.Console as Console

# Make PIL (native module) optional
try:
    from PIL import Image
    from PIL import ImageDraw
    Console.debug("Using Pillow (PIL)")

except ImportError as err1:

    Image = None
    ImageDraw = None
    Console.debug("No support for Pillow (PIL)!")

class SpriteSheet():

    def __init__(self, packer, blocks):

        self.packer = packer
        self.width = packer.root.w
        self.height = packer.root.h
        self.blocks = blocks

        self.area = self.width * self.height
        self.usedArea = sum([s.w * s.h for s in blocks])
        self.used = (100 / self.area) * self.usedArea


    def __len__(self):
        return len(self.blocks)


    def export(self):

        data = {}

        for block in self.blocks:

            info = block.toJSON()
            data[block.image.relPath] = info

            for d in block.duplicates:
                data[d.relPath] = info

        return data


    def write(self, filename, debug=False):

        if Image is None:
            raise UserError("Missing Python PIL which is required to create sprite sheets!")

        img = Image.new('RGBA', (self.width, self.height))
        draw = ImageDraw.Draw(img)

        # Load images and pack them in
        for block in self.blocks:
            res = Image.open(block.image.src)

            x, y = block.fit.x, block.fit.y

            img.paste(res, (x, y))
            del res

            if debug:
                x, y, w, h = block.fit.x, block.fit.y, block.w, block.h
                draw.rectangle((x, y , x + w , y + h), outline=(255, 0, 0, 255))

        if debug:
            for i, block in enumerate(self.packer.getUnused()):
                x, y, w, h = block.x, block.y, block.w, block.h
                draw.rectangle((x, y , x + w , y + h), fill=(255, 255, 0, 255))

        img.save(filename)

