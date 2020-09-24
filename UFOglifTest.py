"""\
Reading glif objects from a UFO font.
Created on September 24, 2020

@author Eric Mader
"""

from os.path import basename
from sys import argv, exit, stderr
import logging
import ufoLib
from FontDocTools.ArgumentIterator import ArgumentIterator
import Bezier
import PathUtilities
from ContourPlotter import ContourPlotter

class GlifTestArgumentIterator(ArgumentIterator):
    def __init__(self, arguments):
        ArgumentIterator.__init__(self, arguments)

    def nextOptional(self):
        """\
        Returns an optional next extra argument.
        Returns None if there’s no more argument, or if the next
        argument starts with “--”.
        """
        try:
            nextArgument = self._next()
        except StopIteration:
            return None

        if nextArgument.startswith("--"):
            self._nextPos -= 1
            return None

        return nextArgument

    def getGlyphList(self):
        glist = []
        nextArg = self.nextOptional()
        while nextArg:
            glist.append(nextArg)
            nextArg = self.nextOptional()

        return glist

class GlifTestArgs:
    def __init__(self):
        self.debug = False
        self.fontName = None
        self.glyphList = []

    def completeInit(self):
        """\
        Complete initialization of a shaping spec after some values have
        been set from the argument list.
        Check that required data has been provided and fill in defaults for others.
        Raise ValueError if required options are missing, or invalid option
        combinations are detected.
        """

        if not self.fontName:
            raise ValueError("Missing “--font” option.")
        if len(self.glyphList) == 0:
            raise ValueError("Missing “--glyph”")

    @classmethod
    def forArguments(cls, argumentList):
        """\
        Return a new GlifTestArgs object representing the given
        argument list.
        Raise ValueError if the argument list is missing required options,
        is missing required extra arguments for options,
        has unsupported options, or has unsupported extra arguments.
        """

        # pylint: disable=too-many-branches

        arguments = GlifTestArgumentIterator(argumentList)
        args = GlifTestArgs()
        argumentsSeen = {}

        for argument in arguments:
            if argument in argumentsSeen:
                raise ValueError("Duplicate option “" + argument + "”.")
            argumentsSeen[argument] = True

            if argument == "--font":
                args.fontName = arguments.nextExtra("font")
            elif argument == "--glyph":
                args.glyphList = arguments.getGlyphList()
            elif argument == "--debug":
                args.debug = True
            else:
                raise ValueError(f"Unrecognized option “{argument}”.")

        args.completeInit()
        return args


class SegmentPen:
    def __init__(self, glyphSet, logger):
        self._contours = []
        self._glyphSet = glyphSet
        self.logger = logger

    def addPoint(self, pt, segmentType, smooth, name):
        raise NotImplementedError

    def moveTo(self, pt):
        self._lastOnCurve = pt

        # This is for glyphs, which are always closed paths,
        # so we assume that the move is the start of a new contour
        self._contour = []
        self._segment = []
        self.logger.debug(f"moveTo({pt})")

    def lineTo(self, pt):
        segment = [self._lastOnCurve, pt]
        self._contour.append(segment)
        self._lastOnCurve = pt
        self.logger.debug(f"lineTo({pt})")

    def curveTo(self, *points):
        segment = [self._lastOnCurve]
        segment.extend(points)
        self._contour.append(segment)
        self._lastOnCurve = points[-1]
        self.logger.debug(f"curveTo({points})")

    def qCurveTo(self, *points):
        segment = [self._lastOnCurve]
        segment.extend(points)

        if len(segment) <= 3:
            self._contour.append(segment)
        else:
            # a starting on-curve point, two or more off-curve points, and a final on-curve point
            startPoint = segment[0]
            for i in range(1, len(segment) - 2):
                p1x, p1y = segment[i]
                p2x, p2y = segment[i + 1]
                impliedPoint = (0.5 * (p1x + p2x), 0.5 * (p1y + p2y))
                self._contour.append([startPoint, segment[i], impliedPoint])
                startPoint = impliedPoint
            self._contour.append([startPoint, segment[-2], segment[-1]])
        self._lastOnCurve = segment[-1]
        self.logger.debug(f"qCurveTo({points})")

    def beginPath(self):
        raise NotImplementedError

    def closePath(self):
        self._contours.append(self._contour)
        if self._contour[0][0] != self._contour[-1][-1]:
            self._contour.append([self._contour[-1][-1], self._contour[0][0]])
        self._contour = []
        self.logger.debug("closePath()")

    def endPath(self):
        raise NotImplementedError

    identityTransformation = (1, 0, 0, 1, 0, 0)

    def addComponent(self, glyphName, transformation):
        self.logger.debug(f"addComponent(\"{glyphName}\", {transformation}")
        if transformation != self.identityTransformation:
            xScale, xyScale, yxScale, yScale, xOffset, yOffset = transformation
            m = PathUtilities.GTTransform._matrix(
                a=xScale,
                b=xyScale,
                c=yxScale,
                d=yScale,
                m=xOffset,
                n=yOffset
            )
            t = PathUtilities.GTTransform(m)
        else:
            t = None

        glifString = self._glyphSet.getGLIF(glyphName)
        glyph = ufoLib.glifLib.Glyph(self._glyphSet, "")
        cpen = SegmentPen(self._glyphSet, self.logger)
        psp = ufoLib.glifLib.PointToSegmentPen(cpen)
        ufoLib.glifLib.readGlyphFromString(glifString, glyph, psp)
        contours = t.applyToContours(cpen.contours) if t else cpen.contours
        self.contours.extend(contours)

    @property
    def contours(self):
        return self._contours

