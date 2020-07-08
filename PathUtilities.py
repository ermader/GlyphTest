"""\
Utilities for manupulating outline paths and segments

Created on July 7, 2020

@author Eric Mader
"""

import math

def minMax(a, b):
    return (a, b) if a <= b else (b, a)

def endPoints(segment):
    p0x, p0y = segment[0]
    p1x, p1y = segment[-1]

    return (p0x, p0y, p1x, p1y)

def getDeltas(segment):
    p0x, p0y, p1x, p1y = endPoints(segment)

    return (p1x - p0x, p1y - p0y)

# Fix this to work for curves too...
def bounds(segment):
    p0x, p0y, p1x, p1y = endPoints(segment)
    left, right = minMax(p0x, p1x)
    bottom, top = minMax(p0y, p1y)

    return [(left, top), (right, bottom)]

def bounds2(segment):
    right = top = -65536
    left = bottom = 65536

    for point in segment:
        px, py = point
        left = min(left, px)
        right = max(right, px)
        bottom = min(bottom, py)
        top = max(top, py)

    return [(left, top), (right, bottom)]

def inBounds(bounds, point):
    left, top = bounds[0]
    right, bottom = bounds[1]
    px, py = point

    return left <= px <= right and bottom <= py <= top

def isVertical(segment):
    dx, _ = getDeltas(segment)
    return dx == 0

def isHorizontal(segment):
    _, dy = getDeltas(segment)
    return dy == 0

def length(segment):
    dx, dy = getDeltas(segment)

    if dx == 0: return dy
    if dy == 0: return dx

    return math.sqrt(dx*dx + dy*dy)

def slope(segment):
    dx, dy = getDeltas(segment)

    if dx == 0: return math.inf
    return dy / dx

def midpoint(line):
    p0x, p0y, p1x, p1y = endPoints(line)

    return ((p0x + p1x) / 2, (p0y + p1y) / 2)

def cooefs(line):
    p0x, p0y, p1x, p1y = endPoints(line)

    a = p0y - p1y
    b = p1x - p0x
    c = (p0x * p1y) - (p1x * p0y)

    return (a, b, -c)

def intersectionPoint(l1, l2):
    a1, b1, c1 = cooefs(l1)
    a2, b2, c2 = cooefs(l2)

    d = a1 * b2 - b1 * a2

    # d == 0 means lines are parallel
    if d == 0: return None

    dx = c1 * b2 - b1 * c2
    dy = a1 * c2 - c1 * a2

    intersection = (dx / d, dy / d)

    b1 = bounds(l1)
    b2 = bounds(l2)

    return intersection if inBounds(b1, intersection) and inBounds(b2, intersection) else None

def intersection(rectangle1, rectangle2):
    l1, t1 = rectangle1[0]
    r1, b1 = rectangle1[1]
    l2, t2 = rectangle2[0]
    r2, b2 = rectangle2[1]

    li = max(l1, l2)
    ti = min(t1, t2)
    ri = min(r1, r2)
    bi = max(b1, b2)

    if ri < li or bi < ti: return None  # maybe want <=, >=?
    return [(li, ti), (ri, bi)]

def verticalLines(contour):
    return list(filter(lambda s: isVertical(s), contour))

def horizontalLines(contour):
    return list(filter(lambda s: isHorizontal(s), contour))

def sortByX(contour):
    return sorted(contour, key=lambda s: s[0][0])

def sortByY(contour):
    return sorted(contour, key=lambda s: s[0][1])

def crossesY(line, y):
    y0 = line[0][1]
    y1 = line[1][1]
    return y0 < y < y1 if y0 < y1 else y1 < y < y0

def crossesX(line, x):
    x0 = line[0][0]
    x1 = line[1][0]
    return x0 < x < x1 if x0 < x1 else x1 < x < x0

# There must be a better way to do this...
def pointOnLine(point, line):
    px, py = point
    p0x, p0y = line[0]
    p1x, p1y = line[1]

    return crossesX(line, px) and crossesY(line, py) and slope(line) == slope([line[0], point])

# Helvetica Neue H
hContours = [[[(78, 714), (78, 0)], [(78, 0), (173, 0)], [(173, 0), (173, 327)], [(173, 327), (549, 327)], [(549, 327), (549, 0)], [(549, 0), (644, 0)], [(644, 0), (644, 714)], [(644, 714), (549, 714)], [(549, 714), (549, 407)], [(549, 407), (173, 407)], [(173, 407), (173, 714)], [(173, 714), (78, 714)]]]
xContours = [[[(248, 367), (0, 0)], [(0, 0), (106, 0)], [(106, 0), (304, 295)], [(304, 295), (496, 0)], [(496, 0), (612, 0)], [(612, 0), (361, 367)], [(361, 367), (597, 714)], [(597, 714), (491, 714)], [(491, 714), (305, 435)], [(305, 435), (127, 714)], [(127, 714), (13, 714)], [(13, 714), (248, 367)]]]
height = 714
h_25 = height * .25
h_75 = height * .75

p0 = (0, 0)
p1 = (300, 0)
p2 = (300,400)
l0 = [p0, p1]
l1 = [p1, p2]
l2 = [p0, p2]

l3 = [(0, 0), (100, 100)]
l4 = [(50, 200), (200, 50)]

def test():
    print(f"length(l0) = {length(l0)}, length(l1) = {length(l1)}, length(l2) = {length(l2)}")
    print(f"slope(l0) = {slope(l0)}, slope(l1) = {slope(l1)}, slope(l2) = {slope(l2)}")
    print(f"midpoint(l0) = {midpoint(l0)}, midpoint(l1) = {midpoint(l1)}, midpoint(l2) = {midpoint(l2)}")
    print(f"intersection = {intersectionPoint([(0,1), (2,3)], [(2,3), (0,4)])}")
    print(f"intersectionPoint(l0, l1) = {intersectionPoint(l0, l1)}")
    print(f"intersectionPoint(l0, l2) = {intersectionPoint(l0, l2)}")
    print(f"intersectionPoint(l1, l2) = {intersectionPoint(l1, l2)}")
    print(f"intersectionPoint(l3, l4) = {intersectionPoint(l3, l4)}")

    print(bounds(l0) == bounds2(l0))
    print(bounds(l1) == bounds2(l1))
    print(bounds(l2) == bounds2(l2))
    print(bounds(l3) == bounds2(l3))
    print(bounds(l4) == bounds2(l4))

    print(pointOnLine((150, 200), l2))
    print(pointOnLine((-300, -400), l2))

    verticals = verticalLines(hContours[0])
    sortedVerticals = sortByX(verticals)
    print(sortedVerticals)

    horizontals = horizontalLines(hContours[0])
    sortedHorizontals = sortByY(horizontals)
    print(sortedHorizontals)

    diagonals = list(filter(lambda s: not isHorizontal(s), xContours[0]))
    diag_25 = list(filter(lambda s: crossesY(s, h_25), diagonals))
    diag_75 = list(filter(lambda s: crossesY(s, h_75), diagonals))

    print(diagonals)

if __name__ == "__main__":
    test()
