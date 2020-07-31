"""\
Utilities for manupulating outline paths and segments

Created on July 7, 2020

@author Eric Mader
"""

import math
from FontDocTools.Color import Color

class GTColor(Color):
    def __init__(self, red, green, blue):
        Color.__init__(self, red, green, blue)

    # X11 colors plus SVG 1.0 gray/grey variants
    # from https://www.w3.org/TR/css-color-3/#html4
    _keywords = {
        'aliceblue': (240, 248, 255),
        'antiquewhite': (250, 235, 215),
        'aqua': (0, 255, 255),
        'aquamarine': (127, 255, 212),
        'azure': (240, 255, 255),
        'beige': (245, 245, 220),
        'bisque': (255, 228, 196),
        'black': (0, 0, 0),
        'blanchedalmond': (255, 235, 205),
        'blue': (0, 0, 255),
        'blueviolet': (138, 43, 226),
        'brown': (165, 42, 42),
        'burlywood': (222, 184, 135),
        'cadetblue': (95, 158, 160),
        'chartreuse': (127, 255, 0),
        'chocolate': (210, 105, 30),
        'coral': (255, 127, 80),
        'cornflowerblue': (100, 149, 237),
        'cornsilk': (255, 248, 220),
        'crimson': (220, 20, 60),
        'cyan': (0, 255, 255),
        'darkblue': (0, 0, 139),
        'darkcyan': (0, 139, 139),
        'darkgoldenrod': (184, 134, 11),
        'darkgray': (169, 169, 169),
        'darkgreen': (0, 100, 0),
        'darkgrey': (169, 169, 169),
        'darkkhaki': (189, 183, 107),
        'darkmagenta': (139, 0, 139),
        'darkolivegreen': (85, 107, 47),
        'darkorange': (255, 140, 0),
        'darkorchid': (153, 50, 204),
        'darkred': (139, 0, 0),
        'darksalmon': (233, 150, 122),
        'darkseagreen': (143, 188, 143),
        'darkslateblue': (72, 61, 139),
        'darkslategray': (47, 79, 79),
        'darkslategrey': (47, 79, 79),
        'darkturquoise': (0, 206, 209),
        'darkviolet': (148, 0, 211),
        'deeppink': (255, 20, 147),
        'deepskyblue': (0, 191, 255),
        'dimgray': (105, 105, 105),
        'dimgrey': (105, 105, 105),
        'dodgerblue': (30, 144, 255),
        'firebrick': (178, 34, 34),
        'floralwhite': (255, 250, 240),
        'forestgreen': (34, 139, 34),
        'fuchsia': (255, 0, 255),
        'gainsboro': (220, 220, 220),
        'ghostwhite': (248, 248, 255),
        'gold': (255, 215, 0),
        'goldenrod': (218, 165, 32),
        'gray': (128, 128, 128),
        'green': (0, 128, 0),
        'greenyellow': (173, 255, 47),
        'grey': (128, 128, 128),
        'honeydew': (240, 255, 240),
        'hotpink': (255, 105, 180),
        'indianred': (205, 92, 92),
        'indigo': (75, 0, 130),
        'ivory': (255, 255, 240),
        'khaki': (240, 230, 140),
        'lavender': (230, 230, 250),
        'lavenderblush': (255, 240, 245),
        'lawngreen': (124, 252, 0),
        'lemonchiffon': (255, 250, 205),
        'lightblue': (173, 216, 230),
        'lightcoral': (240, 128, 128),
        'lightcyan': (224, 255, 255),
        'lightgoldenrodyellow': (250, 250, 210),
        'lightgray': (211, 211, 211),
        'lightgreen': (144, 238, 144),
        'lightgrey': (211, 211, 211),
        'lightpink': (255, 182, 193),
        'lightsalmon': (255, 160, 122),
        'lightseagreen': (32, 178, 170),
        'lightskyblue': (135, 206, 250),
        'lightslategray': (119, 136, 153),
        'lightslategrey': (119, 136, 153),
        'lightsteelblue': (176, 196, 222),
        'lightyellow': (255, 255, 224),
        'lime': (0, 255, 0),
        'limegreen': (50, 205, 50),
        'linen': (250, 240, 230),
        'magenta': (255, 0, 255),
        'maroon': (128, 0, 0),
        'mediumaquamarine': (102, 205, 170),
        'mediumblue': (0, 0, 205),
        'mediumorchid': (186, 85, 211),
        'mediumpurple': (147, 112, 219),
        'mediumseagreen': (60, 179, 113),
        'mediumslateblue': (123, 104, 238),
        'mediumspringgreen': (0, 250, 154),
        'mediumturquoise': (72, 209, 204),
        'mediumvioletred': (199, 21, 133),
        'midnightblue': (25, 25, 112),
        'mintcream': (245, 255, 250),
        'mistyrose': (255, 228, 225),
        'moccasin': (255, 228, 181),
        'navajowhite': (255, 222, 173),
        'navy': (0, 0, 128),
        'oldlace': (253, 245, 230),
        'olive': (128, 128, 0),
        'olivedrab': (107, 142, 35),
        'orange': (255, 165, 0),
        'orangered': (255, 69, 0),
        'orchid': (218, 112, 214),
        'palegoldenrod': (238, 232, 170),
        'palegreen': (152, 251, 152),
        'paleturquoise': (175, 238, 238),
        'palevioletred': (219, 112, 147),
        'papayawhip': (255, 239, 213),
        'peachpuff': (255, 218, 185),
        'peru': (205, 133, 63),
        'pink': (255, 192, 203),
        'plum': (221, 160, 221),
        'powderblue': (176, 224, 230),
        'purple': (128, 0, 128),
        'red': (255, 0, 0),
        'rosybrown': (188, 143, 143),
        'royalblue': (65, 105, 225),
        'saddlebrown': (139, 69, 19),
        'salmon': (250, 128, 114),
        'sandybrown': (244, 164, 96),
        'seagreen': (46, 139, 87),
        'seashell': (255, 245, 238),
        'sienna': (160, 82, 45),
        'silver': (192, 192, 192),
        'skyblue': (135, 206, 235),
        'slateblue': (106, 90, 205),
        'slategray': (112, 128, 144),
        'slategrey': (112, 128, 144),
        'snow': (255, 250, 250),
        'springgreen': (0, 255, 127),
        'steelblue': (70, 130, 180),
        'tan': (210, 180, 140),
        'teal': (0, 128, 128),
        'thistle': (216, 191, 216),
        'tomato': (255, 99, 71),
        'turquoise': (64, 224, 208),
        'violet': (238, 130, 238),
        'wheat': (245, 222, 179),
        'white': (255, 255, 255),
        'whitesmoke': (245, 245, 245),
        'yellow': (255, 255, 0),
        'yellowgreen': (154, 205, 50)
    }

    @classmethod
    def _forKeyword(cls, color):
        """\
         Return a new Color object for the given color keyword.
         Return None if the given string doesn’t consist of Unicode “Letter” characters.
        """
        if not color.isalpha():
            return None
        color = color.lower()
        if color in GTColor._keywords:
            (red, green, blue) = GTColor._keywords[color]
            return GTColor(red, green, blue)
        raise ValueError(f"Unrecognized color keyword: {color}")

    @classmethod
    def fromName(cls, name):
        return cls._forKeyword(name)

