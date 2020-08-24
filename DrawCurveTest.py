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
        self._derivativeCurve = None
        self._dcPoints = None
        self._extrema = None
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

    def _compute(self, t):
        order = len(self._controlPoints) - 1

        # shortcuts...
        if t == 0: return self._controlPoints[0]

        if t == 1: return self._controlPoints[order]

        mt = 1 - t
        p = self._controlPoints

        # constant?
        if order == 0: return self._controlPoints[0]

        # linear?
        if order == 1:
            p0x, p0y = p[0]
            p1x, p1y = p[1]
            return (mt * p0x + t * p1x, mt * p0y + t * p1y)

        # quadratic / cubic?
        if order < 4:
            mt2 = mt * mt
            t2 = t * t

            if order == 2:
                p = [p[0], p[1], p[2], (0, 0)]
                a = mt2
                b = mt * t * 2
                c = t2
                d = 0
            elif order == 3:
                a = mt2 * mt
                b = mt2 * t * 3
                c = mt * t2 * 3
                d = t * t2

            p0x, p0y = p[0]
            p1x, p1y = p[1]
            p2x, p2y = p[2]
            p3x, p3y = p[3]
            rx = a * p0x + b * p1x + c * p2x + d * p3x
            ry = a * p0y + b * p1y + c * p2y + d * p3y
            return (rx, ry)
        else:
            # higher order curves: use de Casteljau's computation
            # (but not now ;-)
            return None

    def _derivative(self, t):
        order = len(self._controlPoints) - 1
        p = self._dcPoints[0]
        mt = 1 - t

        if order == 2:
            p = [p[0], p[1], (0, 0)]
            a = mt
            b = t
            c = 0
        elif order == 3:
            a = mt * mt
            b = mt * t * 2
            c = t * t

        p0x, p0y = p[0]
        p1x, p1y = p[1]
        p2x, p2y = p[2]
        rx = a * p0x + b * p1x + c * p2x
        ry = a * p0y + b * p1y + c * p2y
        return (rx, ry)

    def _normal(self, t):
        d = self._derivative(t)
        q = math.hypot(d[0], d[1])
        return (-d[1] / q, d[0] / q)

    def _getminmax(self, d, list):
        # if (!list) return { min: 0, max: 0 };
        min = +9007199254740991  # Number.MAX_SAFE_INTEGER
        max = -9007199254740991  # Number.MIN_SAFE_INTEGER

        if 0 not in list: list.insert(0, 0)
        if 1 not in list: list.append(1)

        for i in range(len(list)):
            c = self.get(list[i])
            if c[d] < min: min = c[d]
            if c[d] > max: max = c[d]

        return (min, max)

    @property
    def bbox(self):
        extrema = self.extrema
        result = {}

        for dim in range(2):
            result[dim] = self._getminmax(dim, extrema[dim])

        return result

    def get(self, t):
        return self._compute(t)

    @staticmethod
    def droots(p):
        # quadratic roots are easy
        if len(p) == 3:
            a = p[0]
            b = p[1]
            c = p[2]
            d = a - 2 * b + c

            if d != 0:
                m1 = - math.sqrt(b * b - a * c)
                m2 = -a + b
                v1 = -(m1 + m2) / d
                v2 = -(-m1 + m2) / d
                return [v1, v2]

            if b != c and d == 0:
                return [(2 * b - c) / (2 * (b - c))]

            return []

        # linear roots are even easier
        if len(p) == 2:
            a = p[0]
            b = p[1]

            if a != b:
                return [a / (a - b)]

        return []


    @property
    def points(self):
        return self._curvePoints

    @property
    def controlPoints(self):
        return self._controlPoints

    @property
    def dcPoints(self):
        if not self._dcPoints:
            dpoints = []
            p = self._controlPoints
            d = len(p)

            while d > 1:
                dpts = []
                c = d - 1
                for j in range(c):
                    x0, y0 = p[j]
                    x1, y1 = p[j+1]
                    dpts.append((c*(x1-x0), c*(y1-y0)))
                dpoints.append(dpts)
                p = dpts
                d -= 1

            self._dcPoints = dpoints

        return self._dcPoints

    @property
    def extrema(self):
        if not self._extrema:
            result = {}
            roots = []

            for dim in range(2):
                p = list(map(lambda p: p[dim], self.dcPoints[0]))
                result[dim] = Curve.droots(p)
                if len(self._controlPoints) == 4:
                    p = list(map(lambda p: p[dim], self.dcPoints[1]))
                    result[dim].extend(Curve.droots(p))
                result[dim] = list(filter(lambda t: t >= 0 and t <= 1, result[dim]))
                roots.extend(sorted(result[dim]))

            # this is only used in reduce() - skip it for now
            # result.values = roots.sort(utils.numberSort).filter(function (v, idx) {
            #       return roots.indexOf(v) === idx;
            #     });
            self._extrema = result

        return self._extrema


    @property
    def derivativeCurve(self):
        if self._derivativeCurve is None:
            dcp = self._derivativeControlPoints()
            self._derivativeCurve = Curve(dcp, self._interval)
        return self._derivativeCurve

    # def pointAt(self, t):
    #     return self._curvePoints[t]

    def tangentLineAt(self, t, length):
        derivative = self._derivativeCurve
        x, y = self._curvePoints[t]
        tx, ty = derivative._curvePoints[t]
        m = math.hypot(tx, ty)
        tx = (tx / m) * (length / 2)
        ty = (ty / m) * (length / 2)
        return [(x - tx, y - ty), (x + tx, y + ty)]


