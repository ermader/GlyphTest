"""\
A simple class to access .ufo fonts

Created on October 14, 2020

@author Eric Mader
"""

from fontTools.ufoLib import glifLib, plistlib
from SegmentPen import SegmentPen

class UFOFont(object):
    def __init__(self, fileName):
        infoFile = open(f"{fileName}/fontinfo.plist", "r", encoding="UTF-8")
        self._fileInfo = plistlib.load(infoFile)
        self._glyphSet = glifLib.GlyphSet(f"{fileName}/glyphs")
        self._unicodes = self._glyphSet.getUnicodes()

    @property
    def fullName(self):
        return self._fileInfo["postscriptFontName"]  # Should also check for full name...

    @property
    def glyphSet(self):
        return self._glyphSet

    def glyphForName(self, glyphName):
        return UFOGlyph(glyphName, self)

    def glyphForIndex(self, index):
        return None

    def glyphForCharacter(self, charCode):
        for name, codes in self._unicodes.items():
            if charCode in codes: return self.glyphForName(name)
        return None

    # Do we really need this?
    def getGlyphContours(self, glyphName, logger):
        glyph = glifLib.Glyph(glyphName, self._glyphSet)
        pen = SegmentPen(self._glyphSet, logger)
        glyph.draw(pen)
        return pen.contours

class UFOGlyph(object):
    def __init__(self, glyphName, font):
        self._font = font
        self._glyph = glifLib.Glyph(glyphName, font.glyphSet)

    def name(self):
        return self._glyph.glyphName

    def draw(self, pen):
        self._glyph.draw(pen)