class GTBoundsRectangle(object):
    def __init__(self, *points):
        right = top = -32768
        left = bottom = 32768

        for point in points:
            px, py = point
            left = min(left, px)
            right = max(right, px)
            bottom = min(bottom, py)
            top = max(top, py)

        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

    @staticmethod
    def fromContour(contour):
        bounds = GTBoundsRectangle()
        for segment in contour:
            bounds = bounds.union(GTBoundsRectangle(*segment))

        return bounds

    @staticmethod
    def fromCoutours(contours):
        bounds = GTBoundsRectangle()
        for contour in contours:
            bounds = bounds.union(GTBoundsRectangle.fromContour(contour))

        return bounds

    def __str__(self):
        return f"[({self.left}, {self.bottom}), ({self.right}, {self.top})]"

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.top - self.bottom

    @property
    def area(self):
        return self.width * self.height

    @property
    def diagonal(self):
        return [(self.right, self.bottom), (self.left, self.top)]

    @property
    def centerPoint(self):
        return midpoint(self.diagonal)

    @property
    def points(self):
        return (self.left, self.bottom, self.right, self.top)

    def yFromBottom(self, percent):
        return self.bottom + self.height * percent

    def xFromLeft(self, percent):
        return self.left + self.width * percent

    def enclosesPoint(self, point):
        px, py = point

        return self.left <= px <= self.right and self.bottom <= py <= self.top

    def crossesX(self, x):
        return self.left <= x <= self.right

    def crossesY(self, y):
        return self.bottom <= y <= self.top

    def union(self, other):
        newLeft = min(self.left, other.left)
        newTop = max(self.top, other.top)
        newRight = max(self.right, other.right)
        newBottom = min(self.bottom, other.bottom)

        return GTBoundsRectangle((newLeft, newBottom), (newRight, newTop))

    def intersection(self, other):
        newLeft = max(self.left, other.left)
        newTop = min(self.top, other.top)
        newRight = min(self.right, other.right)
        newBottom = max(self.bottom, other.bottom)

        if newRight < newLeft or newTop < newBottom: return None  # maybe want <=, >=?
        return GTBoundsRectangle((newLeft, newBottom), (newRight, newTop))

    def rotateAbout(self, about):
        rotatedLine = rotateSegmentAbout(self.diagonal, about)
        return GTBoundsRectangle(*rotatedLine)


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
    return math.hypot(*getDeltas(segment))

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

    b1 = GTBoundsRectangle(*l1)
    b2 = GTBoundsRectangle(*l2)

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

