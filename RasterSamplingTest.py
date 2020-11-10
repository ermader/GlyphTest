"""\
Raster Sampling Tests

Created on October 26, 2020

@author Eric Mader
"""

from os.path import basename
from sys import argv, exit, stderr
import math
import logging
import statistics
import CharNames  # From UnicodeData...
from GlyphTest import GTFont
from Bezier import Bezier, BOutline, drawOutline
import BezierUtilities as buitls
from SegmentPen import SegmentPen
from UFOFont import UFOFont
import PathUtilities
import ContourPlotter
from TestArgumentIterator import TestArgs
import TextUtilities

class RasterSamplingTestArgs(TestArgs):

    boundsTypes = {"typographic": (True, False), "glyph": (False, True), "both": (True, True)}

    def __init__(self, argumentList):
        self.typoBounds = self.glyphBounds = False
        TestArgs.__init__(self, argumentList)

    def processArgument(self, argument, arguments):
        if argument == "--bounds":
            boundsType = arguments.nextExtra("bounds")
            if boundsType in self.boundsTypes.keys():
                self.typoBounds, self.glyphBounds = self.boundsTypes[boundsType]
        else:
            TestArgs.processArgument(self, argument, arguments)

def splitCurve(curve, splits):
    p1, p2, p3 = curve.controlPoints
    q1 = p1
    r3 = p3
    q2 = PathUtilities.midpoint([p1, p2])
    r2 = PathUtilities.midpoint([p2, p3])
    q3 = r1 = PathUtilities.midpoint([q2, r2])
    q = Bezier([q1, q2, q3])
    r = Bezier([r1, r2, r3])

    if q.direction != Bezier.dir_mixed:
        splits.append(q)
    else:
        splitCurve(q, splits)

    if r.direction != Bezier.dir_mixed:
        splits.append(r)
    else:
        splitCurve(r, splits)

def sortByP0(list):
    list.sort(key=lambda b: b.controlPoints[0][0])

def curvesAtY(curveList, y):
    return list(filter(lambda curve: curve.boundsRectangle.crossesY(y), curveList))

def intersection(curve, raster):
    if curve.order == 1:
        return buitls.lli(curve.controlPoints, raster)

    roots = curve.roots(raster)
    return curve.get(roots[0])

def leftmostIntersection(curves, raster):
    leftmost = (65536, 65536)

    for curve in curves:
        ip = intersection(curve, raster)
        if ip[0] < leftmost[0]:
            leftmost = ip

    return leftmost

def unzipPoints(points):
    xs = []
    ys = []

    for x, y in points:
        xs.append(x)
        ys.append(y)

    return xs, ys

def bestFit(points):
    xs, ys = unzipPoints(points)
    n = len(points)
    xbar = statistics.mean(xs)
    ybar = statistics.mean(ys)

    numer = sum([x * y for x, y in points]) - n * xbar * ybar
    denom = sum([x**2 for x in xs]) - n * xbar**2

    if denom == 0: return math.inf, math.inf

    b = numer/denom
    a = ybar - b*xbar
    return a, b, xbar, ybar