colorRed = PathUtilities.GTColor.fromName("red")
colorGreen = PathUtilities.GTColor.fromName("green")
colorBlue = PathUtilities.GTColor.fromName("blue")
colorGold = PathUtilities.GTColor.fromName("gold")
colorMagenta = PathUtilities.GTColor.fromName("magenta")
colorCyan = PathUtilities.GTColor.fromName("cyan")
colorYellow = PathUtilities.GTColor.fromName("yellow")
colorBlack = PathUtilities.GTColor.fromName("black")
colorLightGrey = PathUtilities.GTColor.fromName("lightgrey")
colorLightBlue = PathUtilities.GTColor.fromName("lightblue")
colorLightGreen = PathUtilities.GTColor.fromName("lightgreen")

def getGLIFOutline(glyphSet, glyphName, logger):
    glyph = ufoLib.glifLib.Glyph(glyphSet, "")
    glifString = glyphSet.getGLIF(glyphName)
    pen = SegmentPen(glyphSet, logger)
    psp = ufoLib.glifLib.PointToSegmentPen(pen)
    ufoLib.glifLib.readGlyphFromString(glifString, glyph, psp)
    return Bezier.BOutline(pen.contours)


def glifOutlineTest(glyphSet, glyphName, logger, color=None):
    logger.debug(f"{glyphSet.dirName}/{glyphName}.glif")
    outline = getGLIFOutline(glyphSet, glyphName, logger)
    bounds = outline.boundsRectangle

    cp = ContourPlotter(bounds.points)
    Bezier.drawOutline(cp, outline, color=color)

    cp.pushStrokeAttributes(opacity=0.5)
    cp.drawContours([bounds.contour], colorGreen)
    cp.popStrokeAtributes()

    fontName = glyphSet.dirName.split("/")[-2]

    image = cp.generateFinalImage()
    imageFile = open(f"{fontName}_{glyphName}.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()
    logger.debug("")

def test():
    argumentList = argv
    args = None
    programName = basename(argumentList.pop(0))
    if len(argumentList) == 0:
        print(__doc__, file=stderr)
        exit(1)
    try:
        args = GlifTestArgs.forArguments(argumentList)
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    try:
        level = logging.DEBUG if args.debug else logging.WARNING
        logging.basicConfig(level=level)
        logger = logging.getLogger("glif-test")
        gs = ufoLib.glifLib.GlyphSet(f"{args.fontName}/glyphs")
        for glyphName in args.glyphList:
            glifOutlineTest(gs, glyphName, logger, colorBlue)

    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

if __name__ == "__main__":
    test()