def lines(contours):
    l = []
    for contour in contours:
        for segment in contour:
            if len(segment) == 2:
                l.append(segment)

    return l

def linesCrossingY(contours, y):
    return list(filter(lambda s: crossesY(s, y), sortByX(lines(contours))))

def sortByX(contour):
    return sorted(contour, key=lambda s: s[0][0])

def sortByY(contour):
    return sorted(contour, key=lambda s: s[0][1])

def sortByLength(contour, longestFirst=False):
    return sorted(contour, key=lambda l: length(l), reverse=longestFirst)

def crossesY(line, y):
    return GTBoundsRectangle(*line).crossesY(y)

def crossesX(line, x):
    return GTBoundsRectangle(*line).crossesX(x)

def verticalStrokeWidth(contours, atHeight):
    verticals = verticalLinesCrossing(contours, atHeight)
    vStroke = GTBoundsRectangle(*verticals[0], *verticals[1])
    return vStroke.width

def horizontalStrokeWidth(contours, atWidth):
    horizontals = horizontalLinesCrossing(contours, atWidth)
    hStroke = GTBoundsRectangle(*horizontals[0], *horizontals[1])
    return hStroke.height

# There must be a better way to do this...
def pointOnLine(point, line):
    bounds = GTBoundsRectangle(*line)

    return bounds.enclosesPoint(point) and slope(line) == slope([line[0], point])

