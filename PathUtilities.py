"""\
Utilities for manupulating outline paths and segments

Created on July 7, 2020

@author Eric Mader
"""

import math

class BoundsRectangle(object):
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

    @property
    def points(self):
        return (self.leftTop[0], self.leftTop[1], self.rightBottom[0], self.rightBottom[1])

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

    def rotateAbout(self, about):
        rotatedLine = rotateSegmentAbout([self.leftTop, self.rightBottom], about)
        return BoundsRectangle(rotatedLine[0], rotatedLine[1])


def minMax(a, b):
    return (a, b) if a <= b else (b, a)

def endPoints(segment):
    p0x, p0y = segment[0]
    p1x, p1y = segment[-1]

    return (p0x, p0y, p1x, p1y)

def getDeltas(segment):
    p0x, p0y, p1x, p1y = endPoints(segment)

    return (p1x - p0x, p1y - p0y)

def isVerticalLine(segment):
    dx, _ = getDeltas(segment)
    return len(segment) == 2 and dx == 0

def isHorizontalLine(segment):
    _, dy = getDeltas(segment)
    return len(segment) == 2 and dy == 0

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

# The result of this function cannot be used to create an SVG path...
def flatten(contours):
    return [segment for contour in contours for segment in contour]

def verticalLines(contours):
    v = []
    for contour in contours:
        for segment in contour:
            if isVerticalLine(segment):
                v.append(segment)

    return v

def verticalLinesCrossing(contours, y):
    return list(filter(lambda s: crossesY(s, y), sortByX(verticalLines(contours))))

def horizontalLines(contours):
    h = []
    for contour in contours:
        for segment in contour:
            if isHorizontalLine(segment):
                h.append(segment)

    return h

def horizontalLinesCrossing(contours, x):
    return list(filter(lambda s: crossesX(s, x), sortByY((horizontalLines(contours)))))

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

def sin(degrees):
    return round(math.sin(math.radians(degrees)), 15)

def cos(degrees):
    return round(math.cos(math.radians(degrees)), 15)

class Transform(object):
    @staticmethod
    def multiplyRowByMatrix(row, matrix):
        r1, r2, r3 = row
        m1, m2, m3 = matrix
        m11, m12, m13 = m1
        m21, m22, m23 = m2
        m31, m32, m33 = m3

        return [r1 * m11 + r2 * m21 + r3 * m31, r1 * m12 + r2 * m22 + r3 * m32, r1 * m13 + r2 * m23 + r3 * m33]

    @staticmethod
    def multiplyMatrixByMatrix(m1, m2):
        result = []
        for row in m1:
            result.append(Transform.multiplyRowByMatrix(row, m2))

        return result

    @staticmethod
    def concatenateMatrices(*matrices):
        concatenation = matrices[0]
        for matrix in matrices[1:]:
            concatenation = Transform.multiplyMatrixByMatrix(concatenation, matrix)

        return concatenation

    @staticmethod
    def sin(degrees):
        # We use round() because sin values that should be zero
        # are actually around 1e-16
        return round(math.sin(math.radians(degrees)), 15)

    @staticmethod
    def cos(degrees):
        # We use round() because cos values that should be zero
        # are actually around 1e-16
        return round(math.cos(math.radians(degrees)), 15)

    def __init__(self, *matrices):
        self._transform = Transform.concatenateMatrices(*matrices)

    @staticmethod
    def _matrix(a=1.0, b=0.0, c=0.0, d=1.0, m=0.0, n=0.0, p=0.0, q=0.0, s=1.0):
        return [
            [a, b, p],
            [c, d, q],
            [m, n, s]]

    @staticmethod
    def _identityMatrix():
        return Transform._matrix()

    @staticmethod
    def _scaleMatrix(sx=1.0, sy=1.0):
        return Transform._matrix(a=sx, c=sy)

    @staticmethod
    def _translateMatrix(fromPoint, toPoint):
        fpx, fpy = fromPoint
        tpx, tpy = toPoint
        tx = tpx - fpx
        ty = tpy - fpy

        return Transform._matrix(m=tx, n=ty)

    @staticmethod
    def _rotationMatrix(degrees):
        st = Transform.sin(degrees)  # sin(theta)
        ct = Transform.cos(degrees)  # cos(theta)

        return Transform._matrix(a=ct, b=st, c=-st, d=ct)

    @staticmethod
    def _perspectiveMatrix(p, q, s):
        return Transform._matrix(p=p, q=q, s=s)

    @property
    def transform(self):
        return self._transform

    @classmethod
    def rotation(cls, about, degrees=90):
        # Translate about point to origin
        m1 = Transform._translateMatrix(about, (0, 0))

        # rotate
        m2 = Transform._rotationMatrix(degrees)

        # translate back to about point
        m3 = Transform._translateMatrix((0, 0), about)

        return Transform(m1, m2, m3)

    def applyToPoint(self, point):
        px, py = point
        rp = Transform.multiplyRowByMatrix([px, py, 1], self.transform)

        return (rp[0]/rp[2], rp[1]/rp[2])


    def applyToSegment(self, segment):
        rotated = []
        for point in segment:
            rotated.append(self.applyToPoint(point))

        return rotated


    def applyToContour(self, contour):
        rotated = []
        for segment in contour:
            rotated.append(self.applyToSegment(segment))

        return rotated


    def applyToContours(self, contours):
        rotated = []
        for contour in contours:
            rotated.append(self.applyToContour(contour))

        return rotated

