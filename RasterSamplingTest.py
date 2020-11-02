"""\
Raster Sampling Tests

Created on October 26, 2020

@author Eric Mader
"""

from os.path import basename
from sys import argv, exit, stderr
import logging
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

def curveAtY(list, y):
    for curve in list:
        if curve.boundsRectangle.crossesY(y):
            return curve

    return None

def intersection(curve, raster):
    if curve.order == 1:
        return buitls.lli(curve.controlPoints, raster)

    roots = curve.roots(raster)
    return curve.get(roots[0])

def main():
    argumentList = argv
    args = None
    programName = basename(argumentList.pop(0))
    if len(argumentList) == 0:
        print(__doc__, file=stderr)
        exit(1)
    try:
        args = TestArgs.forArguments(argumentList)
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    steps = args.steps

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
    # bounds = outline.boundsRectangle
    upList = []
    downList = []
    flatList = []
    mixedList = []

    ascent = font.fontMetric("OS/2", "sTypoAscender")
    descent = font.fontMetric("OS/2", "sTypoDescender")
    advance = glyph.glyphMetric("advanceWidth")
    bounds = PathUtilities.GTBoundsRectangle((0, descent), (advance, ascent))

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

    cp = ContourPlotter.ContourPlotter(bounds.union(outline.boundsRectangle).points)

    # Make room for two lines in the content margins
    cp._contentMargins.top *= 2
    cp._contentMargins.bottom *= 2

    # Make sure the content margins are wide enough to
    # hold the label strings.
    ctFont = TextUtilities.ctFont(cp.labelFont, cp.labelFontSize)
    fullNameWidth = TextUtilities.stringWidth(fullName, ctFont)
    charInfoWidth = TextUtilities.stringWidth(charInfo, ctFont)
    labelWidth = max(fullNameWidth, charInfoWidth)
    if labelWidth > bounds.width:
        margin = (labelWidth - bounds.width) / 2
        cp._contentMargins.left = margin
        cp._contentMargins.right = margin
    else:
        margin = cp._contentMargins.left

    cp.pushStrokeAttributes(color=PathUtilities.GTColor.fromName("grey"), dash="2,4")
    cp.drawContours([bounds.contour])
    cp.drawPointsAsSegments([(0, 0), (advance, 0)])
    cp.popStrokeAtributes()

    drawOutline(cp, outline)

    cp.drawText(bounds.width / 2 + margin, cp._labelFontSize * 2, "center", fullName)
    cp.drawText(bounds.width / 2 + margin, cp._labelFontSize / 4, "center", charInfo)

    rasters = []
    height = outline.boundsRectangle.height
    lowerBound = round(height * .30)
    upperBound = round(height * .70)
    interval = round(height * .02)
    left, _, right, _ = bounds.points
    oLeft, _, oRight, _ = outline.boundsRectangle.points
    left = min(left, oLeft)
    right = max(right, oRight)
    for y in range(lowerBound, upperBound, interval):
        raster = [(left, y), (right, y)]
        upCurve = curveAtY(upList, y)
        downCurve = curveAtY(downList, y)

        p1 = intersection(upCurve, raster)
        p2 = intersection(downCurve, raster)
        rasters.append([p1, p2])
        cp.drawPointsAsSegments(raster, color=PathUtilities.GTColor.fromName("red"))

    for raster in rasters:
        cp.drawPointsAsCircles(raster, 4, [PathUtilities.GTColor.fromName("blue")])
        cp.drawPointsAsCircles([PathUtilities.midpoint(raster)], 4, [PathUtilities.GTColor.fromName("green")])

    image = cp.generateFinalImage()

    imageFile = open(f"RasterSamplingTest {fullName}_{glyphName}.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()


if __name__ == "__main__":
    main()