class GTTransform(object):
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
            result.append(GTTransform.multiplyRowByMatrix(row, m2))

        return result

    @staticmethod
    def concatenateMatrices(*matrices):
        concatenation = matrices[0]
        for matrix in matrices[1:]:
            concatenation = GTTransform.multiplyMatrixByMatrix(concatenation, matrix)

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
        self._transform = GTTransform.concatenateMatrices(*matrices)

    @staticmethod
    def _matrix(a=1.0, b=0.0, c=0.0, d=1.0, m=0.0, n=0.0, p=0.0, q=0.0, s=1.0):
        return [
            [a, b, p],
            [c, d, q],
            [m, n, s]]

    @staticmethod
    def _identityMatrix():
        return GTTransform._matrix()

    @staticmethod
    def _scaleMatrix(sx=1.0, sy=1.0):
        return GTTransform._matrix(a=sx, c=sy)

    @staticmethod
    def _translateMatrix(fromPoint, toPoint):
        fpx, fpy = fromPoint
        tpx, tpy = toPoint
        tx = tpx - fpx
        ty = tpy - fpy

        return GTTransform._matrix(m=tx, n=ty)

    @staticmethod
    def _rotationMatrix(degrees, ccw=True):
        st = GTTransform.sin(degrees)  # sin(theta)
        ct = GTTransform.cos(degrees)  # cos(theta)

        return GTTransform._matrix(a=ct, b=st, c=-st, d=ct) if ccw else GTTransform._matrix(a=ct, b=-st, c=st, d=ct)

    @staticmethod
    def _perspectiveMatrix(p, q, s=1):
        return GTTransform._matrix(p=p, q=q, s=s)

    @property
    def transform(self):
        return self._transform

    @classmethod
    def rotation(cls, about, degrees=90, ccw=True):
        # Translate about point of origin
        m1 = GTTransform._translateMatrix(about, (0, 0))

        # rotate
        m2 = GTTransform._rotationMatrix(degrees, ccw)

        # translate back to about point
        m3 = GTTransform._translateMatrix((0, 0), about)

        return GTTransform(m1, m2, m3)

    def applyToPoint(self, point):
        px, py = point
        rp = GTTransform.multiplyRowByMatrix([px, py, 1], self.transform)

        return (rp[0]/rp[2], rp[1]/rp[2])


    def applyToSegment(self, segment):
        transformed = []
        for point in segment:
            transformed.append(self.applyToPoint(point))

        return transformed


    def applyToContour(self, contour):
        transformed = []
        for segment in contour:
            transformed.append(self.applyToSegment(segment))

        return transformed


    def applyToContours(self, contours):
        transformed = []
        for contour in contours:
            transformed.append(self.applyToContour(contour))

        return transformed

def rotatePointAbout(point, about, degrees=90, ccw=True):
    rt = GTTransform.rotation(about, degrees, ccw)

    return rt.applyToPoint(point)

def rotateSegmentAbout(segment, about, degrees=90, ccw=True):
    rt = GTTransform.rotation(about, degrees, ccw)

    return rt.applyToSegment(segment)

def rotateContourAbout(contour, about, degrees=90, ccw=True):
    rt = GTTransform.rotation(about, degrees, ccw)

    return rt.applyToContour(contour)

def rotateContoursAbout(contours, about, degrees=90, ccw=True):
    rt = GTTransform.rotation(about, degrees, ccw)

    return rt.applyToContours(contours)

def toMicros(funits, unitsPerEM):
    return funits * 1000 / unitsPerEM

# Helvetica Neue H
hContours = [[[(78, 714), (78, 0)], [(78, 0), (173, 0)], [(173, 0), (173, 327)], [(173, 327), (549, 327)], [(549, 327), (549, 0)], [(549, 0), (644, 0)], [(644, 0), (644, 714)], [(644, 714), (549, 714)], [(549, 714), (549, 407)], [(549, 407), (173, 407)], [(173, 407), (173, 714)], [(173, 714), (78, 714)]]]
xContours = [[[(248, 367), (0, 0)], [(0, 0), (106, 0)], [(106, 0), (304, 295)], [(304, 295), (496, 0)], [(496, 0), (612, 0)], [(612, 0), (361, 367)], [(361, 367), (597, 714)], [(597, 714), (491, 714)], [(491, 714), (305, 435)], [(305, 435), (127, 714)], [(127, 714), (13, 714)], [(13, 714), (248, 367)]]]
helveticaNeueUPM = 1000

