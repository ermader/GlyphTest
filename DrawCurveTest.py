"""\
Tests of drawing a curve

Created on August 10, 2020

Much of this code translated from bezier.js, utils.js and others
from https://github.com/Pomax/BezierInfo-2

@author Eric Mader
"""

import math
import PathUtilities
from ContourPlotter import ContourPlotter

class Curve(object):
    def __init__(self, controlPoints):
        self._controlPoints = controlPoints
        self._dcPoints = None
        self._extrema = None

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
            #   JavaScript code does this:
            #     const dCpts = JSON.parse(JSON.stringify(points));
            #   don't know why...
            dcPoints = p
            while len(dcPoints) > 1:
                newPoints = []
                for i in range(len(dcPoints) - 1):
                    x0, y0 = dcPoints[i]
                    x1, y1 = dcPoints[i + 1]
                    nx = x0 + (x1 - x0) * t
                    ny = y0 + (y1 - y0) * t
                    newPoints.append((nx, ny))
                dcPoints = newPoints
            return dcPoints[0]

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

    def _tangent(self, t):
        d = self._derivative(t)
        q = math.hypot(d[0], d[1])
        return (d[0] / q, d[1] / q)

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

    def stepPoints(self, steps):
        step = 1 / steps
        points = []
        points.append(self.controlPoints[0])

        t = step
        while t < 1 + step:
            points.append(self.get(min(t, 1)))
            t += step

        return points

def test():
    from FontDocTools import GlyphPlotterEngine

    curvePoints = [(90, 140), (25, 210), (230, 210), (150, 10)]
    # curvePoints = [(70, 0), (20, 140), (250, 190)]
    # curvePoints = [(0, 50), (100, 200)]

    curve1 = Curve(curvePoints)

    bbox = curve1.bbox
    minX, maxX = bbox[0]
    minY, maxY = bbox[1]
    bounds1 = PathUtilities.GTBoundsRectangle((minX, minY), (maxX, maxY))

    cp1 = ContourPlotter(bounds1.points)

    cp1.drawCurve(curve1.controlPoints, PathUtilities.GTColor.fromName("blue"))

    angle = PathUtilities.rawSlopeAngle(curve1.controlPoints)
    align = PathUtilities.GTTransform.moveAndRotate(curve1.controlPoints[0], (0, 0), -angle)

    aligned = Curve(align.applyToSegment(curve1.controlPoints))

    tbbox = aligned.bbox
    minX, maxX = tbbox[0]
    minY, maxY = tbbox[1]
    tBounds = PathUtilities.GTBoundsRectangle((minX, minY), (maxX, maxY))

    translate = PathUtilities.GTTransform.rotateAndMove((0, 0), curve1.controlPoints[0], angle)
    tbContour = translate.applyToContour(tBounds.contour)
    cp1._boundsAggregator.addBounds(PathUtilities.GTBoundsRectangle.fromContour(tbContour).points)
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

        tp = curve1._tangent(t)
        tx = tp[0] * lLength/2
        ty = tp[1] * lLength/2
        cp1.drawContours([[[(p[0] - tx, p[1] - ty), (p[0] + tx, p[1] + ty)]]], PathUtilities.GTColor.fromName("red"))

        np = curve1._normal(t)
        nx = np[0] * lLength/2
        ny = np[1] * lLength/2
        cp1.drawContours([[[(p[0] - nx, p[1] - ny), (p[0] + nx, p[1] + ny)]]], PathUtilities.GTColor.fromName("green"))

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve Tangents and Normals Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    cp1 = ContourPlotter(bounds1.points)
    cp1.setStrokeColor(PathUtilities.GTColor.fromName("blue"))
    points = curve1.stepPoints(30)
    cp1.drawPointsAsSegments(points)

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve Flattening Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    cp1 = ContourPlotter(bounds1.points)
    cp1.setFillColor(PathUtilities.GTColor.fromName("blue"))
    points = curve1.stepPoints(100)
    cp1.drawPointsAsCircles(points)

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve as Points Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    curve5Points = [(0, 5), (40, 5), (40, 40), (80, 40), (80, -50), (120, -50)]

    curve5 = Curve(curve5Points)
    bbox = curve5.bbox
    minX, maxX = bbox[0]
    minY, maxY = bbox[1]
    bounds5 = PathUtilities.GTBoundsRectangle((minX, minY), (maxX, maxY))

    cp5 = ContourPlotter(bounds5.points)
    cp5.setFillColor(PathUtilities.GTColor.fromName("blue"))
    points = curve5.stepPoints(100)
    cp5.drawPointsAsCircles(points)

    image5 = cp5.generateFinalImage()

    imageFile5 = open(f"Fifth Order Curve Test.svg", "wt", encoding="UTF-8")
    imageFile5.write(image5)
    imageFile5.close()

    curve11Points = [(175, 178), (220, 250), (114, 285), (27, 267), (33, 159), (146, 143), (205, 33), (84, 117), (43, 59), (58, 24)]
    curve11 = Curve(curve11Points)
    bbox = curve11.bbox
    minX, maxX = bbox[0]
    minY, maxY = bbox[1]
    bounds11 = PathUtilities.GTBoundsRectangle((minX, minY), (maxX, maxY))

    cp11 = ContourPlotter(bounds11.points)
    cp11.setFillColor(PathUtilities.GTColor.fromName("blue"))
    points = curve11.stepPoints(200)
    cp11.drawPointsAsCircles(points)

    image11 = cp11.generateFinalImage()

    imageFile11 = open(f"Eleventh Order Curve Test.svg", "wt", encoding="UTF-8")
    imageFile11.write(image11)
    imageFile11.close()


if __name__ == "__main__":
    test()


