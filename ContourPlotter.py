"""\
Plot a contour

Created June 23, 2020

@author = Eric Mader
"""

from FontDocTools import GlyphPlotterEngine

class ContourPlotter(GlyphPlotterEngine.GlyphPlotterEngine):
    lastCommand = ""

    def __init__(self, bounds):
        GlyphPlotterEngine.GlyphPlotterEngine.__init__(self)
        self._boundsAggregator.addBounds(bounds)
        self._contentMargins = GlyphPlotterEngine.Margins(10, 10, 10, 10)

    def pointToString(self, point):
        return " ".join([str(i) for i in point])

    def getCommand(self, command):
        if self.lastCommand != command:
            self.lastCommand = command
        else:
            command = " "

        return command

    def drawContours(self, contours, color=None, fill=False):
        if fill:
            self._fillColor = color
            self._fillOpacity = 0.20
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

                commands.append("Z")

        path += "".join(commands)

        if fill:
            path += f"' {self._fillAttributes()}/>"
        else:
            path += f"' fill='none' {self._strokeAttributes()}/>"
        self._content.append(path)