def rotatePointAbout(point, about, degrees=90):
    rt = Transform.rotation(about, degrees)

    return rt.applyToPoint(point)

def rotateSegmentAbout(segment, about, degrees=90):
    rt = Transform.rotation(about, degrees)

    return rt.applyToSegment(segment)

def rotateContourAbout(contour, about, degrees=90):
    rt = Transform.rotation(about, degrees)

    return rt.applyToContour(contour)

def rotateContoursAbout(contours, about, degrees=90):
    rt = Transform.rotation(about, degrees)

    return rt.applyToContours(contours)


# Helvetica Neue H
hContours = [[[(78, 714), (78, 0)], [(78, 0), (173, 0)], [(173, 0), (173, 327)], [(173, 327), (549, 327)], [(549, 327), (549, 0)], [(549, 0), (644, 0)], [(644, 0), (644, 714)], [(644, 714), (549, 714)], [(549, 714), (549, 407)], [(549, 407), (173, 407)], [(173, 407), (173, 714)], [(173, 714), (78, 714)]]]
xContours = [[[(248, 367), (0, 0)], [(0, 0), (106, 0)], [(106, 0), (304, 295)], [(304, 295), (496, 0)], [(496, 0), (612, 0)], [(612, 0), (361, 367)], [(361, 367), (597, 714)], [(597, 714), (491, 714)], [(491, 714), (305, 435)], [(305, 435), (127, 714)], [(127, 714), (13, 714)], [(13, 714), (248, 367)]]]

