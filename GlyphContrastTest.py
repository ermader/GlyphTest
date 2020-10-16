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
from FontDocTools.ArgumentIterator import ArgumentIterator
from GlyphTest import GTFont
from Bezier import Bezier, BOutline, drawOutline
from SegmentPen import SegmentPen
from UFOFont import UFOFont
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

def getGlyphFromArgs(args, font):
    if args.glyphName: return font.glyphForName(args.glyphName)
    if args.glyphID: return font.glyphForIndex(args.glyphID)
    if args.charCode: return font.glyphForCharacter(args.charCode)

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

    level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=level)
    logger = logging.getLogger("glyph-contrast-test")

    glyph = getGlyphFromArgs(args, font)
    glyphName = glyph.name()
    pen = SegmentPen(font.glyphSet, logger)
    font.glyphSet[glyph.name()].draw(pen)
    contours = pen.contours
    outline = BOutline(contours)
    bounds = outline.boundsRectangle
    closePoints = []

    outerContour, innerContour = outline.bContours[:2]  # slice in case there's more than two contours...
    outerLUT = outerContour.getLUT(steps)

    for op in outerLUT:
        closest, ip = innerContour.findClosestPoint(op, steps)
        closePoints.append((closest, op, ip))

    closePoints.sort(key=lambda cp: cp[0])

    min = closePoints[0][0]
    max = closePoints[-1][0]
    ratio = max / min

    print(f"Glyph {glyphName}: Max distance = {max}, min distance = {min}, ratio = {ratio}")
    cp = ContourPlotter.ContourPlotter(bounds.points)
    margin = cp._contentMargins.left

    cp.drawText(bounds.width / 2 + margin, cp._labelFontSize / 4, "center", f"min = {round(min, 2)}, max = {round(max, 2)}, wsf = {round(ratio, 3)}")

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
