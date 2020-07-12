"""\
Utilities for manupulating outline paths and segments

Created on July 7, 2020

@author Eric Mader
"""

import math

class BoundsRectangle:
    def __init__(self, *points):
        right = top = -32768
        left = bottom = 32768

        for point in points:
            px, py = point
            left = min(left, px)
            right = max(right, px)
            bottom = min(bottom, py)
            top = max(top, py)

        self.leftTop = (left, top)
        self.rightBottom = (right, bottom)

    @staticmethod
    def empty():
        r = BoundsRectangle((0, 0), (0, 0))
        r.leftTop = (32768, -32768)
        r.rightBottom = (-32768, 32768)
        return r

    @staticmethod
    def fromContour(contour):
        bounds = BoundsRectangle.empty()
        for segment in contour:
            bounds = bounds.union(BoundsRectangle(*segment))

        return bounds

    @staticmethod
    def fromCoutours(contours):
        bounds = BoundsRectangle.empty()
        for contour in contours:
            bounds = bounds.union(BoundsRectangle.fromContour(contour))

        return bounds

    def __str__(self):
        return f"[{self.leftTop}, {self.rightBottom}]"

    @property
    def width(self):
        return self.rightBottom[0] - self.leftTop[0]

    @property
    def height(self):
        return self.leftTop[1] - self.rightBottom[1]

    @property
    def area(self):
        return self.width * self.height

    @property
    def centerPoint(self):
        return midpoint([self.leftTop, self.rightBottom])

    def enclosesPoint(self, point):
        left, top = self.leftTop
        right, bottom = self.rightBottom
        px, py = point

        return left <= px <= right and bottom <= py <= top

    def crossesX(self, x):
        left, _ = self.leftTop
        right, _ = self.rightBottom

        return left <= x <= right

    def crossesY(self, y):
        _, top = self.leftTop
        _, bottom = self.rightBottom

        return bottom <= y <= top

    def union(self, other):
        left, top = self.leftTop
        right, bottom = self.rightBottom
        oleft, otop = other.leftTop
        oright, obottom = other.rightBottom

        newLeft = min(left, oleft)
        newTop = max(top, otop)
        newRight = max(right, oright)
        newBottom = min(bottom, obottom)

        return BoundsRectangle((newLeft, newTop), (newRight, newBottom))

    def intersection(self, other):
        left, top = self.leftTop
        right, bottom = self.rightBottom
        oleft, otop = other.leftTop
        oright, obottom = other.rightBottom

        newLeft = max(left, oleft)
        newTop = min(top, otop)
        newRight = min(right, oright)
        newBottom = max(bottom, obottom)

        if newRight < newLeft or newTop < newBottom: return None  # maybe want <=, >=?
        return BoundsRectangle((newLeft, newTop), (newRight, newBottom))


def minMax(a, b):
    return (a, b) if a <= b else (b, a)

def endPoints(segment):
    p0x, p0y = segment[0]
    p1x, p1y = segment[-1]

    return (p0x, p0y, p1x, p1y)

def getDeltas(segment):
    p0x, p0y, p1x, p1y = endPoints(segment)

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

    b1 = BoundsRectangle(*l1)
    b2 = BoundsRectangle(*l2)

    return intersection if b1.enclosesPoint(intersection) and b2.enclosesPoint(intersection) else None

def flatten(contours):
    segments = []

    for contour in contours:
        for segment in contour:
            segments.append(segment)

    return segments

def verticalLines(contour):
    return list(filter(lambda s: isVertical(s), contour))

def verticalLinesCrossing(contour, y):
    return list(filter(lambda s: crossesY(s, y), sortByX((verticalLines(contour)))))

def horizontalLines(contour):
    return list(filter(lambda s: isHorizontal(s), contour))

def horizontalLinesCrossing(contour, x):
    return list(filter(lambda s: crossesX(s, x), sortByY((horizontalLines(contour)))))

def sortByX(contour):
    return sorted(contour, key=lambda s: s[0][0])

def sortByY(contour):
    return sorted(contour, key=lambda s: s[0][1])

def crossesY(line, y):
    return BoundsRectangle(*line).crossesY(y)

def crossesX(line, x):
    return BoundsRectangle(*line).crossesX(x)

# There must be a better way to do this...
def pointOnLine(point, line):
    bounds = BoundsRectangle(*line)

    return bounds.enclosesPoint(point) and slope(line) == slope([line[0], point])

# Helvetica Neue H
hContours = [[[(78, 714), (78, 0)], [(78, 0), (173, 0)], [(173, 0), (173, 327)], [(173, 327), (549, 327)], [(549, 327), (549, 0)], [(549, 0), (644, 0)], [(644, 0), (644, 714)], [(644, 714), (549, 714)], [(549, 714), (549, 407)], [(549, 407), (173, 407)], [(173, 407), (173, 714)], [(173, 714), (78, 714)]]]
xContours = [[[(248, 367), (0, 0)], [(0, 0), (106, 0)], [(106, 0), (304, 295)], [(304, 295), (496, 0)], [(496, 0), (612, 0)], [(612, 0), (361, 367)], [(361, 367), (597, 714)], [(597, 714), (491, 714)], [(491, 714), (305, 435)], [(305, 435), (127, 714)], [(127, 714), (13, 714)], [(13, 714), (248, 367)]]]