newYorkHContours = [[[(414, 155), (414, 1289)], [(414, 1289), (414, 1331), (424.0, 1354.0)], [(424.0, 1354.0), (434, 1377), (463.5, 1389.0)], [(463.5, 1389.0), (493, 1401), (550, 1409)], [(550, 1409), (550, 1444)], [(550, 1444), (56, 1444)], [(56, 1444), (56, 1410)], [(56, 1410), (118, 1401), (148.0, 1388.5)], [(148.0, 1388.5), (178, 1376), (188.0, 1351.5)], [(188.0, 1351.5), (198, 1327), (198, 1283)], [(198, 1283), (198, 161)], [(198, 161), (198, 117), (188.0, 92.5)], [(188.0, 92.5), (178, 68), (148.0, 55.5)], [(148.0, 55.5), (118, 43), (56, 34)], [(56, 34), (56, 0)], [(56, 0), (550, 0)], [(550, 0), (550, 34)], [(550, 34), (493, 43), (463.5, 55.0)], [(463.5, 55.0), (434, 67), (424.0, 90.0)], [(424.0, 90.0), (414, 113), (414, 155)]], [[(1352, 161), (1352, 1283)], [(1352, 1283), (1352, 1328), (1362.5, 1352.0)], [(1362.5, 1352.0), (1373, 1376), (1403.5, 1388.5)], [(1403.5, 1388.5), (1434, 1401), (1494, 1410)], [(1494, 1410), (1494, 1444)], [(1494, 1444), (1000, 1444)], [(1000, 1444), (1000, 1410)], [(1000, 1410), (1059, 1401), (1088.0, 1389.0)], [(1088.0, 1389.0), (1117, 1377), (1126.5, 1354.5)], [(1126.5, 1354.5), (1136, 1332), (1136, 1289)], [(1136, 1289), (1136, 155)], [(1136, 155), (1136, 113), (1126.5, 90.0)], [(1126.5, 90.0), (1117, 67), (1088.0, 55.0)], [(1088.0, 55.0), (1059, 43), (1000, 34)], [(1000, 34), (1000, 0)], [(1000, 0), (1494, 0)], [(1494, 0), (1494, 34)], [(1494, 34), (1434, 43), (1403.5, 55.5)], [(1403.5, 55.5), (1373, 68), (1362.5, 92.5)], [(1362.5, 92.5), (1352, 117), (1352, 161)]], [[(306, 717), (1244, 717)], [(1244, 717), (1244, 762)], [(1244, 762), (306, 762)], [(306, 762), (306, 717)]]]
newYorkpContours = [[[(1080, 492), (1080, 649), (1023.5, 759.0)], [(1023.5, 759.0), (967, 869), (875.0, 927.0)], [(875.0, 927.0), (783, 985), (677, 985)], [(677, 985), (571, 985), (483.5, 935.0)], [(483.5, 935.0), (396, 885), (356, 802)], [(356, 802), (356, 978)], [(356, 978), (40, 942)], [(40, 942), (40, 912)], [(40, 912), (99, 894)], [(99, 894), (140, 881), (150.5, 866.5)], [(150.5, 866.5), (161, 852), (161, 812)], [(161, 812), (161, -328)], [(161, -328), (161, -361), (153.0, -379.5)], [(153.0, -379.5), (145, -398), (119.5, -408.0)], [(119.5, -408.0), (94, -418), (40, -426)], [(40, -426), (40, -460)], [(40, -460), (490, -460)], [(490, -460), (490, -426)], [(490, -426), (431, -418), (403.0, -407.0)], [(403.0, -407.0), (375, -396), (366.5, -375.0)], [(366.5, -375.0), (358, -354), (358, -316)], [(358, -316), (358, 105)], [(358, 105), (392, 50), (458.0, 16.0)], [(458.0, 16.0), (524, -18), (613, -18)], [(613, -18), (743, -18), (848.5, 46.0)], [(848.5, 46.0), (954, 110), (1017.0, 224.5)], [(1017.0, 224.5), (1080, 339), (1080, 492)]], [[(875, 468), (875, 276), (790.5, 158.0)], [(790.5, 158.0), (706, 40), (568, 40)], [(568, 40), (498, 40), (440.0, 73.0)], [(440.0, 73.0), (382, 106), (358, 155)], [(358, 155), (358, 771)], [(358, 771), (392, 830), (448.0, 861.0)], [(448.0, 861.0), (504, 892), (582, 892)], [(582, 892), (710, 892), (792.5, 777.0)], [(792.5, 777.0), (875, 662), (875, 468)]]]
newYorkUPM = 2048

