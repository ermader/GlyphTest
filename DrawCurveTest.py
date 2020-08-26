"""\
Tests of drawing a curve

Created on August 10, 2020

Much of this code translated from bezier.js, utils.js and others
from https://github.com/Pomax/BezierInfo-2

@author Eric Mader
"""

import math
from decimal import Decimal, getcontext
import PathUtilities
from ContourPlotter import ContourPlotter

# Legendre-Gauss abscissae with n=24 (x_i values, defined at i=n as the roots of the nth order Legendre polynomial Pn(x))
tValues = [
    Decimal("-0.0640568928626056260850430826247450385909"),
    Decimal("0.0640568928626056260850430826247450385909"),
    Decimal("-0.1911188674736163091586398207570696318404"),
    Decimal("0.1911188674736163091586398207570696318404"),
    Decimal("-0.3150426796961633743867932913198102407864"),
    Decimal("0.3150426796961633743867932913198102407864"),
    Decimal("-0.4337935076260451384870842319133497124524"),
    Decimal("0.4337935076260451384870842319133497124524"),
    Decimal("-0.5454214713888395356583756172183723700107"),
    Decimal("0.5454214713888395356583756172183723700107"),
    Decimal("-0.6480936519369755692524957869107476266696"),
    Decimal("0.6480936519369755692524957869107476266696"),
    Decimal("-0.7401241915785543642438281030999784255232"),
    Decimal("0.7401241915785543642438281030999784255232"),
    Decimal("-0.8200019859739029219539498726697452080761"),
    Decimal("0.8200019859739029219539498726697452080761"),
    Decimal("-0.8864155270044010342131543419821967550873"),
    Decimal("0.8864155270044010342131543419821967550873"),
    Decimal("-0.9382745520027327585236490017087214496548"),
    Decimal("0.9382745520027327585236490017087214496548"),
    Decimal("-0.9747285559713094981983919930081690617411"),
    Decimal("0.9747285559713094981983919930081690617411"),
    Decimal("-0.9951872199970213601799974097007368118745"),
    Decimal("0.9951872199970213601799974097007368118745"),
]

# Legendre-Gauss weights with n=24 (w_i values, defined by a function linked to in the Bezier primer article)
cValues = [
    Decimal("0.1279381953467521569740561652246953718517"),
    Decimal("0.1279381953467521569740561652246953718517"),
    Decimal("0.1258374563468282961213753825111836887264"),
    Decimal("0.1258374563468282961213753825111836887264"),
    Decimal("0.121670472927803391204463153476262425607"),
    Decimal("0.121670472927803391204463153476262425607"),
    Decimal("0.1155056680537256013533444839067835598622"),
    Decimal("0.1155056680537256013533444839067835598622"),
    Decimal("0.1074442701159656347825773424466062227946"),
    Decimal("0.1074442701159656347825773424466062227946"),
    Decimal("0.0976186521041138882698806644642471544279"),
    Decimal("0.0976186521041138882698806644642471544279"),
    Decimal("0.086190161531953275917185202983742667185"),
    Decimal("0.086190161531953275917185202983742667185"),
    Decimal("0.0733464814110803057340336152531165181193"),
    Decimal("0.0733464814110803057340336152531165181193"),
    Decimal("0.0592985849154367807463677585001085845412"),
    Decimal("0.0592985849154367807463677585001085845412"),
    Decimal("0.0442774388174198061686027482113382288593"),
    Decimal("0.0442774388174198061686027482113382288593"),
    Decimal("0.0285313886289336631813078159518782864491"),
    Decimal("0.0285313886289336631813078159518782864491"),
    Decimal("0.0123412297999871995468056670700372915759"),
    Decimal("0.0123412297999871995468056670700372915759"),
]

class Curve(object):
    def __init__(self, controlPoints):
        self._controlPoints = controlPoints
        self._dcPoints = None
        self._extrema = None
        self._length = None
        self._bbox = None
        self._boundsRectangle = None
        self._lut = []

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
        if not self._bbox:
            extrema = self.extrema
            result = {}

            for dim in range(2):
                result[dim] = self._getminmax(dim, extrema[dim])

            self._bbox = result

        return self._bbox

    @property
    def boundsRectangle(self):
        if not self._boundsRectangle:
            bbox = self.bbox
            minX, maxX = bbox[0]
            minY, maxY = bbox[1]
            self._boundsRectangle = PathUtilities.GTBoundsRectangle((minX, minY), (maxX, maxY))

        return self._boundsRectangle

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

    def getLUT(self, steps=100):
        if len(self._lut) == steps: return self._lut

        self._lut = []
        # We want a range from 0 to 1 inclusive, so
        # we decrement steps and use range(steps+1)
        steps -= 1
        for t in range(steps+1):
            self._lut.append(self.get(t / steps))

        return self._lut

    def _arcfun(self, t):
        dx, dy = self._derivative(t)
        ddx = Decimal(dx)
        ddy = Decimal(dy)

        # getcontext().prec += 2
        result = (ddx * ddx + ddy * ddy).sqrt()
        # getcontext().prec -= 2
        return result

    @property
    def length(self):
        if not self._length:
            z = Decimal(0.5)
            sum = Decimal(0)

            getcontext().prec += 2
            for i in range(len(tValues)):
                t = tValues[i].fma(z, z)
                sum = cValues[i].fma(self._arcfun(t), sum)

            length = z * sum
            getcontext().prec -= 2
            self._length = +length

        return self._length

