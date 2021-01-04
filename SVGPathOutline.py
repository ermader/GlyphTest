"""\
Classes to implement glyph outlines based on svgpathtools.

Created on November 30, 2020

@author Eric Mader
"""

from svgpathtools import Line, QuadraticBezier, CubicBezier, Path, is_bezier_segment, bpoints2bezier
from Bezier import Bezier
import PathUtilities

try:
    from collections.abc import MutableSequence  # noqa
except ImportError:
    from collections import MutableSequence  # noqa

# path segment .length() parameters for arc length computation
LENGTH_MIN_DEPTH = 5
LENGTH_ERROR = 1e-12
USE_SCIPY_QUAD = True  # for elliptic Arc segment arc length computation

# path segment .ilength() parameters for inverse arc length computation
ILENGTH_MIN_DEPTH = 5
ILENGTH_ERROR = 1e-12
ILENGTH_S_TOL = 1e-12
ILENGTH_MAXITS = 10000

class SVGPathSegment(object):
    def __init__(self, segment):
        if is_bezier_segment(segment):
            self._segment = segment
        else:
            self._segment = bpoints2bezier(segment)

        self._direction = self._computeDirection()

    def __repr__(self):
        return f"SVGPathSegment({repr(self._segment)})"

    def __eq__(self, other):
        if isinstance(other, SVGPathSegment):
            return self._segment == other._segment
        return self._segment == other

    def __ne__(self, other):
        return not self == other

    def __getitem__(self, item):
        return self._segment[item]

    def __len__(self):
        return len(self._segment)

    def point(self, t):
        """returns the coordinates of the Bezier curve evaluated at t."""
        return self._segment.point(t)

    def get(self, t):
        """returns the coordinates of the Bezier curve evaluated at t."""
        return self._segment.point(t)

    def points(self, ts):
        """Faster than running Path.point many times."""
        return self._segment.poly(ts)

    def length(self, t0=0, t1=1, error=None, min_depth=None):
        """returns the length of the segment between t0 and t1."""
        return self._segment.length(t0, t1, error, min_depth)

    def ilength(self, s, s_tol=ILENGTH_S_TOL, maxits=ILENGTH_MAXITS,
                error=ILENGTH_ERROR, min_depth=ILENGTH_MIN_DEPTH):
        """Returns a float, t, such that self.length(0, t) is approximately s.
        See the inv_arclength() docstring for more details."""
        return self._segment.ilength(s, s_tol, maxits, error, min_depth)

    def bpoints(self):
        """returns the Bezier control points of the segment."""
        return self._segment.bpoints()

    def poly(self, return_coeffs=False):
        """returns the segment as a Polynomial object."""
        return self._segment.poly(return_coeffs)

    def intersect(self, other):
        tol = None if isinstance(self._segment, Line) else 1e-12
        return self._segment.intersect(other._segment, tol)

    def intersectWithLine(self, line):
        t = self.intersect(line)[0][0]
        return self.point(t)

    @classmethod
    def pointXY(cls, point):
        return point.real, point.imag

    @classmethod
    def xyPoint(cls, x, y):
        return complex(x, y)

    @property
    def start(self):
        return self._segment.start

    @property
    def startX(self):
        return self.start.real

    @property
    def startY(self):
        return self.start.imag

    @property
    def end(self):
        return self._segment.end

    @property
    def endX(self):
        return self.end.real

    @property
    def endY(self):
        return self.end.imag

    @property
    def midpoint(self):
        return self._segment.point(0.5)

    @property
    def controlPoints(self):
        return self._segment.bpoints()

    @property
    def order(self):
        return len(self.controlPoints) - 1

    @property
    def direction(self):
        return self._direction

    @property
    def boundsRectangle(self):
        xmin, xmax, ymin, ymax = self._segment.bbox()
        return PathUtilities.GTBoundsRectangle((xmin, ymin), (xmax, ymax))

    def _computeDirection(self):
        bpoints = self.controlPoints
        order = self.order

        p0y = bpoints[0].imag
        p1y = bpoints[1].imag

        if order == 1:
            if p0y == p1y:
                return Bezier.dir_flat

            if p0y < p1y:
                return Bezier.dir_up

            return Bezier.dir_down

        p2y = bpoints[2].imag
        if order == 2:
            if p0y <= p1y <= p2y:
                return Bezier.dir_up
            if p0y >= p1y >= p2y:
                return Bezier.dir_down

            # we assume that a quadratic bezier won't be flat...
            return Bezier.dir_mixed

        p3y = bpoints[3].imag
        if order == 3:
            if p0y <= p1y <= p2y <= p3y:
                return Bezier.dir_up
            if p0y >= p1y >= p2y >= p3y:
                return Bezier.dir_down

            # we assume that a cubic bezier won't be flat...
            return Bezier.dir_mixed

        # For now, just say higher-order curves are mixed...
        return Bezier.dir_mixed


