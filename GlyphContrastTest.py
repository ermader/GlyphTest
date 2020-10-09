"""\
Determine the contrast of a glyph by
measuring thickest and thinnest stroke width

Created on October 7, 2020

Much of this code translated from bezier.js, utils.js and others
from https://github.com/Pomax/BezierInfo-2

@author Eric Mader
"""

import math
from GlyphTest import GTFont
from Bezier import Bezier, BOutline, drawOutline
import GlyphContours
import PathUtilities
import ContourPlotter

def test():
    steps = 20
    font = GTFont("/System/Library/Fonts/NewYork.ttf")
    glyph = font.glyphForName("o")
    glyphContours = GlyphContours.GTGlyphCoutours(glyph)
    contours = glyphContours.contours
    outline = BOutline(contours)
    bounds = outline.boundsRectangle
    closePoints = []

    outerContour, innerContour = outline.bContours
    outerLUT = outerContour.getLUT(steps)

    for op in outerLUT:
        closest, ip = innerContour.findClosestPoint(op, steps)
        closePoints.append((closest, op, ip))

    closePoints.sort(key=lambda cp: cp[0])

    print(f"Max distance = {closePoints[-1][0]}, min distance = {closePoints[0][0]}")
    cp = ContourPlotter.ContourPlotter(bounds.points)
    cp.drawContours([bounds.contour], PathUtilities.GTColor.fromName("grey"))
    drawOutline(cp, outline)
    cp.pushStrokeAttributes(width=4)

    _, cop, cip = closePoints[0]
    cp.drawPointsAsSegments([cop, cip], PathUtilities.GTColor.fromName("blue"))

    _, cop, cip = closePoints[-1]
    cp.drawPointsAsSegments([cop, cip], PathUtilities.GTColor.fromName("blue"))

    image = cp.generateFinalImage()
    imageFile = open("Glyh Contrast Test.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()





if __name__ == "__main__":
    test()
