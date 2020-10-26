"""\
Raster Sampling Tests

Created on October 26, 2020

@author Eric Mader
"""

from os.path import basename
from sys import argv, exit, stderr
import logging
from GlyphTest import GTFont
from Bezier import Bezier, BOutline, drawOutline
from SegmentPen import SegmentPen
from UFOFont import UFOFont
import PathUtilities
import ContourPlotter
from TestArgumentIterator import TestArgs

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
    flatList = []
    mixedList = []

    for bContour in outline.bContours:
        for curve in bContour.beziers:
            if curve.direction == Bezier.dir_up: upList.append(curve)
            elif curve.direction == Bezier.dir_down: downList.append(curve)
            elif curve.direction == Bezier.dir_flat: flatList.append(curve)
            else: mixedList.append(curve)

    upList.sort(key=lambda b: b.controlPoints[0][0])
    downList.sort(key=lambda b: b.controlPoints[0][0])
    flatList.sort(key=lambda b: b.controlPoints[0][0])

    print("up list:")
    for b in upList: print(b.controlPoints)
    print("\ndown list:")
    for b in downList: print(b.controlPoints)
    print("\nflat list:")
    for b in flatList: print(b.controlPoints)
    if len(mixedList) > 0:
        print("\nmixed list:")
        for b in mixedList: print(b.controlPoints)


if __name__ == "__main__":
    main()
