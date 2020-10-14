"""\
Determine the contrast of a glyph by
measuring thickest and thinnest stroke width

Created on October 7, 2020

Much of this code translated from bezier.js, utils.js and others
from https://github.com/Pomax/BezierInfo-2

@author Eric Mader
"""

from os.path import basename
from sys import argv, exit, stderr
import logging
from re import fullmatch
from ufoLib import glifLib, plistlib
from FontDocTools.ArgumentIterator import ArgumentIterator
from GlyphTest import GTFont
from Bezier import Bezier, BOutline, drawOutline
import GlyphContours
import PathUtilities
import ContourPlotter

class ContrastTestArgumentIterator(ArgumentIterator):
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

    def nextExtraAsFont(self, valueName):
        """\
        Returns a tuple (fontFile, fontName).
        The font file is taken from the first extra argument.
        If the font file name ends in “.ttc”, the font name is taken from
        the second extra argument; otherwise it is None.
        Raises ValueError if there’s no more argument, or if the next
        argument starts with “--”, or if it’s not a valid file name,
        or if there’s no font name along with a font file name ending in “.ttc”.
        """
        fontFile = self.nextExtra(valueName + " file")
        fontName = None
        if fontFile.endswith(".ttc"):
            fontName = self.nextExtra(valueName + " name")
        elif not fontFile.endswith(".ttf") and not fontFile.endswith(".otf") and not fontFile.endswith(".ufo"):
            raise ValueError(f"Expected file name with “.ttf” or “.otf” or “.ufo”; got “{fontFile}”.")
        return (fontFile, fontName)

    def getGlyphList(self):
        glist = []
        nextArg = self.nextOptional()
        while nextArg:
            glist.append(nextArg)
            nextArg = self.nextOptional()

        return glist

class ContrastTestArgs:
    def __init__(self):
        self.debug = False
        self.fontFile = None
        self.fontName = None
        self.glyphName = None
        self.glyphID = None
        self.charCode = None
        self.steps = 20

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
        if sum([self.glyphName is not None, self.glyphID is not None, self.charCode is not None]) != 1:
            raise ValueError("Missing “--glyph”")

    @classmethod
    def getHexCharCode(cls, arg):
        if not fullmatch(r"[0-9a-fA-F]{4,6}", arg) or int(arg, 16) == 0:
            raise ValueError(f"Char code must be a non-zero hex number; got {arg}")
        return int(arg, 16)

    @classmethod
    def getGlyphID(cls, arg):
        if not fullmatch(r"[0-9]{1,5}", arg) or int(arg) == 0:
            raise ValueError(f"GlyphID must be a positive integer; got {arg}")
        return int(arg)

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

        arguments = ContrastTestArgumentIterator(argumentList)
        args = ContrastTestArgs()
        argumentsSeen = {}

        for argument in arguments:
            if argument in argumentsSeen:
                raise ValueError("Duplicate option “" + argument + "”.")
            argumentsSeen[argument] = True

            if argument == "--font":
                args.fontFile, args.fontName = arguments.nextExtraAsFont("font")
            elif argument == "--glyph":
                extra = arguments.nextExtra("glyph")
                if len(extra) == 1:
                    args.charCode = ord(extra)
                elif extra[0] == "/":
                    args.glyphName = extra[1:]
                elif extra[0] == "u":
                    args.charCode = cls.getHexCharCode(extra[1:])
                elif extra[0:3] == "gid":
                    args.glyphID = cls.getGlyphID(extra[3:])
            elif argument == "--steps":
                args.steps = arguments.nextExtraAsPosInt("steps")
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

        # glyph = glifLib.Glyph(glyphName, self._glyphSet)
        glyph = self.glyphSet[glyphName]
        cpen = SegmentPen(self._glyphSet, self.logger)
        glyph.draw(cpen)
        contours = t.applyToContours(cpen.contours) if t else cpen.contours
        self.contours.extend(contours)

    @property
    def contours(self):
        return self._contours

