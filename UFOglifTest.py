"""\
Reading glif objects from a UFO font.
Created on September 24, 2020

@author Eric Mader
"""

from os.path import basename
from sys import argv, exit, stderr
import logging
from FontDocTools.ArgumentIterator import ArgumentIterator
import Bezier
import PathUtilities
from ContourPlotter import ContourPlotter
from SegmentPen import SegmentPen
from UFOFont import UFOFont

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

def glifOutlineTest(font, glyphName, pen, color=None):
    logger = pen.logger
    logger.debug(f"{font.glyphSet.dirName}/{glyphName}.glif")
    glyph = font.glyphForName(glyphName)
    glyph.draw(pen)
    outline = Bezier.BOutline(pen.contours)
    bounds = outline.boundsRectangle

    cp = ContourPlotter(bounds.points)
    Bezier.drawOutline(cp, outline, color=color)

    cp.pushStrokeAttributes(opacity=0.5)
    cp.drawContours([bounds.contour], colorGreen)
    cp.popStrokeAtributes()

    fontName = font.glyphSet.dirName.split("/")[-2]

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

        font = UFOFont(args.fontName)
        pen = SegmentPen(font.glyphSet, logger)

        for glyphName in args.glyphList:
            glifOutlineTest(font, glyphName, pen, colorBlue)

    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

if __name__ == "__main__":
    test()
