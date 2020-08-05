"""\
Playground for glyph outlines

Created on June 18, 2020

@author Eric Mader
"""

from os.path import basename
from sys import argv, exit, stderr
from logging import getLogger, ERROR
from re import fullmatch
from fontTools.ttLib import ttFont, TTLibError
from fontTools.pens import svgPathPen
from FontDocTools.ArgumentIterator import ArgumentIterator
from FontDocTools.Font import Font, Glyph
import ContourPlotter
import PathUtilities
import GlyphContours

class GlyphTestArgumentIterator(ArgumentIterator):
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


class GlyphTestArgs:
    """\
    Interprets and checks the command line options for the GlyphTest tool,
    and condenses them into a specification for what the tool should do.
    """

    def __init__(self):
        self.fontFile = None
        self.fontName = None
        self.glyphName = None
        self.glyphID = None
        self.charCode = None
        self.color = None
        self.fill = False
        self.rotate = None
        self.mirror = None
        self.shear = None
        self.stretch = None
        self.project = None
        self.pinwheel = None
        self.ccw = True

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

    directions = {"clockwise": False, "cw": False, "counterclockwise": True, "ccw": True}
    @classmethod
    def getDirection(cls, direction):
        if direction is None:
            return True
        elif direction in cls.directions:
            return cls.directions[direction]
        else:
            raise ValueError(f"Unrecognized direction “{direction}”.")

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

        arguments = GlyphTestArgumentIterator(argumentList)
        args = GlyphTestArgs()
        argumentsSeen = {}

        for argument in arguments:
            if argument in argumentsSeen:
                raise ValueError("Duplicate option “" + argument + "”.")
            argumentsSeen[argument] = True

            if argument == "--font":
                (args.fontFile, args.fontName) = arguments.nextExtraAsFont("font")
            elif argument ==  "--color":
                colorName = arguments.nextExtra("color")
                args.color = PathUtilities.GTColor.fromName(colorName)
                if args.color is None: raise ValueError(f"{colorName} is not a valid color name")
            elif argument == "--fill":
                # opacity = arguments.nextExtraAsNumber("opacity")  # should make sure 0 < opacity <= 1
                args.fill = 1.0
            elif argument == "--transform":
                transform = arguments.nextExtra("transform type")

                if transform == "rotate":
                    args.rotate = arguments.nextExtraAsNumber("angle in degrees")
                    direction = arguments.nextOptional()
                    args.ccw = cls.getDirection(direction)
                elif transform == "project":
                    p = arguments.nextExtraAsNumber("p")
                    q = arguments.nextExtraAsNumber("q")
                    args.project = (p, q)
                elif transform == "mirror":
                    args.mirror = arguments.nextExtra("mirror axis")  # should check this x, y, xy
                elif transform == "shear":
                    x = arguments.nextExtraAsNumber("x shear")
                    y = arguments.nextExtraAsNumber("y shear")
                    args.shear = (x, y)
                elif transform == "stretch":
                    x = arguments.nextExtraAsNumber("x stretch")
                    y = arguments.nextExtraAsNumber("y stretch")
                    args.stretch = (x, y)
                elif transform == "pinwheel":
                    args.pinwheel = True
                    direction = arguments.nextOptional()
                    args.ccw = cls.getDirection(direction)
                    args.fill = 0.2
                else:
                    raise ValueError(f"Unrecognized transform “{transform}”.")

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
            else:
                raise ValueError(f"Unrecognized option “{argument}”.")

        args.completeInit()
        return args

