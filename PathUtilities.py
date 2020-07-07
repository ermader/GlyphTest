"""\
Utilities for manupulating outline paths and segments

Created on July 7, 2020

@author Eric Mader
"""

import math

def getDeltas(segment):
    p0x, p0y = segment[0]
    p1x, p1y = segment[1]

    return (p1x - p0x, p1y - p0y)

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

def test():
    print(f"length(l0) = {length(l0)}, length(l1) = {length(l1)}, length(l2) = {length(l2)}")
    print(f"slope(l0) = {slope(l0)}, slope(l1) = {slope(l1)}, slope(l2) = {slope(l2)}")
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
