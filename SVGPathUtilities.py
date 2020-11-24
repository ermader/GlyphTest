"""\
Utilities for svgpathtools objects

Created on November 23, 2020

@author Eric Mader
"""

from svgpathtools import Line, QuadraticBezier, CubicBezier, Path, bpoints2bezier
from Bezier import Bezier

def pointFromComplexPoint(cpoint):
    return (cpoint.real, cpoint.imag)

def complexPointFromPoint(point):
    x, y = point
    return complex(x, y)

def curveDirection(curve):
    bpoints = curve.bpoints()
    order = len(bpoints) - 1

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

def crossesY(path, y):
    _, _, miny, maxy = path.bbox()
    return miny <= y <= maxy

def midpoint(line):
    mp = (line.start + line.end) / 2
    return mp

