#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
# Copyright 2013 Sebastian Werner
#

class Block():

    def __init__(self, w, h, image=False):
        self.w = w
        self.h = h
        self.image = image

        self.fit = None
        self.duplicates = []
        self.area = w * h

    def toJSON(self):
        if self.fit:
            return {
                "left": self.fit.x,
                "top": self.fit.y,
                "width": self.image.width,
                "height": self.image.height,
                "checksum": self.image.checksum
            }

        else:
            return  {
                "left": 0,
                "top": 0,
                "width": self.w,
                "height": self.h,
                "checksum": None
            }