def main():
    argumentList = argv
    args = None
    programName = basename(argumentList.pop(0))
    if len(argumentList) == 0:
        print(__doc__, file=stderr)
        exit(1)
    try:
        args = RasterSamplingTestArgs(argumentList)
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    if args.fontFile.endswith(".ufo"):
        font = UFOFont(args.fontFile)
    else:
        font = GTFont(args.fontFile, fontName=args.fontName)

    fullName = font.fullName
    if fullName.startswith("."): fullName = fullName[1:]

    level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=level)
    logger = logging.getLogger("raster-sampling-test")

    glyph = args.getGlyph(font)
    glyphName = glyph.name()
    charCode = font.unicodeForName(glyphName)
    charInfo = f"U+{charCode:04X} {CharNames.CharNames.getCharName(charCode)}"

    pen = SegmentPen(font.glyphSet, logger)
    font.glyphSet[glyph.name()].draw(pen)
    contours = pen.contours
    outline = BOutline(contours)
    outlineBounds = outline.boundsRectangle
    upList = []
    downList = []
    flatList = []
    mixedList = []

    ascent = font.typographicAscender
    descent = font.typographicDescender
    advance = glyph.glyphMetric("advanceWidth")
    typoBounds = PathUtilities.GTBoundsRectangle((0, descent), (advance, ascent))

    for bContour in outline.bContours:
        for curve in bContour.beziers:
            if curve.direction == Bezier.dir_up: upList.append(curve)
            elif curve.direction == Bezier.dir_down: downList.append(curve)
            elif curve.direction == Bezier.dir_flat: flatList.append(curve)
            else: mixedList.append(curve)

    sortByP0(upList)
    sortByP0(downList)
    sortByP0(flatList)

    print("up list:")
    for b in upList: print(b.controlPoints)

    print("\ndown list:")
    for b in downList: print(b.controlPoints)

    print("\nflat list:")
    for b in flatList: print(b.controlPoints)

    if len(mixedList) > 0:
        print("\nmixed list:")
        for b in mixedList:
            print(b.controlPoints)

            # splits = []
            # splitCurve(b, splits)
            #
            # for s in splits: print(f"    {s.controlPoints}")
        print()

    cp = ContourPlotter.ContourPlotter(typoBounds.union(outlineBounds).points)

    # Make room for two lines in the content margins
    cp._contentMargins.top *= 2
    cp._contentMargins.bottom *= 2

    # Make sure the content margins are wide enough to
    # hold the label strings.
    ctFont = TextUtilities.ctFont(cp.labelFont, cp.labelFontSize)
    fullNameWidth = TextUtilities.stringWidth(fullName, ctFont)
    charInfoWidth = TextUtilities.stringWidth(charInfo, ctFont)
    labelWidth = max(fullNameWidth, charInfoWidth)
    if labelWidth > typoBounds.width:
        margin = (labelWidth - typoBounds.width) / 2
        cp._contentMargins.left = margin
        cp._contentMargins.right = margin
    else:
        margin = cp._contentMargins.left

    cp.pushStrokeAttributes( dash="2,4")
    if args.typoBounds:
        cyan = PathUtilities.GTColor.fromName("cyan")
        cp.drawContours([typoBounds.contour], color=cyan)
        cp.drawPointsAsSegments([(0, 0), (advance, 0)], color=cyan)
    if args.glyphBounds:
        cp.drawContours([outlineBounds.contour], color=PathUtilities.GTColor.fromName("magenta"))
    cp.popStrokeAtributes()

    drawOutline(cp, outline)

    cp.drawText(typoBounds.width / 2 + margin, cp._labelFontSize * 2, "center", fullName)
    cp.drawText(typoBounds.width / 2 + margin, cp._labelFontSize / 4, "center", charInfo)

    rasters = []
    height = outlineBounds.height
    lowerBound = round(height * .30)
    upperBound = round(height * .70)
    interval = round(height * .02)
    left, _, right, _ = typoBounds.union(outlineBounds).points
    for y in range(lowerBound, upperBound, interval):
        raster = [(left, y), (right, y)]

        p1 = leftmostIntersection(curvesAtY(upList, y), raster)
        p2 = leftmostIntersection(curvesAtY(downList, y), raster)
        rasters.append([p1, p2])
        cp.drawPointsAsSegments(raster, color=PathUtilities.GTColor.fromName("red"))

    midpoints = []
    widths = []
    for raster in rasters:
        midpoint = PathUtilities.midpoint(raster)
        midpoints.append(midpoint)
        widths.append(PathUtilities.length(raster))
        cp.drawPointsAsCircles(raster, 4, [PathUtilities.GTColor.fromName("blue")])
        cp.drawPointsAsCircles([midpoint], 4, [PathUtilities.GTColor.fromName("green")])

    a, b, xbar, ybar = bestFit(midpoints)
    # y = a + bx, so x = (y-a)/b
    my0 = outlineBounds.bottom
    myn = outlineBounds.top
    cp.pushStrokeAttributes(width=2, color=PathUtilities.GTColor.fromName("green"))

    if a != math.inf:
        line = [((my0-a)/b, my0), ((myn-a)/b, myn)]
    else:
        x = midpoints[0][0]
        line = [(x, my0), (x, myn)]

    cp.drawPointsAsSegments(line)
    cp.popStrokeAtributes()

    numer = 0
    denom = 0
    for midpoint in midpoints:
        mx, my = midpoint
        fy = a + (b * mx)
        numer += (fy - ybar) ** 2
        denom += (my - ybar) ** 2
    r2 = numer / denom
    print(f"a = {round(a, 2)}, b = {round(b, 4)}, r\u00B2 = {round(r2, 4)}")

    strokeAngle = round(PathUtilities.slopeAngle(line), 1)
    avgWidth = round(statistics.mean(widths), 2)
    quartiles = statistics.quantiles(widths, n=4, method="inclusive")
    q1 = round(quartiles[0], 2)
    median = round(quartiles[1], 2)
    q3 = round(quartiles[2], 2)
    minWidth = round(min(widths), 2)
    maxWidth = round(max(widths), 2)
    print(f"slope = {round(b, 1)}, angle = {strokeAngle}")
    print(f"widths: min = {minWidth}, Q1 = {q1}, median = {median}, mean = {avgWidth}, Q3 = {q3}, max = {maxWidth}")

    cp.setFillColor(PathUtilities.GTColor.fromName("black"))

    cp.drawText(line[-1][0] + margin, -cp._labelFontSize * 1.5, "center", f"Stroke angle = {strokeAngle}")
    cp.drawText(line[-1][0] + margin, -cp._labelFontSize * 3, "center", f"Mean stroke width = {avgWidth}")

    image = cp.generateFinalImage()

    imageFile = open(f"RasterSamplingTest {fullName}_{glyphName}.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()


if __name__ == "__main__":
    main()
