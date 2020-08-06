"""\
Processing the contours in a glyph outline

Created on August 5, 2020

@author Eric Mader
"""

import math
import PathUtilities

class GTGlyphCoutours(object):
    # This class needs access to Glyph internals that shouldn’t be exposed otherwise.
    # pylint: disable=protected-access

    def __init__(self, glyph):
        self._glyph = glyph
        font = glyph._font
        glyfTable = font['glyf']
        ttGlyph = glyfTable[glyph.name()]

        self._minX = self._minY = 65536
        self._maxX = self._maxY = -65536
        self._contours = []

        coords, endPoints, flags = ttGlyph.getCoordinates(glyfTable)
        coords = coords.copy()

        startPoint = 0
        for endPoint in endPoints:
            self._segments = []
            limitPoint = endPoint + 1
            contour = coords[startPoint:limitPoint]
            contourFlags = [flag & 0x1 for flag in flags[startPoint:limitPoint]]

            contour.append(contour[0])
            contourFlags.append(contourFlags[0])
            startPoint = limitPoint

            while len(contour) > 1:
                firstOnCurve = contourFlags.index(1)
                nextOnCurve = contourFlags.index(1, firstOnCurve + 1)
                self.handleSegment(contour[firstOnCurve:nextOnCurve + 1])
                contour = contour[nextOnCurve:]
                contourFlags = contourFlags[nextOnCurve:]

            self._contours.append(self._segments)

        self._boundsRectangle = PathUtilities.GTBoundsRectangle((self._minX, self._minY), (self._maxX, self._maxY))

    def handleSegment(self, segment):
        for x, y in segment:
            self._minX = min(self._minX, x)
            self._minY = min(self._minY, y)
            self._maxX = max(self._maxX, x)
            self._maxY = max(self._maxY, y)

        if len(segment) <= 3:
            self._segments.append(segment)
        else:
            # a starting on-curve point, two or more off-curve points, and a final on-curve point
            startPoint = segment[0]
            for i in range(1, len(segment) - 2):
                p1x, p1y = segment[i]
                p2x, p2y = segment[i + 1]
                impliedPoint = (0.5 * (p1x + p2x), 0.5 * (p1y + p2y))
                self._segments.append([startPoint, segment[i], impliedPoint])
                startPoint = impliedPoint
            self._segments.append([startPoint, segment[-2], segment[-1]])

    @property
    def contours(self):
        return self._contours

    @property
    def boundsRectangle(self):
        return self._boundsRectangle

    def verticalLines(self):
        """\
        Return a list of all the vertical lines in the given contours.
        """
        v = []
        for contour in self._contours:
            for segment in contour:
                if PathUtilities.isVerticalLine(segment):
                    v.append(segment)

        return v

    def verticalLinesCrossing(self, y):
        """\
        Return a list of all the vertical lines in the given contours that
        span the given y coordinate.
        """
        return list(filter(lambda s: self.crossesY(s, y), self.sortByX(self.verticalLines())))

    def horizontalLines(self):
        """\
        Return a list of all the horizontal lines in the given contours.
        """
        h = []
        for contour in self._contours:
            for segment in contour:
                if PathUtilities.isHorizontalLine(segment):
                    h.append(segment)

        return h

    def horizontalLinesCrossing(self, x):
        """\
        Return a list of all the horizontal lines in the given contours that
        span the given x coordinate.
        """
        return list(filter(lambda s: self.crossesX(s, x), self.sortByY((self.horizontalLines()))))

    def lines(self):
        """\
        Return a list of all the lines in the given contours.
        """
        l = []
        for contour in self._contours:
            for segment in contour:
                if len(segment) == 2:
                    l.append(segment)

        return l

    def linesCrossingY(self, y):
        """\
        Return a list of all the lines in the given contours that
        cross a given y coordinate.
        """
        return list(filter(lambda s: self.crossesY(s, y), self.sortByX(self.lines())))

    @classmethod
    def sortByX(cls, contour):
        """\
        Return a list of all the segments in contour sorted by their x coordinate.
        """
        return sorted(contour, key=lambda s: s[0][0])

    @classmethod
    def sortByY(cls, contour):
        """\
        Return a list of all the segments in contour sorted by their y coordinate.
        """
        return sorted(contour, key=lambda s: s[0][1])

    @classmethod
    def sortByLength(cls, contour, longestFirst=False):
        """\
        Return a list of all the segments in contour sorted by their length.
        """
        return sorted(contour, key=lambda l: PathUtilities.length(l), reverse=longestFirst)

    @classmethod
    def crossesY(cls, line, y):
        """\
        Test if the line crosses the given y coordinate.
        """
        return PathUtilities.GTBoundsRectangle(*line).crossesY(y)

    @classmethod
    def crossesX(cls, line, x):
        """\
        Test if the line crosses the given x coordinate.
        """
        return PathUtilities.GTBoundsRectangle(*line).crossesX(x)

    def verticalStrokeWidth(self, atHeight):
        """\
        Calculate the vertical stroke width of the given contours
        by finding all vertical lines that span a given height,
        and returning the width of a bounds rectangle that encloses
        the first two lines.
        """
        verticals = self.verticalLinesCrossing(atHeight)
        if len(verticals) >= 2:
            vStroke = PathUtilities.GTBoundsRectangle(*verticals[0], *verticals[1])
            return vStroke.width

        return 0  # or maybe None?

    def horizontalStrokeWidth(self, atWidth):
        """\
        Calculate the horizontal stroke width of the given contours
        by finding all horizontal lines that span a given width,
        and returning the height of a bounds rectangle that encloses
        the first two lines.
        """
        horizontals = self.horizontalLinesCrossing(atWidth)
        if len(horizontals) >= 2:
            hStroke = PathUtilities.GTBoundsRectangle(*horizontals[0], *horizontals[1])
            return hStroke.height

        return 0  # or maybe None?

    def italicAngle(self):
        if self._glyph.name() == "colon":  # is it safe to assume the colon glyph will always have this name?
            # use colon method:
            # assumes that the colon glyph has two contours, one for each dot
            lowerDot = self._contours[0]
            upperDot = self._contours[1]
            lowerBounds = PathUtilities.GTBoundsRectangle.fromContour(lowerDot)
            upperBounds = PathUtilities.GTBoundsRectangle.fromContour(upperDot)
            lowerCenter = lowerBounds.centerPoint
            upperCenter = upperBounds.centerPoint
            italicSlope = PathUtilities.slope([lowerCenter, upperCenter])
            return 90.0 - math.degrees(math.atan(italicSlope))
        else:
            lines = self.linesCrossingY(self._boundsRectangle.yFromBottom(0.40))
            linesByLength = PathUtilities.sortByLength(lines, longestFirst=True)
            italicSlope = PathUtilities.slope(linesByLength[0])
            return 90.0 - math.degrees(math.atan(italicSlope))

    def italicStrokeWidth(self):
        lines = self.linesCrossingY(self._boundsRectangle.yFromBottom(0.25))
        midPoint = PathUtilities.midpoint(lines[0])
        perpendicular = PathUtilities.rotateSegmentAbout(lines[0], midPoint)
        intersection = PathUtilities.intersectionPoint(perpendicular, lines[1])
        return PathUtilities.length([midPoint, intersection])


