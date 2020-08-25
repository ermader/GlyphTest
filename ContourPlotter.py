"""\
Plot a contour

Created June 23, 2020

@author = Eric Mader
"""

from FontDocTools import GlyphPlotterEngine

class ContourPlotter(GlyphPlotterEngine.GlyphPlotterEngine):
    lastCommand = ""

    def __init__(self, bounds, poly=False):
        GlyphPlotterEngine.GlyphPlotterEngine.__init__(self)
        self._boundsAggregator.addBounds(bounds)
        self._contentMargins = GlyphPlotterEngine.Margins(15, 15, 15, 15)
        self._poly = poly
        self._lastCommand = ""

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
            self._fillColor = color
            self._fillOpacity = fill
        elif color:
            self._strokeColor = color
            self._strokeWidth = 2

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
        else:
            path += f"' fill='none' {self._strokeAttributes()}/>"
        self._content.append(path)

    def drawPointsAsSegments(self, points, color=None):
        if color:
            self._strokeColor = color
            # self._strokeWidth = 2

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

    def drawPointsAsCircles(self, points, color=None):
        if color:
            self._fillColor = color

        for point in points:
            x, y = point
            self.drawCircle(GlyphPlotterEngine.CoordinateSystem.content, x, y, 0.5, GlyphPlotterEngine.PaintMode.fill)

    def drawCurve(self, segment, color=None):
        self.drawContours([[segment]], color=color, fill=False, close=False)

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
