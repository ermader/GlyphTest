"""\
Reading glif objects from a UFO font.
Created on September 24, 2020

@author Eric Mader
"""

import ufoLib
import Bezier
import PathUtilities
from ContourPlotter import ContourPlotter

# Add verbose mode to print calls?
class SegmentPen:
    def __init__(self, glyphSet):
        self._contours = []
        self._glyphSet = glyphSet

    def addPoint(self, pt, segmentType, smooth, name):
        raise NotImplementedError

    def moveTo(self, pt):
        self._lastOnCurve = pt

        # This is for glyphs, which are always closed paths,
        # so we assume that the move is the start of a new contour
        self._contour = []
        self._segment = []
        # print(f"moveTo({pt})")

    def lineTo(self, pt):
        segment = [self._lastOnCurve, pt]
        self._contour.append(segment)
        self._lastOnCurve = pt
        # print(f"lineTo({pt})")

    def curveTo(self, *points):
        segment = [self._lastOnCurve]
        segment.extend(points)
        self._contour.append(segment)
        self._lastOnCurve = points[-1]
        # print(f"curveTo({points})")

    def qCurveTo(self, *points):
        segment = [self._lastOnCurve]
        segment.extend(points)

        if len(segment) <= 3:
            self._contour.append(segment)
        else:
            # a starting on-curve point, two or more off-curve points, and a final on-curve point
            startPoint = segment[0]
            for i in range(1, len(segment) - 2):
                p1x, p1y = segment[i]
                p2x, p2y = segment[i + 1]
                impliedPoint = (0.5 * (p1x + p2x), 0.5 * (p1y + p2y))
                self._contour.append([startPoint, segment[i], impliedPoint])
                startPoint = impliedPoint
            self._contour.append([startPoint, segment[-2], segment[-1]])
        self._lastOnCurve = segment[-1]
        # print(f"qCurveTo({points})")

    def beginPath(self):
        raise NotImplementedError

    def closePath(self):
        self._contours.append(self._contour)
        if self._contour[0][0] != self._contour[-1][-1]:
            self._contour.append([self._contour[-1][-1], self._contour[0][0]])
        self._contour = []
        # print("closePath()")

    def endPath(self):
        raise NotImplementedError

    identityTransformation = (1, 0, 0, 1, 0, 0)

    def addComponent(self, glyphName, transformation):
        if transformation != self.identityTransformation:
            xScale, xyScale, yxScale, yScale, xOffset, yOffset = transformation
            m = PathUtilities.GTTransform._matrix(
                a=xScale,
                b=xyScale,
                c=yxScale,
                d=yScale,
                m=xOffset,
                n=yOffset
            )
            t = PathUtilities.GTTransform(m)
        else:
            t = None

        glifString = self._glyphSet.getGLIF(glyphName)
        glyph = ufoLib.glifLib.Glyph(self._glyphSet, "")
        cpen = SegmentPen(self._glyphSet)
        psp = ufoLib.glifLib.PointToSegmentPen(cpen)
        ufoLib.glifLib.readGlyphFromString(glifString, glyph, psp)
        contours = t.applyToContours(cpen.contours) if t else cpen.contours
        self.contours.extend(contours)
        # print(f"addComponent(\"{glyphName}\", {transformation}")

    @property
    def contours(self):
        return self._contours

colorRed = PathUtilities.GTColor.fromName("red")
colorGreen = PathUtilities.GTColor.fromName("green")
colorBlue = PathUtilities.GTColor.fromName("blue")
colorGold = PathUtilities.GTColor.fromName("gold")
colorMagenta = PathUtilities.GTColor.fromName("magenta")
colorCyan = PathUtilities.GTColor.fromName("cyan")
colorYellow = PathUtilities.GTColor.fromName("yellow")
colorBlack = PathUtilities.GTColor.fromName("black")
colorLightGrey = PathUtilities.GTColor.fromName("lightgrey")
colorLightBlue = PathUtilities.GTColor.fromName("lightblue")
colorLightGreen = PathUtilities.GTColor.fromName("lightgreen")

def getGLIFOutline(glyphSet, glyphName):
    glyph = ufoLib.glifLib.Glyph(glyphSet, "")
    glifString = glyphSet.getGLIF(glyphName)
    pen = SegmentPen(glyphSet)
    psp = ufoLib.glifLib.PointToSegmentPen(pen)
    ufoLib.glifLib.readGlyphFromString(glifString, glyph, psp)
    return Bezier.BOutline(pen.contours)


def glifOutlineTest(glyphSet, glyphName, color=None):
    outline = getGLIFOutline(glyphSet, glyphName)
    bounds = outline.boundsRectangle

    cp = ContourPlotter(bounds.points)
    Bezier.drawOutline(cp, outline, color=color)

    cp.pushStrokeAttributes(opacity=0.5)
    cp.drawContours([bounds.contour], colorGreen)
    cp.popStrokeAtributes()

    fontName = glyphSet.dirName.split("/")[-2]

    image = cp.generateFinalImage()
    imageFile = open(f"{fontName}_{glyphName}.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()

def test():
    gsSFNS = ufoLib.glifLib.GlyphSet("/Users/emader/Downloads/SF NS Text Condensed-Regular.ufo/glyphs")
    gsNewYork = ufoLib.glifLib.GlyphSet("/Users/emader/Downloads/NewYork.ufo/glyphs")

    glifOutlineTest(gsSFNS, "a", colorBlue)  # cubic outline
    glifOutlineTest(gsNewYork, "a", colorBlue)  # quadratic outline
    glifOutlineTest(gsNewYork, "j", colorBlue)  # quadratic outline, two components: dotless-j, dot-accent
    glifOutlineTest(gsNewYork, "acircumflexacute", colorBlue) # quddratic outline, two components: a, circumflex-acute
    glifOutlineTest(gsNewYork, "ccedillaacute", colorBlue)  # quadratic outline, three components: c, cedilla, acute
    glifOutlineTest(gsNewYork, "imacron", colorBlue)  # quadratic outline, three components: c, cedilla, acute

if __name__ == "__main__":
    test()