hBounds = GTBoundsRectangle.fromCoutours(hContours)
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

    print(f"vertical stroke width of Helvetica Neue H = {toMicros(verticalStrokeWidth(hContours, hBounds.yFromBottom(0.25)), helveticaNeueUPM)} micro")
    print(f"horizontal stroke width of Helvetica Neue H = {toMicros(horizontalStrokeWidth(hContours, hBounds.xFromLeft(0.50)), helveticaNeueUPM)} micro")
    print()

    diagonals = list(filter(lambda s: not isHorizontalLine(s), xContours[0]))
    diag_25 = list(filter(lambda s: crossesY(s, hBounds.yFromBottom(0.25)), diagonals))
    diag_75 = list(filter(lambda s: crossesY(s, hBounds.yFromBottom(0.75)), diagonals))

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
    print(f"stroke width of Helvetica Neue X = {toMicros(xWidth, helveticaNeueUPM)} micro")

    print(f"diagonal strokes of Helvetica Neue X = {diagonals}")
    print()

    nyhBounds =  GTBoundsRectangle.fromCoutours(newYorkHContours)
    print(f"vertical stroke width of New York H = {toMicros(verticalStrokeWidth(newYorkHContours, nyhBounds.yFromBottom(0.25)), newYorkUPM)} micro")
    print(f"horizontal stroke width of New York H = {toMicros(horizontalStrokeWidth(newYorkHContours, nyhBounds.xFromLeft(0.50)), newYorkUPM)} micro")
    # print(f"intersection of vertical and horizontal strokes = {vStroke.intersection(hStroke)}")
    print()

    nypBounds = GTBoundsRectangle.fromCoutours(newYorkpContours)
    print(f"vertical stroke width of New York p = {toMicros(verticalStrokeWidth(newYorkpContours, nypBounds.yFromBottom(0.25)), newYorkUPM)} micro")
    print()

    #
    # Colon method of determining the italic angle.
    # (Assumes that the colon glyph is two contours)
    # Draw a line between the center points of the bounding boxes of each contour.
    # The angle is 90 - the arc-tangent of the slope of the line.
    #
    nyItalicColonContours = [[[(249, -17), (283, -17), (311.0, -0.5)], [(311.0, -0.5), (339, 16), (355.5, 44.5)], [(355.5, 44.5), (372, 73), (372, 107)], [(372, 107), (372, 157), (336.0, 193.0)], [(336.0, 193.0), (300, 229), (248, 229)], [(248, 229), (214, 229), (186.0, 212.5)], [(186.0, 212.5), (158, 196), (141.5, 167.5)], [(141.5, 167.5), (125, 139), (125, 104)], [(125, 104), (125, 55), (161.0, 19.0)], [(161.0, 19.0), (197, -17), (249, -17)]], [[(401, 698), (435, 698), (463.0, 714.5)], [(463.0, 714.5), (491, 731), (507.5, 759.5)], [(507.5, 759.5), (524, 788), (524, 822)], [(524, 822), (524, 872), (488.0, 908.0)], [(488.0, 908.0), (452, 944), (400, 944)], [(400, 944), (366, 944), (338.0, 927.5)], [(338.0, 927.5), (310, 911), (293.5, 882.5)], [(293.5, 882.5), (277, 854), (277, 819)], [(277, 819), (277, 770), (313.0, 734.0)], [(313.0, 734.0), (349, 698), (401, 698)]]]
    lowerDot = nyItalicColonContours[0]
    upperDot = nyItalicColonContours[1]
    lowerBounds = GTBoundsRectangle.fromContour(lowerDot)
    upperBounds = GTBoundsRectangle.fromContour(upperDot)
    lowerCenter = lowerBounds.centerPoint
    upperCenter = upperBounds.centerPoint
    italicSlope = slope([lowerCenter, upperCenter])
    angle = 90.0 - math.degrees(math.atan(italicSlope))
    print(f"italic angle for New York Italic from colon method = {angle}")
    print()

    nyItalicpContours = [[[(1069, 635), (1069, 741), (1037.0, 819.5)], [(1037.0, 819.5), (1005, 898), (948.0, 941.5)], [(948.0, 941.5), (891, 985), (816, 985)], [(816, 985), (710, 985), (627.0, 913.0)], [(627.0, 913.0), (544, 841), (498, 704)], [(498, 704), (557, 979)], [(557, 979), (231, 938)], [(231, 938), (224, 905)], [(224, 905), (285, 892)], [(285, 892), (323, 882), (333.0, 865.0)], [(333.0, 865.0), (343, 848), (335, 810)], [(335, 810), (94, -327)], [(94, -327), (87, -358), (74.5, -376.0)], [(74.5, -376.0), (62, -394), (33.0, -404.5)], [(33.0, -404.5), (4, -415), (-53, -425)], [(-53, -425), (-60, -460)], [(-60, -460), (407, -460)], [(407, -460), (414, -425)], [(414, -425), (350, -414), (320.0, -403.5)], [(320.0, -403.5), (290, -393), (284.0, -375.0)], [(284.0, -375.0), (278, -357), (284, -324)], [(284, -324), (369, 78)], [(369, 78), (387, 44), (435.5, 13.0)], [(435.5, 13.0), (484, -18), (572, -18)], [(572, -18), (686, -18), (777.5, 37.0)], [(777.5, 37.0), (869, 92), (934.0, 185.0)], [(934.0, 185.0), (999, 278), (1034.0, 394.5)], [(1034.0, 394.5), (1069, 511), (1069, 635)]], [[(871, 653), (871, 551), (850.0, 443.5)], [(850.0, 443.5), (829, 336), (786.5, 244.0)], [(786.5, 244.0), (744, 152), (680.5, 95.0)], [(680.5, 95.0), (617, 38), (532, 38)], [(532, 38), (471, 38), (431.5, 64.5)], [(431.5, 64.5), (392, 91), (381, 128)], [(381, 128), (482, 605)], [(482, 605), (517, 745), (586.0, 822.0)], [(586.0, 822.0), (655, 899), (728, 899)], [(728, 899), (796, 899), (833.5, 842.0)], [(833.5, 842.0), (871, 785), (871, 653)]]]
    nyipBounds = GTBoundsRectangle.fromCoutours(nyItalicpContours)
    nyipLines = linesCrossingY(nyItalicpContours, nyipBounds.yFromBottom(0.25))
    nyipLinesByLength = sortByLength(nyipLines, longestFirst=True)
    italicSlope = slope(nyipLinesByLength[0])
    angle = 90.0 - math.degrees(math.atan(italicSlope))
    print(f"italic angle for New York Italic from stem method = {angle}")
    print()
    midPoint = midpoint(nyipLines[0])
    perpendicular = rotateSegmentAbout(nyipLines[0], midPoint)
    intersection = intersectionPoint(perpendicular, nyipLines[1])
    xWidth = length([midPoint, intersection])
    print(f"stroke width of New York Italic p = {toMicros(xWidth, newYorkUPM)} micro")
    print()

    helveticaNeueItalicColonContours = [[[(211, 406), (234, 517)], [(234, 517), (122, 517)], [(122, 517), (99, 406)], [(99, 406), (211, 406)]], [[(37, 111), (15, 0)], [(15, 0), (127, 0)], [(127, 0), (150, 111)], [(150, 111), (37, 111)]]]
    helveticaNeueItalicpContours = [[[(102, 517), (-48, -197)], [(-48, -197), (35, -197)], [(35, -197), (90, 79)], [(90, 79), (92, 79)], [(92, 79), (99, 53), (116.5, 35.5)], [(116.5, 35.5), (134, 18), (156.5, 7.5)], [(156.5, 7.5), (179, -3), (204.5, -7.0)], [(204.5, -7.0), (230, -11), (253, -11)], [(253, -11), (321, -11), (374.5, 18.0)], [(374.5, 18.0), (428, 47), (464.5, 94.0)], [(464.5, 94.0), (501, 141), (520.5, 199.5)], [(520.5, 199.5), (540, 258), (540, 317)], [(540, 317), (540, 364), (527.0, 403.0)], [(527.0, 403.0), (514, 442), (488.0, 470.0)], [(488.0, 470.0), (462, 498), (424.5, 513.5)], [(424.5, 513.5), (387, 529), (337, 529)], [(337, 529), (285, 529), (244.5, 511.0)], [(244.5, 511.0), (204, 493), (166, 443)], [(166, 443), (164, 443)], [(164, 443), (182, 517)], [(182, 517), (102, 517)]], [[(455, 317), (455, 274), (442.0, 229.0)], [(442.0, 229.0), (429, 184), (403.0, 147.0)], [(403.0, 147.0), (377, 110), (339.0, 86.5)], [(339.0, 86.5), (301, 63), (250, 63)], [(250, 63), (187, 63), (153.5, 101.0)], [(153.5, 101.0), (120, 139), (120, 197)], [(120, 197), (120, 238), (133.5, 283.0)], [(133.5, 283.0), (147, 328), (172.5, 366.0)], [(172.5, 366.0), (198, 404), (236.0, 429.0)], [(236.0, 429.0), (274, 454), (322, 454)], [(322, 454), (392, 454), (423.5, 417.0)], [(423.5, 417.0), (455, 380), (455, 317)]]]

    lowerDot = helveticaNeueItalicColonContours[0]
    upperDot = helveticaNeueItalicColonContours[1]
    lowerBounds = GTBoundsRectangle.fromContour(lowerDot)
    upperBounds = GTBoundsRectangle.fromContour(upperDot)
    lowerCenter = lowerBounds.centerPoint
    upperCenter = upperBounds.centerPoint
    italicSlope = slope([lowerCenter, upperCenter])
    angle = 90.0 - math.degrees(math.atan(italicSlope))
    print(f"italic angle for Helvetica Neue Italic from colon method = {angle}")
    print()

    hnipBounds = GTBoundsRectangle.fromCoutours(helveticaNeueItalicpContours)
    hnipLines = linesCrossingY(helveticaNeueItalicpContours, hnipBounds.yFromBottom(0.25))
    hnipLinesByLength = sortByLength(hnipLines, longestFirst=True)
    italicSlope = slope(hnipLinesByLength[0])
    angle = 90.0 - math.degrees(math.atan(italicSlope))
    print(f"italic angle for Helvetica Neue Italic from stem method = {angle}")
    print()
    midPoint = midpoint(hnipLines[0])
    perpendicular = rotateSegmentAbout(hnipLines[0], midPoint)
    intersection = intersectionPoint(perpendicular, hnipLines[1])
    xWidth = length([midPoint, intersection])
    print(f"stroke width of Helvetica Neue Italic p = {toMicros(xWidth, helveticaNeueUPM)} micro")
    print()

    #
    # Example 2-6 from Mathematical Elements for Computer Graphics
    # Second Edition
    #
    print("Example 2-6 from Mathematical Elements for Computer Graphics:")
    m1 = [[1, 0, 0], [0, 1, 0], [-4, -3, 1]]
    m2 = [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]
    m3 = [[1, 0, 0], [0, 1, 0], [4, 3, 1]]

    fp = GTTransform(m1, m2, m3)
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
