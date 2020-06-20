"""\
Playground for glyph outlines

Created on June 18, 2020

@author Eric Mader
"""

from fontTools.ttLib import ttFont

class Glyph(object):
    def handleSegment(self, segment):
        if len(segment) <= 3:
            segments.append(segment)
        else:
            # a starting on-curve point, two or more off-curve points, and a final on-curve point
            startPoint = segment[0]
            for i in range(1, len(segment) - 2):
                p1x, p1y = segment[i]
                p2x, p2y = segment[i + 1]
                impliedPoint = (0.5 * (p1x + p2x), 0.5 * (p1y + p2y))
                self.segments.append((startPoint, segment[i], impliedPoint))
                startPoint = impliedPoint
            self.segments.append((startPoint, segment[-2], segment[-1]))

    def __init__(self, font, glyphName):
        self.font = font
        self.unitsPerEm = font['head'].unitsPerEm
        self.glyfTable = font["glyf"]
        self.glyph = self.glyfTable["kadeva"]
        self.glyphID = self.glyfTable.getGlyphID("kadeva")

        self.contours = []

        halfEm = self.unitsPerEm // 2
        coords, endPoints, flags = self.glyph.getCoordinates(self.glyfTable)
        coords = coords.copy()
        coords.translate((halfEm, halfEm))

        startPoint = 0
        for endPoint in endPoints:
            self.segments = []
            limitPoint = endPoint + 1
            contour = coords[startPoint:limitPoint]
            contourFlags = [flag & 0x1 for flag in flags[startPoint:limitPoint]]

            contour.append(contour[0])
            contourFlags.append(contourFlags[0])
            start = limitPoint

            while len(contour) > 1:
                firstOnCurve = contourFlags.index(1)
                nextOnCurve = contourFlags.index(1, firstOnCurve + 1)
                handleSegment(contour[firstOnCurve:nextOnCurve + 1])
                contour = contour[nextOnCurve:]
                contourFlags = contourFlags[nextOnCurve:]

            self.contours.append(segments)




segments = []
def handleSegment(segment):
    if len(segment) <= 3:
        segments.append(segment)
    else:
        # a starting on-curve point, two or more off-curve points, and a final on-curve point
        startPoint = segment[0]
        for i in range(1, len(segment) - 2):
            p1x, p1y = segment[i]
            p2x, p2y = segment[i+1]
            impliedPoint = (0.5 * (p1x + p2x), 0.5 * (p1y + p2y))
            segments.append((startPoint, segment[i], impliedPoint))
            startPoint = impliedPoint
        segments.append((startPoint, segment[-2], segment[-1]))

def main():
    font = ttFont.TTFont("/Users/emader/PycharmProjects/IndicShaper/Fonts/Noto-2019/NotoSansDevanagari-Regular.ttf")
    kaGlyph = Glyph(font, "kadeva")

    print(f"Number of contours = {len(kaGlyph.contours)}")
    print(f"Number of segments = {len(kaGlyph.contours[0])}")
    # unitsPerEm = font["head"].unitsPerEm
    # halfEm = unitsPerEm // 2
    # glyfTable = font["glyf"]
    # kaGlyph = glyfTable["kadeva"]
    # kaGlyphID = glyfTable.getGlyphID("kadeva")
    # print(f"UnitsPerEm = {unitsPerEm}")
    # print(f"Glyph ID of 'kadeva' = {kaGlyphID}")
    #
    # coords, endPoints, flags = kaGlyph.getCoordinates(glyfTable)
    # coords = coords.copy()
    # coords.translate((halfEm, halfEm))
    #
    # print(f"Number of coordinates = {len(coords)}")
    # print(f"Number of contours = {len(endPoints)}")
    #
    # startPoint = 0
    # for endPoint in endPoints:
    #     limitPoint = endPoint + 1
    #     contour = coords[startPoint:limitPoint]
    #     contourFlags = [flag & 0x1 for flag in flags[startPoint:limitPoint]]
    #
    #     contour.append(contour[0])
    #     contourFlags.append(contourFlags[0])
    #     start = limitPoint
    #
    #     while len(contour) > 1:
    #         firstOnCurve = contourFlags.index(1)
    #         nextOnCurve = contourFlags.index(1, firstOnCurve + 1)
    #         handleSegment(contour[firstOnCurve:nextOnCurve + 1])
    #         contour = contour[nextOnCurve:]
    #         contourFlags = contourFlags[nextOnCurve:]
    #
    #     print(f"Number of segments = {len(segments)}")

if __name__ == "__main__":
    main()