class SVGPathContour(MutableSequence):
    def __init__(self, *segments):
        if len(segments) > 0:
            self._segments = segments
        else:
            self._segments = []
        self._start = None
        self._end = None

    def __getitem__(self, index):
        return self._segments[index]

    def __setitem__(self, index, value):
        self._segments[index] = SVGPathSegment(value)
        # self._length = None
        self._start = self._segments[0].start
        self._end = self._segments[-1].end

    def __delitem__(self, index):
        del self._segments[index]
        # self._length = None
        self._start = self._segments[0].start
        self._end = self._segments[-1].end

    def __iter__(self):
        return self._segments.__iter__()

    def __contains__(self, x):
        return self._segments.__contains__(x)  # not sure this is right, but also not sure it is right in Path()...

    def insert(self, index, value):
        self._segments.insert(index, SVGPathSegment(value))

    def __len__(self):
        return len(self._segments)

    def __repr__(self):
        segments = ", \n     ".join(repr(x) for x in self._segments)
        return f"SVGPathContour({segments})"

    @classmethod
    def pointXY(cls, point):
        return SVGPathSegment.pointXY(point)

    @classmethod
    def xyPoint(cls, x, y):
        return SVGPathSegment.xyPoint(x, y)

    @property
    def start(self):
        if not self._start:
            self._start = self._segments[0].start
        return self._start

    @start.setter
    def start(self, pt):
        self._start = pt
        self._segments[0].start = pt

    @property
    def end(self):
        if not self._end:
            self._end = self._segments[-1].end
        return self._end

    @end.setter
    def end(self, pt):
        self._end = pt
        self._segments[-1].end = pt

    @property
    def boundsRectangle(self):
        bounds = PathUtilities.GTBoundsRectangle()

        for segment in self._segments:
            bounds = bounds.union(segment.boundsRectangle)

        return bounds

    def d(self, useSandT=False, use_closed_attrib=False, rel=False):
        """Returns a path d-string for the path object.
        For an explanation of useSandT and use_closed_attrib, see the
        compatibility notes in the README."""

        segments = [s._segment for s in self._segments]
        path = Path(*segments)
        return path.d(useSandT, use_closed_attrib, rel)

    # And lots of other methods from Path...

class SVGPathOutline(MutableSequence):  # maybe take font, glyph name and construct a pen to get the paths?
    def __init__(self):
        self._contours = []

    def __getitem__(self, index):
        return self._contours[index]

    def __setitem__(self, index, value):
        self._contours[index] = value
        # self._length = None
        # self._start = self._segments[0].start
        # self._end = self._segments[-1].end

    def __delitem__(self, index):
        del self._contours[index]
        # self._length = None
        # self._start = self._segments[0].start
        # self._end = self._segments[-1].end

    def __iter__(self):
        return self._contours.__iter__()

    def __contains__(self, x):
        return self._contours.__contains__(x)

    def insert(self, index, value):
        self._contours.insert(index, value)

    def __len__(self):
        return len(self._contours)

    @classmethod
    def pointXY(cls, point):
        return SVGPathSegment.pointXY(point)

    @classmethod
    def xyPoint(cls, x, y):
        return SVGPathSegment.xyPoint(x, y)

    @classmethod
    def unzipPoints(cls, points):
        xs = []
        ys = []

        for p in points:
            xs.append(p.real)
            ys.append(p.imag)

        return xs, ys

    @classmethod
    def segmentFromPoints(cls, points):
        return SVGPathSegment(bpoints2bezier(points))

    @classmethod
    def pathFromSegments(cls, *segments):
        return SVGPathContour(*segments)

    @property
    def boundsRectangle(self):
        bounds = PathUtilities.GTBoundsRectangle()

        for contour in self._contours:
            bounds = bounds.union(contour.boundsRectangle)

        return bounds