newYorkHContours = [[[(414, 155), (414, 1289)], [(414, 1289), (414, 1331), (424.0, 1354.0)], [(424.0, 1354.0), (434, 1377), (463.5, 1389.0)], [(463.5, 1389.0), (493, 1401), (550, 1409)], [(550, 1409), (550, 1444)], [(550, 1444), (56, 1444)], [(56, 1444), (56, 1410)], [(56, 1410), (118, 1401), (148.0, 1388.5)], [(148.0, 1388.5), (178, 1376), (188.0, 1351.5)], [(188.0, 1351.5), (198, 1327), (198, 1283)], [(198, 1283), (198, 161)], [(198, 161), (198, 117), (188.0, 92.5)], [(188.0, 92.5), (178, 68), (148.0, 55.5)], [(148.0, 55.5), (118, 43), (56, 34)], [(56, 34), (56, 0)], [(56, 0), (550, 0)], [(550, 0), (550, 34)], [(550, 34), (493, 43), (463.5, 55.0)], [(463.5, 55.0), (434, 67), (424.0, 90.0)], [(424.0, 90.0), (414, 113), (414, 155)]], [[(1352, 161), (1352, 1283)], [(1352, 1283), (1352, 1328), (1362.5, 1352.0)], [(1362.5, 1352.0), (1373, 1376), (1403.5, 1388.5)], [(1403.5, 1388.5), (1434, 1401), (1494, 1410)], [(1494, 1410), (1494, 1444)], [(1494, 1444), (1000, 1444)], [(1000, 1444), (1000, 1410)], [(1000, 1410), (1059, 1401), (1088.0, 1389.0)], [(1088.0, 1389.0), (1117, 1377), (1126.5, 1354.5)], [(1126.5, 1354.5), (1136, 1332), (1136, 1289)], [(1136, 1289), (1136, 155)], [(1136, 155), (1136, 113), (1126.5, 90.0)], [(1126.5, 90.0), (1117, 67), (1088.0, 55.0)], [(1088.0, 55.0), (1059, 43), (1000, 34)], [(1000, 34), (1000, 0)], [(1000, 0), (1494, 0)], [(1494, 0), (1494, 34)], [(1494, 34), (1434, 43), (1403.5, 55.5)], [(1403.5, 55.5), (1373, 68), (1362.5, 92.5)], [(1362.5, 92.5), (1352, 117), (1352, 161)]], [[(306, 717), (1244, 717)], [(1244, 717), (1244, 762)], [(1244, 762), (306, 762)], [(306, 762), (306, 717)]]]

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

    hVerticals = verticalLinesCrossing(hContours, hBounds.height / 4)
    hStroke = BoundsRectangle(*hVerticals[0], *hVerticals[1])
    print(f"vertical stroke width of Helvetica Neue H = {hStroke.width}")
    print(f"rotated point = {rotatePointAbout(hVerticals[0][1], hVerticals[0][0])}")

    hHorizontals = horizontalLinesCrossing(hContours, hBounds.width / 2)
    vStroke = BoundsRectangle(*hHorizontals[0], *hHorizontals[1])
    print(f"horizontal stroke width of Helvetica Neue H = {vStroke.height}")
    print()

    diagonals = list(filter(lambda s: not isHorizontalLine(s), xContours[0]))
    diag_25 = list(filter(lambda s: crossesY(s, hBounds.height / 4), diagonals))
    diag_75 = list(filter(lambda s: crossesY(s, hBounds.height * .75), diagonals))

    #
    # To calculate the stroke width:
    # 1) find the midpoint of the leftmost line
    # 2) rotate the line 90 degrees around the midpoint
    # 3) intersect the rotation with the 2nd line
    # 4) width is the length of the line from the midpoint to the intersection
    #
    midPoint = midpoint(diagonals[0])
    perpendicular = rotateSegmentAbout(diagonals[0], midPoint)
    intersection = intersectionPoint(perpendicular, diagonals[1])
    xWidth = length([midPoint, intersection])
    print(f"stroke width of Helvetica Neue X = {xWidth}")

    print(f"diagonal strokes of Helvetica Neue X = {diagonals}")
    print()

    nyhBounds =  BoundsRectangle.fromCoutours(newYorkHContours)

    newYorkHVert = verticalLinesCrossing(newYorkHContours, nyhBounds.height / 4)
    vStroke = BoundsRectangle(*newYorkHVert[0], *newYorkHVert[1])
    print(f"vertical stroke width of New York H = {vStroke.width}")

    newYorkHHoriz = horizontalLinesCrossing(newYorkHContours, nyhBounds.width / 2)
    hStroke = BoundsRectangle(*newYorkHHoriz[0], *newYorkHHoriz[1])
    print(f"horizontal stroke width of New York H = {hStroke.height}")
    print(f"intersection of vertical and horizontal strokes = {vStroke.intersection(hStroke)}")
    print()

    #
    # Example 2-6 from Mathematical Elements for Computer Graphics
    # Second Edition
    #
    print("Example 2-6 from Mathematical Elements for Computer Graphics:")
    m1 = [[1, 0, 0], [0, 1, 0], [-4, -3, 1]]
    m2 = [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]
    m3 = [[1, 0, 0], [0, 1, 0], [4, 3, 1]]

    fp = Transform(m1, m2, m3)
    print(f"rotation transform = {fp.transform}")
    print(f"rotation of (8, 6) = {fp.applyToPoint((8, 6))}")

    # s1 = [(253, 239), (242, 210), (216, 136), (199, 80)]
    # s2 = [(253, 239), (242, 210), (229, 173), (216, 136), (199, 80)]
    # m1 = Transform._rotationMatrix(45)
    # transform = Transform(m1)
    # r1 = transform.applyToSegment(s1)
    # r2 = transform.applyToSegment(s2)
    # print(r1)
    # print(r2)
if __name__ == "__main__":
    test()