def test():
    from FontDocTools import GlyphPlotterEngine

    curvePoints = [(90, 140), (25, 210), (230, 210), (150, 10)]
    # curvePoints = [(70, 0), (20, 140), (250, 190)]
    # curvePoints = [(0, 50), (100, 200)]

    curve1 = Curve(curvePoints, 35)

    bbox = curve1.bbox
    minX, maxX = bbox[0]
    minY, maxY = bbox[1]
    bounds1 = PathUtilities.GTBoundsRectangle((minX, minY), (maxX, maxY))

    cp1 = ContourPlotter(bounds1.points)

    cp1.drawCurve(curve1.controlPoints, PathUtilities.GTColor.fromName("blue"))

    angle = PathUtilities.rawSlopeAngle(curve1.controlPoints)
    align = PathUtilities.GTTransform.moveAndRotate(curve1.controlPoints[0], (0, 0), -angle)

    aligned = Curve(align.applyToSegment(curve1.controlPoints), 35)

    tbbox = aligned.bbox
    minX, maxX = tbbox[0]
    minY, maxY = tbbox[1]
    tBounds = PathUtilities.GTBoundsRectangle((minX, minY), (maxX, maxY))

    translate = PathUtilities.GTTransform.rotateAndMove((0, 0), curve1.controlPoints[0], angle)
    tbContour = translate.applyToContour(tBounds.contour)
    cp1.setStrokeOpacity(0.5)

    cp1.drawContours([bounds1.contour], PathUtilities.GTColor.fromName("gold"))

    cp1.drawContours([tbContour], PathUtilities.GTColor.fromName("magenta"))

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve Bounding Boxes Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    cp1 = ContourPlotter(bounds1.points)

    cp1.drawCurve(curve1.controlPoints, PathUtilities.GTColor.fromName("blue"))
    cp1.setStrokeOpacity(0.5)

    nPoints = 10
    lLength = 20
    for i in range(nPoints + 1):
        t = i / nPoints
        p = curve1.get(t)
        tg = curve1._derivative(t)
        m = math.hypot(tg[0], tg[1])
        tx = tg[0]/m * lLength/2
        ty = tg[1]/m * lLength/2
        cp1.setStrokeColor(PathUtilities.GTColor.fromName("red"))
        cp1.drawLine(GlyphPlotterEngine.CoordinateSystem.content, p[0] - tx, p[1] - ty, p[0] + tx, p[1] + ty)

        n = curve1._normal(t)
        nx = n[0] * lLength/2
        ny = n[1] * lLength/2
        cp1.setStrokeColor(PathUtilities.GTColor.fromName("green"))
        cp1.drawLine(GlyphPlotterEngine.CoordinateSystem.content, p[0] - nx, p[1] - ny, p[0] + nx, p[1] + ny)

    image1 = cp1.generateFinalImage()

    # curve2 = Curve(curvePoints, 350)
    # bounds2 = PathUtilities.GTBoundsRectangle(*curve2.points)
    # cp2 = ContourPlotter(bounds2.points)
    #
    # cp2.drawPointsAsCircles(curve2.points, PathUtilities.GTColor.fromName("blue"))
    # image2 = cp2.generateFinalImage()

    imageFile1 = open(f"Curve Tangents and Normals Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    cp1 = ContourPlotter(bounds1.points)
    cp1.setStrokeColor(PathUtilities.GTColor.fromName("blue"))
    steps = 30
    step = 1 / steps
    p = curve1.controlPoints[0]
    t = step
    while t < 1 + step:
        cp = curve1.get(min(t, 1))
        cp1.drawLine(GlyphPlotterEngine.CoordinateSystem.content, p[0], p[1], cp[0], cp[1])
        p = cp
        t += step

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve Flattening Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    # imageFile2 = open(f"Curve as Points Test.svg", "wt", encoding="UTF-8")
    # imageFile2.write(image2)
    # imageFile2.close()

if __name__ == "__main__":
    test()


