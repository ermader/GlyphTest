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

MAX_SAFE_INTEGER = +9007199254740991  # Number.MAX_SAFE_INTEGER
MIN_SAFE_INTEGER = -9007199254740991  # Number.MIN_SAFE_INTEGER

# findClosest() and refineBinary() copied from Bezier.test()...
def findClosest(point, LUT):
    x, y = point
    closest = MAX_SAFE_INTEGER
    for index in range(len(LUT)):
        px, py = LUT[index]
        dist = math.hypot(px - x, py - y)
        if dist < closest:
            closest = dist
            i = index

    return i


"""\
  We already know that LUT[i1] and LUT[i2] are *not* good distances,
  so we know that a better distance will be somewhere between them.
  We generate three new points between those two, so we end up with
  five points, and then check which three of those five are a new,
  better, interval to check within.
"""


def refineBinary(point, curve, LUT, i):
    closest = MAX_SAFE_INTEGER
    steps = len(LUT)
    TT = [t / (steps - 1) for t in range(steps)]
    px, py = point

    for _ in range(25):  # This is for safety; the loop should always break
        steps = len(LUT)
        i1 = 0 if i == 0 else i - 1
        i2 = i if i == steps - 1 else i + 1
        t1 = TT[i1]
        t2 = TT[i2]
        lut = []
        tt = []
        step = (t2 - t1) / 5

        if step < 0.001: break
        lut.append(LUT[i1])
        tt.append(TT[i1])
        for j in range(1, 4):
            nt = t1 + (j * step)
            nx, ny = n = curve.get(nt)
            dist = math.hypot(nx - px, ny - py)
            if dist < closest:
                closest = dist
                q = n
                i = j
            lut.append(n)
            tt.append(nt)
        lut.append(LUT[i2])
        tt.append(TT[i2])

        # update the LUT to be our new five point LUT, and run again.
        LUT = lut
        TT = tt

    return (q, closest)

def test():
    steps = 20
    font = GTFont("/System/Library/Fonts/NewYork.ttf")
    glyph = font.glyphForName("o")
    glyphContours = GlyphContours.GTGlyphCoutours(glyph)
    contours = glyphContours.contours
    outline = BOutline(contours)
    bounds = outline.boundsRectangle
    closePoints = []

    for outer in outline.bContours[0].beziers:
        outerLUT = outer.getLUT(steps)

        for op in outerLUT:
            cop = cip = None  # just to remove a referenced before assignment warning...
            closest = MAX_SAFE_INTEGER
            for inner in outline.bContours[1].beziers:
                innerLUT = inner.getLUT(steps)
                i = findClosest(op, innerLUT)
                ip, dist = refineBinary(op, inner, innerLUT, i)
                if dist < closest:
                    closest = dist
                    cop = op
                    cip = ip

            closePoints.append((closest, cop, cip))

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
