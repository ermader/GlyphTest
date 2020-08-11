"""\
Tests of drawing a curve

Created on August 10, 2020

@author Eric Mader
"""

import math
import PathUtilities
from ContourPlotter import ContourPlotter

class Curve(object):
    def __init__(self, controlPoints, interval):
        self._controlPoints = controlPoints
        self._interval = interval
        self._derivative = None
        self._curvePoints = []

        for t in range(interval + 1):
            self._computePoints(controlPoints, t / interval)

    def _computePoints(self, points, t):
        if len(points) == 1:
            self._curvePoints.append(points[0])
        else:
            newpoints = []
            for i in range(len(points) - 1):
                x = int((1 - t) * points[i][0] + t * points[i + 1][0])
                y = int((1 - t) * points[i][1] + t * points[i + 1][1])
                newpoints.append((x, y))
            self._computePoints(newpoints, t)

    def _derivativeControlPoints(self):
        dcPoints = []
        degree = len(self._controlPoints) - 1
        for i in range(degree):
            x0, y0 = self._controlPoints[i]
            x1, y1 = self._controlPoints[i+1]
            dcPoints.append((degree*(x1-x0), (degree*(y1-y0))))
        return dcPoints

    @property
    def points(self):
        return self._curvePoints

    @property
    def controlPoints(self):
        return self._controlPoints

    @property
    def derivative(self):
        if self._derivative is None:
            dcp = self._derivativeControlPoints()
            self._derivative = Curve(dcp, self._interval)
        return self._derivative

    # def pointAt(self, t):
    #     return self._curvePoints[t]

    def tangentLineAt(self, t, length):
        derivative = self._derivative
        x, y = self._curvePoints[t]
        tx, ty = derivative._curvePoints[t]
        m = math.sqrt(tx*tx + ty*ty)
        tx = (tx / m) * (length / 2)
        ty = (ty / m) * (length / 2)
        return [(x - tx, y - ty), (x + tx, y + ty)]


def test():
    from FontDocTools import GlyphPlotterEngine

    curvePoints = [(90, 140), (25, 210), (230, 210), (150, 10)]
    # curvePoints = [(70, 0), (20, 140), (250, 190)]
    # curvePoints = [(0, 50), (100, 200)]

    curve1 = Curve(curvePoints, 35)
    bounds1 = PathUtilities.GTBoundsRectangle(*curve1.points)

    dCurve = curve1.derivative

    # ddCurve = dCurve.derivative
    #
    # dbounds = PathUtilities.GTBoundsRectangle(*dCurve.points)
    # ddbounds = PathUtilities.GTBoundsRectangle(*ddCurve.points)
    # bounds1 = bounds1.union(dbounds)
    # bounds1 = bounds1.union(ddbounds)
    cp1 = ContourPlotter(bounds1.points)

    cp1.drawPointsAsSegments(curve1.points, PathUtilities.GTColor.fromName("blue"))
    # cp1.drawPointsAsSegments(dCurve.points, PathUtilities.GTColor.fromName("green"))
    # cp1.drawPointsAsSegments(ddCurve.points, PathUtilities.GTColor.fromName("red"))

    cp1.setStrokeOpacity(0.5)
    nd = 10
    for tangentPoint in range(0, 36, 2):
        x, y = curve1.points[tangentPoint]
        tangent = curve1.tangentLineAt(tangentPoint, 20)

        startx, starty = tangent[0]
        endx, endy = tangent[1]
        cp1.setStrokeColor(PathUtilities.GTColor.fromName("red"))
        cp1.drawLine(GlyphPlotterEngine.CoordinateSystem.content, startx, starty, endx, endy)

        rotateTransform = PathUtilities.GTTransform.rotationAbout((x, y))
        normal = rotateTransform.applyToSegment(tangent)
        startx, starty = normal[0]
        endx, endy = normal[1]

        cp1.setStrokeColor(PathUtilities.GTColor.fromName("green"))
        cp1.drawLine(GlyphPlotterEngine.CoordinateSystem.content, startx, starty, endx, endy)

    image1 = cp1.generateFinalImage()

    curve2 = Curve(curvePoints, 350)
    bounds2 = PathUtilities.GTBoundsRectangle(*curve2.points)
    cp2 = ContourPlotter(bounds2.points)

    cp2.drawPointsAsCircles(curve2.points, PathUtilities.GTColor.fromName("blue"))
    image2 = cp2.generateFinalImage()

    imageFile1 = open(f"Curve as Segments Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    imageFile2 = open(f"Curve as Points Test.svg", "wt", encoding="UTF-8")
    imageFile2.write(image2)
    imageFile2.close()

if __name__ == "__main__":
    test()


