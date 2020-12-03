"""\
Determine the contrast of a glyph by
measuring thickest and thinnest stroke width

Created on October 7, 2020

Much of this code translated from bezier.js, utils.js and others
from https://github.com/Pomax/BezierInfo-2

@author Eric Mader
"""

from os.path import basename
from sys import argv, exit, stderr
import logging
from re import fullmatch
from FontDocTools.ArgumentIterator import ArgumentIterator
from GlyphTest import GTFont
from Bezier import Bezier, BOutline, drawOutline
from SegmentPen import SegmentPen
from UFOFont import UFOFont
import PathUtilities
import ContourPlotter
from TestArgumentIterator import TestArgs

class GlyphContrastTestArgs(TestArgs):

    def __init__(self, argumentList):
        self.steps = 20
        TestArgs.__init__(self, argumentList)

    def processArgument(self, argument, arguments):
        if argument == "--steps":
            self.steps = arguments.nextExtraAsPosInt("steps")
        else:
            TestArgs.processArgument(self, argument, arguments)

dir_names = {Bezier.dir_mixed: "mixed", Bezier.dir_flat: "flat", Bezier.dir_up: "up", Bezier.dir_down: "down"}

def main():
    argumentList = argv
    args = None
    programName = basename(argumentList.pop(0))
    if len(argumentList) == 0:
        print(__doc__, file=stderr)
        exit(1)
    try:
        args = GlyphContrastTestArgs(argumentList)
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
    logger = logging.getLogger("glyph-contrast-test")

    glyph = args.getGlyph(font)
    glyphName = glyph.name()
    pen = SegmentPen(font.glyphSet, logger)
    font.glyphSet[glyph.name()].draw(pen)
    contours = pen.contours
    outline = BOutline(contours)
    bounds = outline.boundsRectangle
    closePoints = []
    upList = []
    downList = []

    for bContour in outline.bContours:
        for curve in bContour.beziers:
            if curve.direction == Bezier.dir_up: upList.append(curve)
            if curve.direction == Bezier.dir_down: downList.append(curve)
            # print(f"{curve.controlPoints} - {dir_names[curve.direction]}")

    upList.sort(key=lambda b: b.controlPoints[0][0])
    downList.sort(key=lambda b: b.controlPoints[0][0])
    print("up list:")
    for b in upList: print(b.controlPoints)
    print("\ndown list:")
    for b in downList: print(b.controlPoints)

    outerContour, innerContour = outline.bContours[:2]  # slice in case there's more than two contours...
    outerLUT = outerContour.getLUT(steps)

    for op in outerLUT:
        closest, ip = innerContour.findClosestPoint(op, steps)
        closePoints.append((closest, op, ip))

    closePoints.sort(key=lambda cp: cp[0])

    min = closePoints[0][0]
    max = closePoints[-1][0]
    ratio = max / min

    print(f"Glyph {glyphName}: Max distance = {max}, min distance = {min}, ratio = {ratio}")
    cp = ContourPlotter.ContourPlotter(bounds.points)
    margin = cp._contentMargins.left

    cp.drawText(bounds.width / 2 + margin, cp._labelFontSize / 4, "center", f"min = {round(min, 2)}, max = {round(max, 2)}, wsf = {round(ratio, 3)}")

    cp.drawContours([bounds.contour], PathUtilities.GTColor.fromName("grey"))
    # drawOutline(cp, outline)
    cp.drawPaths(outline)
    cp.pushStrokeAttributes(width=4)

    _, cop, cip = closePoints[0]
    cp.drawPointsAsSegments([cop, cip], PathUtilities.GTColor.fromName("blue"))

    _, cop, cip = closePoints[-1]
    cp.drawPointsAsSegments([cop, cip], PathUtilities.GTColor.fromName("blue"))

    image = cp.generateFinalImage()

    imageFile = open(f"Glyph Contrast Test {fullName}_{glyphName}.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()

if __name__ == "__main__":
    main()