class GTFont(Font):
    def __init__(self, fontFile, fontName=None, fontNumber=None):
        Font.__init__(self, fontFile, fontName, fontNumber)

    def __contains__(self, item):
        return item in self._ttFont

    def __getitem__(self, item):
        return self._ttFont[item]

    @classmethod
    def _getFontName(cls, ttFont, nameID):
        nameRecord = ttFont["name"].getName(nameID, 3, 1, 0x0409)  # name, Windows, Unicode BMP, English
        if nameRecord is None:
            nameRecord = ttFont["name"].getName(nameID, 1, 0)  # name, Mac, Roman
        if nameRecord is not None:
            return str(nameRecord)
        return None

    @classmethod
    def _getPostScriptName(cls, ttFont):
        return cls._getFontName(ttFont, 6)

    @classmethod
    def _getFullName(cls, ttFont):
        return cls._getFontName(ttFont, 4)

    @property
    def postscriptName(self):
        return self._getPostScriptName(self._ttFont)

    @property
    def fullName(self):
        return self._getFullName(self._ttFont)

    def glyphNameForCharacterCode(self, charCode):
        return self._ttFont.getBestCmap()[charCode]

    @property
    def glyphSet(self):
        return self._ttFont.getGlyphSet()

    @property
    def hmtxMetrics(self):
        if not self._hMetrics:
            self._hMetrics = self["hmtx"].metrics
        return self._hMetrics

    @property
    def vmtxMetrics(self):
        if not self._vMetrics and "vmtx" in self:
            self._vMetrics = self["vmtx"].metrics
        return self._vMetrics

    def __str__(self):
        return self.postscriptName

    def glyphForName(self, glyphName):
        """\
        Returns the glyph with the given name.
        """
        glyphs = self._glyphs
        if glyphName in glyphs:
            return glyphs[glyphName]
        if glyphName not in self._ttGlyphSet:
            raise ValueError(f"Unknown glyph name: “{glyphName}”.")
        # glyph = GTGlyph(self, glyphName)
        glyph = Glyph(glyphName, self)
        glyphs[glyphName] = glyph
        return glyph


    def glyphForIndex(self, index):
        """\
        Returns the glyph with the given glyph index.
        """
        return self.glyphForName(self.glyphName(index))


    def glyphForCharacter(self, char):
        """\
        Returns the nominal glyph for the given Unicode character.
        """

        charCode = ord(char) if type(char) == type("") else char
        return self.glyphForName(self.glyphNameForCharacterCode(charCode))

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
        args = GlyphTestArgs.forArguments(argumentList)
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    try:
        font = GTFont(args.fontFile, args.fontName)
        glyph = getGlyphFromArgs(args, font)

        fontBasename = basename(args.fontFile)
        fontPostscriptName = font.postscriptName
        print(f"Drawing glyph {glyph.name()} from font {fontBasename}/{fontPostscriptName}")

        glyphContours = GlyphContours.GTGlyphCoutours(glyph)
        contours = glyphContours.contours
        boundingRect = PathUtilities.GTBoundsRectangle.fromCoutours(contours)
        centerPoint = boundingRect.centerPoint

        nameSuffix = ""
        directionSuffix = "" if args.ccw else "_CW"
        colors = None
        shapes = [(contours, args.color)]
        if args.rotate:
            nameSuffix = f"_Rotated_{args.rotate}{directionSuffix}"
            transform = PathUtilities.GTTransform.rotationAbout(centerPoint, args.rotate, args.ccw)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.GTBoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.project:
            nameSuffix = "_Projected"
            p, q = args.project
            transform = PathUtilities.GTTransform.perspectiveFrom(centerPoint, p, q)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.GTBoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.mirror:
            nameSuffix = "_Mirrored"
            xAxis = args.mirror.startswith("x")
            yAxis = args.mirror.endswith("y")
            transform = PathUtilities.GTTransform.mirrorAround(centerPoint, xAxis, yAxis)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.GTBoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.shear:
            nameSuffix = "_Sheared"
            x, y = args.shear
            transform = PathUtilities.GTTransform.shear(x, y)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.GTBoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.stretch:
            nameSuffix = "_Stretched"
            x, y = args.stretch
            transform = PathUtilities.GTTransform.scale(x, y)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.GTBoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.pinwheel:
            nameSuffix = f"_PinWheel{directionSuffix}"
            colors = ["red", "orange", "gold", "lime", "green", "blue", "indigo", "violet", "purple"]
            colorIndex = 1
            shapes = [(contours, PathUtilities.GTColor.fromName(colors[0]))]  # the original shape with the first color
            for degrees in range(45, 360, 45):
                transform = PathUtilities.GTTransform.rotation(degrees, args.ccw)
                rc = transform.applyToContours(contours)
                bounds = PathUtilities.GTBoundsRectangle.fromCoutours(rc)
                shapes.append([rc, PathUtilities.GTColor.fromName(colors[colorIndex])])
                colorIndex += 1

                boundingRect = boundingRect.union(bounds)

        # print(glyph.referenceCommands())
        cp = ContourPlotter.ContourPlotter(boundingRect.points)

        for contours, color in shapes:
            cp.drawContours(contours, color, args.fill)

        image = cp.generateFinalImage()

        fullName = font.fullName
        if fullName.startswith("."): fullName = fullName[1:]

        imageFile = open(f"{fullName}_{glyph.name()}{nameSuffix}.svg", "wt", encoding="UTF-8")
        imageFile.write(image)
        imageFile.close()

        print(f"Number of contours = {len(contours)}")
        print(f"Number of segments = {[len(contour) for contour in contours]}")
        print()

        boundsRect = glyphContours.boundsRectangle
        upm = font.unitsPerEm()
        vsw = glyphContours.verticalStrokeWidth(boundsRect.yFromBottom(0.25))
        hsw = glyphContours.horizontalStrokeWidth(boundsRect.xFromLeft(0.50))

        print(f"vertical stroke width = {PathUtilities.toMicros(vsw, upm)} micro")
        print(f"horizontal stroke width = {PathUtilities.toMicros(hsw, upm)} micro")


    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

if __name__ == "__main__":
    main()