def test():
    from FontDocTools import GlyphPlotterEngine

    colorRed = PathUtilities.GTColor.fromName("red")
    colorGreen = PathUtilities.GTColor.fromName("green")
    colorBlue = PathUtilities.GTColor.fromName("blue")
    colorGold = PathUtilities.GTColor.fromName("gold")
    colorMagenta = PathUtilities.GTColor.fromName("magenta")

    curvePoints = [(90, 140), (25, 210), (230, 210), (150, 10)]
    # curvePoints = [(70, 0), (20, 140), (250, 190)]
    # curvePoints = [(0, 50), (100, 200)]

    curve1 = Curve(curvePoints)

    bounds1 = curve1.boundsRectangle

    cp1 = ContourPlotter(bounds1.points)

    cp1.drawCurve(curve1.controlPoints, colorBlue)

    angle = PathUtilities.rawSlopeAngle(curve1.controlPoints)
    align = PathUtilities.GTTransform.moveAndRotate(curve1.controlPoints[0], (0, 0), -angle)

    aligned = Curve(align.applyToSegment(curve1.controlPoints))

    tBounds = aligned.boundsRectangle

    translate = PathUtilities.GTTransform.rotateAndMove((0, 0), curve1.controlPoints[0], angle)
    tbContour = translate.applyToContour(tBounds.contour)
    cp1._boundsAggregator.addBounds(PathUtilities.GTBoundsRectangle.fromContour(tbContour).points)
    cp1.setStrokeOpacity(0.5)

    cp1.drawContours([bounds1.contour], colorGold)

    cp1.drawContours([tbContour], colorMagenta)

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve Bounding Boxes Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    cp1 = ContourPlotter(bounds1.points)

    cp1.drawCurve(curve1.controlPoints, colorBlue)
    cp1.setStrokeOpacity(0.5)

    nPoints = 10
    lLength = 20
    for i in range(nPoints + 1):
        t = i / nPoints
        p = curve1.get(t)

        tp = curve1._tangent(t)
        tx = tp[0] * lLength/2
        ty = tp[1] * lLength/2
        cp1.drawContours([[[(p[0] - tx, p[1] - ty), (p[0] + tx, p[1] + ty)]]], colorRed)

        np = curve1._normal(t)
        nx = np[0] * lLength/2
        ny = np[1] * lLength/2
        cp1.drawContours([[[(p[0] - nx, p[1] - ny), (p[0] + nx, p[1] + ny)]]], colorGreen)

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve Tangents and Normals Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    cp1 = ContourPlotter(bounds1.points)
    points = curve1.getLUT(30)
    cp1.drawPointsAsSegments(points, colorBlue)

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve Flattening Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    cp1 = ContourPlotter(bounds1.points)
    points = curve1.getLUT(100)
    cp1.drawPointsAsCircles(points, colorBlue)

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve as Points Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    curve5Points = [(0, 5), (40, 5), (40, 40), (80, 40), (80, -50), (120, -50)]

    curve5 = Curve(curve5Points)
    bounds5 = curve5.boundsRectangle

    cp5 = ContourPlotter(bounds5.points)
    points = curve5.getLUT(100)
    cp5.drawPointsAsCircles(points, colorBlue)

    image5 = cp5.generateFinalImage()

    imageFile5 = open(f"Fifth Order Curve Test.svg", "wt", encoding="UTF-8")
    imageFile5.write(image5)
    imageFile5.close()

    curve11Points = [(175, 178), (220, 250), (114, 285), (27, 267), (33, 159), (146, 143), (205, 33), (84, 117), (43, 59), (58, 24)]
    curve11 = Curve(curve11Points)
    bounds11 = curve11.boundsRectangle

    cp11 = ContourPlotter(bounds11.points)
    points = curve11.getLUT(200)
    cp11.drawPointsAsCircles(points, colorBlue)

    image11 = cp11.generateFinalImage()

    imageFile11 = open(f"Eleventh Order Curve Test.svg", "wt", encoding="UTF-8")
    imageFile11.write(image11)
    imageFile11.close()

    curve2Points = [(120, 140), (35, 100), (220, 40), (220, 260)]
    curve2 = Curve(curve2Points)
    bounds2 = curve2.boundsRectangle

    points = curve2.getLUT(16)
    aLen = 0
    for i in range(len(points) - 1):
        aLen += PathUtilities.length([points[i], points[i+1]])

    cp2 = ContourPlotter(bounds2.points)
    margin = cp2._contentMargins.left
    cp2.setLabelFontSize(4, 4)  # Not sure what the "scaled" parameter is for...
    cp2.drawCurve(curve2.controlPoints, colorBlue)
    cp2.drawLabel(GlyphPlotterEngine.CoordinateSystem.contentMargins, bounds2.width / 2 + margin, -6, 0, "center", f"Curve length: {curve2.length}")
    image2 = cp2.generateFinalImage()
    imageFile2 = open("Curve Length Test.svg", "wt", encoding="UTF-8")
    imageFile2.write(image2)
    imageFile2.close()

    cp2 = ContourPlotter(bounds2.points)
    cp2.setLabelFontSize(4, 4)  # Not sure what the "scaled" parameter is for...


    points = curve2.getLUT(16)
    aLen = 0
    for i in range(len(points) - 1):
        aLen += PathUtilities.length([points[i], points[i + 1]])

    cp2.drawPointsAsSegments(points, colorBlue)
    cp2.drawLabel(GlyphPlotterEngine.CoordinateSystem.contentMargins, bounds2.width / 2 + margin, -6, 0, "center", f"Approximate curve length, 16 steps: {aLen}")

    image2 = cp2.generateFinalImage()
    imageFile2 = open("Approximate curve Length Test.svg", "wt", encoding="UTF-8")
    imageFile2.write(image2)
    imageFile2.close()

if __name__ == "__main__":
    test()


