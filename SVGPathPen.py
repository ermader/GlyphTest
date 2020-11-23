"""\
A pen to convert a glyph into a list of svgpathtools Path objects

Created on November 18, 2020

@author Eric Mader
"""

from svgpathtools import Line, QuadraticBezier, CubicBezier, Path, bpoints2bezier
import PathUtilities

def applyTransformToSegment(t, s):
    segment = []
    sp = s.bpoints()
    for p in sp:
        segment.append(t.applyToPoint(p))
    return bpoints2bezier(segment)

def applyTransformToPath(t, p):
    segments = []
    for s in p:
        segments.append(applyTransformToSegment(t, s))
    return Path(*segments)

def applyTransformToPaths(t, paths):
    tpaths = []
    for path in paths:
        tpaths.append(applyTransformToPath(t, path))
    return tpaths

class SVGPathPen:
    def __init__(self, glyphSet, logger):
        self._paths = []
        self._glyphSet = glyphSet
        self.logger = logger

    @classmethod
    def convertPoint(cls, point):
        x, y = point
        return complex(x, y)

    def addPoint(self, pt, segmentType, smooth, name):
        raise NotImplementedError

    def moveTo(self, pt):
        self._lastOnCurve = pt

        # This is for glyphs, which are always closed paths,
        # so we assume that the move is the start of a new contour
        self._path = Path()
        self._segment = []
        self.logger.debug(f"moveTo({pt})")

    def lineTo(self, pt):
        # an old bug in fontTools.ttLib.tables._g_l_y_f.Glyph.draw()
        # can cause this to be called w/ a zero-length line.
        if pt != self._lastOnCurve:
            self._path.append(Line(self.convertPoint(self._lastOnCurve), self.convertPoint(pt)))
            self.logger.debug(f"lineTo({pt})")
            self._lastOnCurve = pt

    def curveTo(self, *points):
        cpoints = [self.convertPoint(self._lastOnCurve)]
        cpoints.extend([self.convertPoint(p) for p in points])
        self._path.append(CubicBezier(*cpoints))
        self.logger.debug(f"CurveTo({points})")
        self._lastOnCurve = points[-1]

    def qCurveTo(self, *points):
        cpoints = [self.convertPoint(self._lastOnCurve)]
        cpoints.extend([self.convertPoint(p) for p in points])

        if len(cpoints) <= 3:
            self._path.append(QuadraticBezier(*cpoints))
        else:
            # a starting on-curve point, two or more off-curve points, and a final on-curve point
            startPoint = cpoints[0]
            for i in range(1, len(cpoints) - 2):
                impliedPoint = ((cpoints[i] + cpoints[i + 1]) / 2)
                self._path.append(QuadraticBezier(startPoint, cpoints[i], impliedPoint))
                startPoint = impliedPoint
            self._path.append(QuadraticBezier(startPoint, cpoints[-2], cpoints[-1]))
        self.logger.debug(f"qCurveTo({points})")
        self._lastOnCurve = points[-1]

    def beginPath(self):
        raise NotImplementedError

    def closePath(self):
        self._paths.append(self._path)
        if self._path[0].start != self._path[-1].end:
            self._path.append(Line(self._path[-1].end, self._path[0].start))
        self._path = Path()
        self.logger.debug("closePath()")

    def endPath(self):
        raise NotImplementedError

    identityTransformation = (1, 0, 0, 1, 0, 0)

    def addComponent(self, glyphName, transformation):
        self.logger.debug(f"addComponent(\"{glyphName}\", {transformation}")
        if transformation != self.identityTransformation:
            xScale, xyScale, yxScale, yScale, xOffset, yOffset = transformation
            m = PathUtilities.GTTransform._matrix(
                a=xScale,
                b=xyScale,
                c=yxScale,
                d=yScale,
                m=xOffset,
                n=yOffset
            )
            t = PathUtilities.GTTransform(m)
        else:
            t = None

        glyph = self._glyphSet[glyphName]
        spen = SVGPathPen(self._glyphSet, self.logger)
        glyph.draw(spen)
        paths = applyTransformToPaths(t, spen.paths) if t else spen.paths
        self._paths.extend(paths)

    @property
    def paths(self):
        return self._paths

