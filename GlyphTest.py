"""\
Playground for glyph outlines

Created on June 18, 2020

@author Eric Mader
"""

from os.path import basename
from sys import argv, exit, stderr
from fontTools.ttLib import ttFont
from FontDocTools.ArgumentIterator import ArgumentIterator
import ContourPlotter

class GlyphTestArgs:
    """\
    Interprets and checks the command line options for the GlyphTest tool,
    and condenses them into a specification for what the tool should do.
    """

    def __init__(self):
        self.fontFile = None
        self.fontName = None
        self.glyphName = None

    def completeInit(self):
        """\
        Complete initialization of a shaping spec after some values have
        been set from the argument list.
        Check that required data has been provided and fill in defaults for others.
        Raise ValueError if required options are missing, or invalid option
        combinations are detected.
        """

        if not self.fontFile:
            raise ValueError("Missing “--font” option.")
        if not self.glyphName:
            raise ValueError("Missing “--glyphName” option.")



    @classmethod
    def forArguments(cls, argumentList):
        """\
        Return a new GlyphShaperSpec object representing the given
        argument list.
        Raise ValueError if the argument list is missing required options,
        is missing required extra arguments for options,
        has unsupported options, or has unsupported extra arguments.
        """

        # pylint: disable=too-many-branches

        arguments = ArgumentIterator(argumentList)
        args = GlyphTestArgs()
        argumentsSeen = {}

        for argument in arguments:
            if argument in argumentsSeen:
                raise ValueError("Duplicate option “" + argument + "”.")
            argumentsSeen[argument] = True

            if argument == "--font":
                (args.fontFile, args.fontName) = arguments.nextExtraAsFont("font")
            elif argument == "--glyphName":
                extra = arguments.nextExtra("glyph name")
                args.glyphName = extra
            else:
                raise ValueError(f"Unrecognized option “{argument}”.")

        args.completeInit()
        return args

class Glyph(object):
    def handleSegment(self, segment):
        if len(segment) <= 3:
            self.segments.append(segment)
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
        headTable = font['head']
        hheaTable = font['hhea']
        self.ascent = hheaTable.ascent
        self.descent = hheaTable.descent
        self.maxAdvanceWidth = hheaTable.advanceWidthMax
        self.unitsPerEm = headTable.unitsPerEm
        xMin = headTable.xMin
        yMin = headTable.yMin
        xMax = headTable.xMax
        yMax = headTable.yMax
        self.bounds = (xMin, yMin, xMax, yMax)
        self.glyfTable = font["glyf"]
        self.glyph = self.glyfTable[glyphName]
        self.glyphID = self.glyfTable.getGlyphID(glyphName)

        self.contours = []

        halfEm = self.unitsPerEm // 2
        coords, endPoints, flags = self.glyph.getCoordinates(self.glyfTable)
        coords = coords.copy()
        # coords.translate((halfEm, halfEm))

        startPoint = 0
        for endPoint in endPoints:
            self.segments = []
            limitPoint = endPoint + 1
            contour = coords[startPoint:limitPoint]
            contourFlags = [flag & 0x1 for flag in flags[startPoint:limitPoint]]

            contour.append(contour[0])
            contourFlags.append(contourFlags[0])
            startPoint = limitPoint

            while len(contour) > 1:
                firstOnCurve = contourFlags.index(1)
                nextOnCurve = contourFlags.index(1, firstOnCurve + 1)
                self.handleSegment(contour[firstOnCurve:nextOnCurve + 1])
                contour = contour[nextOnCurve:]
                contourFlags = contourFlags[nextOnCurve:]

            self.contours.append(self.segments)

def main():
    argumentList = argv
    programName = basename(argumentList.pop(0))
    if len(argumentList) == 0:
        print(__doc__, file=stderr)
        exit(1)
    try:
        args = GlyphTestArgs.forArguments(argumentList)
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    try:
        font = ttFont.TTFont(args.fontFile)
        glyph = Glyph(font, args.glyphName)

        cp = ContourPlotter.ContourPlotter(glyph.bounds)

        for contour in glyph.contours:
            cp.drawContour(contour)

        image = cp.generateFinalImage()
        imageFile = open(args.glyphName + ".svg", "wt", encoding="UTF-8")
        imageFile.write(image)
        imageFile.close()

        print(f"Number of contours = {len(glyph.contours)}")
        print(f"Number of segments = {[len(contour) for contour in glyph.contours]}")

    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    # font = ttFont.TTFont("/Users/emader/PycharmProjects/IndicShaper/Fonts/Noto-2019/NotoSansDevanagari-Regular.ttf")
    # kaGlyph = Glyph(font, "kassadeva")
    #
    # cp = ContourPlotter.ContourPlotter(kaGlyph.bounds)
    #
    # for contour in kaGlyph.contours:
    #     cp.drawContour(contour)
    #
    # image = cp.generateFinalImage()
    # file = open("kassaglyph.svg", "wt", encoding="UTF-8")
    # file.write(image)
    # file.close()
    #
    # print(f"Number of contours = {len(kaGlyph.contours)}")
    # print(f"Number of segments = {[len(contour) for contour in kaGlyph.contours]}")

if __name__ == "__main__":
    main()