class UFOFont(object):
    def __init__(self, fileName):
        infoFile = open(f"{fileName}/fontinfo.plist", "r", encoding="UTF-8")
        self._fileInfo = plistlib.load(infoFile)
        self._glyphSet = glifLib.GlyphSet(f"{fileName}/glyphs")
        self._unicodes = self._glyphSet.getUnicodes()

    @property
    def fullName(self):
        return self._fileInfo["postscriptFontName"]  # Should also check for full name...

    @property
    def glyphSet(self):
        return self._glyphSet

    def glyphForName(self, glyphName):
        return UFOGlyph(glyphName, self._glyphSet)

    def glyphForIndex(self, index):
        return None

    def glyphForCharacter(self, charCode):
        for name, codes in self._unicodes.items():
            if charCode in codes: return self.glyphForName(name)
        return None

    def getGlyphContours(self, glyphName, logger):
        glyph = glifLib.Glyph(glyphName, self._glyphSet)
        pen = SegmentPen(self._glyphSet, logger)
        glyph.draw(pen)
        return pen.contours

class UFOGlyph(object):
    def __init__(self, glyphName, glyphSet):
        self._glyph = glifLib.Glyph(glyphName, glyphSet)

    def name(self):
        return self._glyph.glyphName

    def draw(self, pen):
        self._glyph.draw(pen)

def getGlyphFromArgs(args, font):
    if args.glyphName: return font.glyphForName(args.glyphName)
    if args.glyphID: return font.glyphForIndex(args.glyphID)
    if args.charCode: return font.glyphForCharacter(args.charCode)

def getGlyphContours(args, font):
    level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=level)
    logger = logging.getLogger("glyph-contrast-test")

    glyph = getGlyphFromArgs(args, font)
    pen = SegmentPen(font.glyphSet, logger)
    font.glyphSet[glyph.name()].draw(pen)
    return (pen.contours, glyph.name())


def main():
    argumentList = argv
    args = None
    programName = basename(argumentList.pop(0))
    if len(argumentList) == 0:
        print(__doc__, file=stderr)
        exit(1)
    try:
        args = ContrastTestArgs.forArguments(argumentList)
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    steps = args.steps

    if args.fontFile.endswith(".ufo"):
        font = UFOFont(args.fontFile)
    else:
        font = GTFont(args.fontFile, fontName=args.fontName)
    fullName = font.fullName
    if fullName.startswith("."): fullName = fullName[1:]
    contours, glyphName = getGlyphContours(args, font)
    outline = BOutline(contours)
    bounds = outline.boundsRectangle
    closePoints = []

    outerContour, innerContour = outline.bContours[:2]  # slice in case there's more than two contours...
    outerLUT = outerContour.getLUT(steps)

    for op in outerLUT:
        closest, ip = innerContour.findClosestPoint(op, steps)
        closePoints.append((closest, op, ip))

    closePoints.sort(key=lambda cp: cp[0])

    print(f"Glyph {glyphName}: Max distance = {closePoints[-1][0]}, min distance = {closePoints[0][0]}")
    cp = ContourPlotter.ContourPlotter(bounds.points)
    cp.setLabelFontSize(20, 20)
    margin = cp._contentMargins.left

    cp.drawText(bounds.width / 2 + margin, 5, "center", f"min = {round(closePoints[0][0], 2)}, max = {round(closePoints[-1][0], 2)}")

    cp.drawContours([bounds.contour], PathUtilities.GTColor.fromName("grey"))
    drawOutline(cp, outline)
    cp.pushStrokeAttributes(width=4)

    _, cop, cip = closePoints[0]
    cp.drawPointsAsSegments([cop, cip], PathUtilities.GTColor.fromName("blue"))

    _, cop, cip = closePoints[-1]
    cp.drawPointsAsSegments([cop, cip], PathUtilities.GTColor.fromName("blue"))

    image = cp.generateFinalImage()

    imageFile = open(f"Glyph Contrast Test {fullName}_{glyphName}.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()





if __name__ == "__main__":
    main()