def test():
    from GlyphTest import GTFont

    helveticaNeuePath = "/System/Library/Fonts/HelveticaNeue.ttc"
    helveticaNeueRegularName = "HelveticaNeue"
    helveticaNeueItalicName = "HelveticaNeue-Italic"

    newYorkPath = "/System/Library/Fonts/NewYork.ttf"
    newYorkItalicPath = "/System/Library/Fonts/NewYorkItalic.ttf"

    # removed M, N because the heuristic doesn't find the right stroke:
    # the middle strokes are longer than the side strokes...
    strokeMethodChars = "BDHIJKLPRTbdhijklmnpqrt"

    hnrFont = GTFont(helveticaNeuePath, fontName=helveticaNeueRegularName)
    hnrHGlyph = hnrFont.glyphForCharacter("H")
    hnrpGlyph = hnrFont.glyphForCharacter("p")

    hnrHGlyphContours = GTGlyphCoutours(hnrHGlyph)
    hnrpGlyphContours = GTGlyphCoutours(hnrpGlyph)

    boundsRect = hnrHGlyphContours.boundsRectangle
    upm = hnrFont.unitsPerEm()
    vsw = hnrHGlyphContours.verticalStrokeWidth(boundsRect.yFromBottom(0.25))
    hsw = hnrHGlyphContours.horizontalStrokeWidth(boundsRect.xFromLeft(0.50))

    print(f"vertical stroke width of HelveticaNeue H = {PathUtilities.toMicros(vsw, upm)} micro")
    print(f"horizontal stroke width of HelveticaNeue H = {PathUtilities.toMicros(hsw, upm)} micro")
    print()

    boundsRect = hnrpGlyphContours.boundsRectangle
    vsw = hnrpGlyphContours.verticalStrokeWidth(boundsRect.yFromBottom(0.25))

    print(f"vertical stroke width of HelveticaNeue p = {PathUtilities.toMicros(vsw, upm)} micro")
    print()

    nyFont = GTFont(newYorkPath)
    nyHGlyph = nyFont.glyphForCharacter("H")
    nypGlyph = nyFont.glyphForCharacter("p")

    nyHGlyphContours = GTGlyphCoutours(nyHGlyph)
    nypGlyphContours = GTGlyphCoutours(nypGlyph)

    boundsRect = nyHGlyphContours.boundsRectangle
    upm = nyFont.unitsPerEm()
    vsw = nyHGlyphContours.verticalStrokeWidth(boundsRect.yFromBottom(0.25))
    hsw = nyHGlyphContours.horizontalStrokeWidth(boundsRect.xFromLeft(0.50))

    print(f"vertical stroke width of NewYork H = {PathUtilities.toMicros(vsw, upm)} micro")
    print(f"horizontal stroke width of NewYork H = {PathUtilities.toMicros(hsw, upm)} micro")
    print()


    boundsRect = nypGlyphContours.boundsRectangle
    vsw = nypGlyphContours.verticalStrokeWidth(boundsRect.yFromBottom(0.25))

    print(f"vertical stroke width of NewYork p = {PathUtilities.toMicros(vsw, upm)} micro")
    print()

    hniFont = GTFont(helveticaNeuePath, fontName=helveticaNeueItalicName)
    hniColonGlyph = hniFont.glyphForCharacter(":")
    hniColonGlyphContours = GTGlyphCoutours(hniColonGlyph)
    print(f"italic angle of HelveticaNeueItalic from colon method = {hniColonGlyphContours.italicAngle()}")
    print()

    for char in strokeMethodChars:
        glyph = hniFont.glyphForCharacter(char)
        glyphContours = GTGlyphCoutours(glyph)
        print(f"italic angle of HelveticaNeueItalic {char} from stroke method = {glyphContours.italicAngle()}")
    print()

    hnipGlyph = hniFont.glyphForCharacter("p")
    hnipGlyphContours = GTGlyphCoutours(hnipGlyph)
    isw = hnipGlyphContours.italicStrokeWidth()
    print(f"stroke width of HelveticaNeueItalic p = {PathUtilities.toMicros(isw, hniFont.unitsPerEm())} micro")
    print()

    nyiFont = GTFont(newYorkItalicPath)
    nyiColonGlyph = nyiFont.glyphForCharacter(":")
    nyiColonGlyphContours = GTGlyphCoutours(nyiColonGlyph)
    print(f"italic angle of NewYorkItalic from colon method = {nyiColonGlyphContours.italicAngle()}")
    print()

    for char in strokeMethodChars:
        glyph = nyiFont.glyphForCharacter(char)
        glyphContours = GTGlyphCoutours(glyph)
        print(f"italic angle of NewYorkItalic {char} from stroke method = {glyphContours.italicAngle()}")
    print()

    nyipGlyph = nyiFont.glyphForCharacter("p")
    nyipGlyphContours = GTGlyphCoutours(nyipGlyph)
    isw = nyipGlyphContours.italicStrokeWidth()
    print(f"stroke width of NewYorkItalic p = {PathUtilities.toMicros(isw, nyiFont.unitsPerEm())} micro")
    print()


if __name__ == "__main__":
    test()