newYorkHContours = [[[(414, 155), (414, 1289)], ((414, 1289), (414, 1331), (424.0, 1354.0)), ((424.0, 1354.0), (434, 1377), (463.5, 1389.0)), ((463.5, 1389.0), (493, 1401), (550, 1409)), [(550, 1409), (550, 1444)], [(550, 1444), (56, 1444)], [(56, 1444), (56, 1410)], ((56, 1410), (118, 1401), (148.0, 1388.5)), ((148.0, 1388.5), (178, 1376), (188.0, 1351.5)), ((188.0, 1351.5), (198, 1327), (198, 1283)), [(198, 1283), (198, 161)], ((198, 161), (198, 117), (188.0, 92.5)), ((188.0, 92.5), (178, 68), (148.0, 55.5)), ((148.0, 55.5), (118, 43), (56, 34)), [(56, 34), (56, 0)], [(56, 0), (550, 0)], [(550, 0), (550, 34)], ((550, 34), (493, 43), (463.5, 55.0)), ((463.5, 55.0), (434, 67), (424.0, 90.0)), ((424.0, 90.0), (414, 113), (414, 155))], [[(1352, 161), (1352, 1283)], ((1352, 1283), (1352, 1328), (1362.5, 1352.0)), ((1362.5, 1352.0), (1373, 1376), (1403.5, 1388.5)), ((1403.5, 1388.5), (1434, 1401), (1494, 1410)), [(1494, 1410), (1494, 1444)], [(1494, 1444), (1000, 1444)], [(1000, 1444), (1000, 1410)], ((1000, 1410), (1059, 1401), (1088.0, 1389.0)), ((1088.0, 1389.0), (1117, 1377), (1126.5, 1354.5)), ((1126.5, 1354.5), (1136, 1332), (1136, 1289)), [(1136, 1289), (1136, 155)], ((1136, 155), (1136, 113), (1126.5, 90.0)), ((1126.5, 90.0), (1117, 67), (1088.0, 55.0)), ((1088.0, 55.0), (1059, 43), (1000, 34)), [(1000, 34), (1000, 0)], [(1000, 0), (1494, 0)], [(1494, 0), (1494, 34)], ((1494, 34), (1434, 43), (1403.5, 55.5)), ((1403.5, 55.5), (1373, 68), (1362.5, 92.5)), ((1362.5, 92.5), (1352, 117), (1352, 161))], [[(306, 717), (1244, 717)], [(1244, 717), (1244, 762)], [(1244, 762), (306, 762)], [(306, 762), (306, 717)]]]

hBounds = BoundsRectangle.fromCoutours(hContours)
hCenter = hBounds.centerPoint
hHeight = hBounds.height

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
    print(f"slope(l0) = {slope(l0)}, slope(l1) = {slope(l1)}, slope(l2) = {slope(l2)}, slope([p2, p0]) = {slope([p2, p0])}")
    print(f"midpoint(l0) = {midpoint(l0)}, midpoint(l1) = {midpoint(l1)}, midpoint(l2) = {midpoint(l2)}")
    print(f"intersection([(0,1), (4,5)], [(4, 2), (0,4)]) = {intersectionPoint([(0,1), (4,5)], [(4, 2), (0,4)])}")
    print(f"intersectionPoint(l0, l1) = {intersectionPoint(l0, l1)}")
    print(f"intersectionPoint(l0, l2) = {intersectionPoint(l0, l2)}")
    print(f"intersectionPoint(l1, l2) = {intersectionPoint(l1, l2)}")
    print(f"intersectionPoint(l3, l4) = {intersectionPoint(l3, l4)}")

    print(pointOnLine((150, 200), l2))
    print(pointOnLine((-300, -400), l2))
    print()

    hVerticals = verticalLinesCrossing(hContours[0], hBounds.height / 4)
    hStroke = BoundsRectangle(*hVerticals[0], *hVerticals[1])
    print(f"vertical stroke width of Helvetica Neue H = {hStroke.width}")

    hHorizontals = horizontalLinesCrossing(hContours[0], hBounds.width / 2)
    vStroke = BoundsRectangle(*hHorizontals[0], *hHorizontals[1])
    print(f"horizontal stroke width of Helvetica Neue H = {vStroke.height}")
    print()

    diagonals = list(filter(lambda s: not isHorizontal(s), xContours[0]))
    diag_25 = list(filter(lambda s: crossesY(s, hBounds.height / 4), diagonals))
    diag_75 = list(filter(lambda s: crossesY(s, hBounds.height * .75), diagonals))

    print(f"diagonal strokes of Helvetica Neue X = {diagonals}")
    print()

    nyhBounds =  BoundsRectangle.fromCoutours(newYorkHContours)
    newYorkHFlat = flatten(newYorkHContours)

    newYorkHVert = verticalLinesCrossing(newYorkHFlat, nyhBounds.height / 4)
    vStroke = BoundsRectangle(*newYorkHVert[0], *newYorkHVert[1])
    print(f"vertical stroke width of New York H = {vStroke.width}")

    newYorkHHoriz = horizontalLinesCrossing(newYorkHFlat, nyhBounds.width / 2)
    hStroke = BoundsRectangle(*newYorkHHoriz[0], *newYorkHHoriz[1])
    print(f"horizontal stroke width of New York H = {hStroke.height}")
    print(f"intersection of vertical and horizontal strokes = {vStroke.intersection(hStroke)}")

if __name__ == "__main__":
    test()
