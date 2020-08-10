"""\
Tests of drawing a curve

Created on August 10, 2020

@author Eric Mader
"""

import PathUtilities
from ContourPlotter import ContourPlotter

class Curve(object):
    def __init__(self, points, interval):
        self._curvePoints = []

        for t in range(interval + 1):
            self._computePoints(points, t / interval)

    def _computePoints(self, points, t):
        if len(points) == 1:
            self._curvePoints.append(points[0])
        else:
            newpoints = []
            for i in range(len(points) - 1):
                x = int((1 - t) * points[i][0] + t * points[i + 1][0])
                y = int((1 - t) * points[i][1] + t * points[i + 1][1])
                newpoints.append((x, y))
            self._computePoints(newpoints, t)

    @property
    def points(self):
        return self._curvePoints

def test():
    curvePoints = [(90, 140), (25, 210), (230, 210), (150, 10)]
    # curvePoints = [(70, 0), (20, 140), (250, 190)]
    # curvePoints = [(0, 50), (100, 200)]

    curve1 = Curve(curvePoints, 35)
    bounds1 = PathUtilities.GTBoundsRectangle(*curve1.points)
    cp1 = ContourPlotter(bounds1.points)

    cp1.drawPointsAsSegments(curve1.points, PathUtilities.GTColor.fromName("blue"))
    image1 = cp1.generateFinalImage()

    curve2 = Curve(curvePoints, 350)
    bounds2 = PathUtilities.GTBoundsRectangle(*curve2.points)
    cp2 = ContourPlotter(bounds2.points)

    cp2.drawPointsAsCircles(curve2.points, PathUtilities.GTColor.fromName("blue"))
    image2 = cp2.generateFinalImage()

    imageFile1 = open(f"Curve as Segments Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    imageFile2 = open(f"Curve as Points Test.svg", "wt", encoding="UTF-8")
    imageFile2.write(image2)
    imageFile2.close()

if __name__ == "__main__":
    test()


