"""\
Plot a contour

Created June 23, 2020

@author = Eric Mader
"""

from FontDocTools import GlyphPlotterEngine
from PathUtilities import GTColor

# Add methods for drawing lines, circles, titles w/o needing to know about contexts?
class ContourPlotter(GlyphPlotterEngine.GlyphPlotterEngine):
    lastCommand = ""

    def __init__(self, bounds, poly=False):
        GlyphPlotterEngine.GlyphPlotterEngine.__init__(self)
        self._boundsAggregator.addBounds(bounds)
        self.setContentMargins(GlyphPlotterEngine.Margins(15, 15, 15, 15))
        self._poly = poly
        self._lastCommand = ""
        self._fillAttributeStack = []
        self._strokeAttributeStack = []

    def pushFillAttributes(self, color=None, opacity=None):
        self._fillAttributeStack.append((self._fillColor, self._fillOpacity))
        if color: self.setFillColor(color)
        if opacity: self.setFillOpacity(opacity)

    def popFillAttributes(self):
        color, opacity = self._fillAttributeStack.pop()
        self.setFillColor(color)
        self.setFillOpacity(opacity)

    def pushStrokeAttributes(self, width=None, color=None, opacity=None, dash=None):
        self._strokeAttributeStack.append((self._strokeWidth, self._strokeColor, self._strokeOpacity, self._strokeDash))
        if width: self.setStrokeWidth(width)
        if color: self.setStrokeColor(color)
        if opacity: self.setStrokeOpacity(opacity)
        if dash: self.setStrokeDash(dash)

    def popStrokeAtributes(self):
        width ,color, opacity, dash = self._strokeAttributeStack.pop()
        self.setStrokeWidth(width)
        self.setStrokeColor(color)
        self.setStrokeOpacity(opacity)
        self.setStrokeDash(dash)

    def pointToString(self, point):
        return " ".join([str(i) for i in point])

    def getCommand(self, command):
        if self._poly:
            if self._lastCommand != command:
                self._lastCommand = command
            else:
                command = " "

        return command

    def drawContours(self, contours, color=None, fill=False, close=True):
        if fill:
            # self._fillColor = color
            # self._fillOpacity = fill
            self.pushFillAttributes(color=color, fill=fill)
        elif color:
            self.pushStrokeAttributes(color=color)
            # self._strokeWidth = 2

        path = "<path d='"
        commands = []
        for contour in contours:
                firstPoint = contour[0][0]
                self.moveToXY(*firstPoint)
                commands.append(f"M{self.pointToString(firstPoint)}")

                for segment in contour:
                    if len(segment) == 2:
                        # a line
                        penX, penY = self._pen
                        x, y = segment[1]

                        if penX == x and penY == y:
                            continue
                        elif penX == x:
                            # vertical line
                            command = self.getCommand("V")
                            commands.append(f"{command}{y}")
                        elif penY == y:
                            # horizontal line
                            command = self.getCommand("H")
                            commands.append(f"{command}{x}")
                        else:
                            point = self.pointToString(segment[1])
                            command = self.getCommand("L")
                            commands.append(f"L{point}")
                        self._pen = (x, y)
                    elif len(segment) == 3:
                            p1 = self.pointToString(segment[1])
                            p2 = self.pointToString(segment[2])
                            command = self.getCommand("Q")
                            commands.append(f"{command}{p1} {p2}")
                            self._pen = segment[2]
                    elif len(segment) == 4:
                        p1 = self.pointToString(segment[1])
                        p2 = self.pointToString(segment[2])
                        p3 = self.pointToString(segment[3])
                        command = self.getCommand("C");
                        commands.append(f"{command}{p1} {p2} {p3}")
                        self._pen = segment[3]

                if close: commands.append("Z")

        path += "".join(commands)

        if fill:
            path += f"' {self._fillAttributes()}/>"
            self.popFillAttributes()
        else:
            path += f"' fill='none' {self._strokeAttributes()}/>"
            if color: self.popStrokeAtributes()

        self._content.append(path)

    def drawPointsAsSegments(self, points, color=None):
        if color: self.pushStrokeAttributes(color=color)  # used to set stroke width to 2...

        path = "<path d='"
        commands = []
        firstPoint = points[0]
        self.moveToXY(*firstPoint)
        commands.append(f"M{self.pointToString(firstPoint)}")
        command = "L"

        for point in points[1:]:
            x, y = point
            penX, penY = self._pen

            if penX == x and penY == y:
                continue

            commands.append(f"{command}{self.pointToString(point)}")
            self._pen = (x, y)
            command = " "

        path += "".join(commands)

        path += f"' fill='none' {self._strokeAttributes()}/>"
        self._content.append(path)
        if color: self.popStrokeAtributes()

    def drawPointsAsCircles(self, points, radius, color=None, fill=True):
        if color:
            if fill:
                self._fillColor = color
            else:
                self.pushStrokeAttributes(color=color)

        paintMode = GlyphPlotterEngine.PaintMode.fill if fill else GlyphPlotterEngine.PaintMode.stroke

        for point in points:
            x, y = point
            self.drawCircle(GlyphPlotterEngine.CoordinateSystem.content, x, y, radius, paintMode)

        if color and not fill: self.popStrokeAtributes()

    def drawCurve(self, segment, color=None):
        self.drawContours([[segment]], color=color, fill=False, close=False)

    def drawText(self, x, y, alignment, text, margin=True):
        coordinates = GlyphPlotterEngine.CoordinateSystem.contentMargins if margin else GlyphPlotterEngine.CoordinateSystem.content
        self.drawLabel(coordinates, x, y, 0, alignment, text)

    colorLightGrey = GTColor.fromName("lightgrey")
    colorBlack = GTColor.fromName("black")

    def drawSkeleton(self, curve, lineColor=colorLightGrey, pointColor=colorBlack):
        points = curve.controlPoints
        self._strokWidth = 1
        self.drawPointsAsSegments(points, lineColor)
        self.drawPointsAsCircles(points, 2, pointColor, fill=False)

        if pointColor: self.pushFillAttributes(color=pointColor)
        self.setLabelFontSize(6, 6)
        for point in points:
            x, y = point
            self.drawText(x + 4, y - 4, "left", f"({x}, {y})", margin=False)
        if pointColor: self.popFillAttributes()

    def drawHull(self, curve, t, lineColor=colorLightGrey, pointColor=colorBlack):
        self.drawSkeleton(curve, lineColor, pointColor)

        if lineColor: self.pushStrokeAttributes(color=lineColor)
        order = curve.order
        hull = curve.hull(t)
        start = len(curve.controlPoints)
        while order > 1:
            stop = start + order
            self.drawPointsAsSegments(hull[start:stop], lineColor)
            start = stop
            order -= 1

        if lineColor: self.popStrokeAtributes()

    def drawArrowBetweenPoints(self, startPoint, endPoint, color=None, style="open60", position="end"):
        if color:
            self._strokeColor = color

        self.setStrokeDash("2, 1")
        startX, startY = startPoint
        endX, endY = endPoint
        self.drawArrow(GlyphPlotterEngine.CoordinateSystem.content, startX, startY, endX, endY, style, position)
        self.setStrokeDash(None)




def test():
    import PathUtilities

    testContour = [[(292, 499), (292, 693), (376.5, 810.5)], [(376.5, 810.5), (461, 928), (599, 928)], [(599, 928), (670, 928), (727.5, 895.5)], [(727.5, 895.5), (785, 863), (809, 813)], [(809, 813), (809, 197)], [(809, 197), (775, 139), (719.0, 107.0)], [(719.0, 107.0), (663, 75), (584, 75)], [(584, 75), (457, 75), (374.5, 190.5)], [(374.5, 190.5), (292, 306), (292, 499)]]
    testBounds = PathUtilities.GTBoundsRectangle.fromContour(testContour)

    cp = ContourPlotter(testBounds.points)

    cp.drawContours([testContour], PathUtilities.colorFromName("red"), False)

    image = cp.generateFinalImage()

    imageFile = open(f"Curve Test.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()

    pcp = ContourPlotter(testBounds.points, poly=True)
    pcp.drawContours([testContour], PathUtilities.colorFromName("green"), False)

    polyImage = pcp.generateFinalImage()


    polyImageFile = open(f"Poly Curve Test.svg", "wt", encoding="UTF-8")
    polyImageFile.write(polyImage)
    polyImageFile.close()

if __name__ == "__main__":
    test()
