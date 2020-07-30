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
from FontDocTools.Font import Font
from FontDocTools.Color import Color
import ContourPlotter
import PathUtilities

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
    def postScriptName(self):
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
        return self.postScriptName

    def glyphForName(self, glyphName):
        """\
        Returns the glyph with the given name.
        """
        glyphs = self._glyphs
        if glyphName in glyphs:
            return glyphs[glyphName]
        if glyphName not in self._ttGlyphSet:
            raise ValueError(f"Unknown glyph name: “{glyphName}”.")
        glyph = Glyph(self, glyphName)
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

class Glyph(object):
    def handleSegment(self, segment):
        for x, y in segment:
            self.minX = min(self.minX, x)
            self.minY = min(self.minY, y)
            self.maxX = max(self.maxX, x)
            self.maxY = max(self.maxY, y)

        if len(segment) <= 3:
            self.segments.append(segment)
        else:
            # a starting on-curve point, two or more off-curve points, and a final on-curve point
            startPoint = segment[0]
            for i in range(1, len(segment) - 2):
                p1x, p1y = segment[i]
                p2x, p2y = segment[i + 1]
                impliedPoint = (0.5 * (p1x + p2x), 0.5 * (p1y + p2y))
                self.segments.append([startPoint, segment[i], impliedPoint])
                startPoint = impliedPoint
            self.segments.append([startPoint, segment[-2], segment[-1]])

    def __init__(self, font, glyphName):
        self.font = font
        headTable = font['head']
        hheaTable = font['hhea']
        self.ascent = hheaTable.ascent
        self.descent = hheaTable.descent
        self.maxAdvanceWidth = hheaTable.advanceWidthMax
        self.unitsPerEm = headTable.unitsPerEm
        self.glyfTable = font["glyf"]
        self.glyph = self.glyfTable[glyphName]
        self.glyphID = self.glyfTable.getGlyphID(glyphName)
        self.glyphName = glyphName

        self.minX = self.minY = 65536
        self.maxX = self.maxY = -65536
        self.contours = []

        coords, endPoints, flags = self.glyph.getCoordinates(self.glyfTable)
        coords = coords.copy()

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

        self.bounds = PathUtilities.BoundsRectangle((self.minX, self.maxY), (self.maxX, self.minY))

    def __str__(self):
        return f'"{self.glyphName}" of "{self.font.postScriptName}"'

    @property
    def advanceWidth(self):
        """\
        Returns the advance width of this glyph as given
        in the hmtx table.
        """
        (advanceWidth, _) = self.font.hmtxMetrics[self.glyphName]
        return advanceWidth

    @property
    def advanceHeight(self):
        """\
        Returns the advance height of this glyph as given
        in the vmtx table.
        """

        vmtxMetrics = self.font.vmtxMetrics
        if vmtxMetrics:
            (advanceHeight, _) = self.font.vmtxMetrics[self.glyphName]
            return advanceHeight
        return None

    def referenceCommands(self):
        glyphSet = self.font.glyphSet
        pen = svgPathPen.SVGPathPen(glyphSet)
        glyphSet[self.glyphName].draw(pen)
        return pen.getCommands()

def getGlyphFromArgs(args, font):
    if args.glyphName: return font.glyphForName(args.glyphName)
    if args.glyphID: return font.glyphForIndex(args.glyphID)
    if args.charCode: return font.glyphForCharacter(args.charCode)

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
        font = GTFont(args.fontFile, args.fontName)
        glyph = getGlyphFromArgs(args, font)

        fontBasename = basename(args.fontFile)
        fontPostscriptName = font.postScriptName
        print(f"Drawing glyph {glyph.glyphName} from font {fontBasename}/{fontPostscriptName}")

        contours = glyph.contours
        boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
        centerPoint = boundingRect.centerPoint

        nameSuffix = ""
        directionSuffix = "" if args.ccw else "_CW"
        colors = None
        shapes = [(contours, args.color)]
        if args.rotate:
            nameSuffix = f"_Rotated_{args.rotate}{directionSuffix}"
            contours = PathUtilities.rotateContoursAbout(contours, centerPoint, args.rotate, args.ccw)
            boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.project:
            nameSuffix = "_Projected"
            p, q = args.project
            m1 = PathUtilities.Transform._translateMatrix(centerPoint, (0, 0))
            m2 = PathUtilities.Transform._perspectiveMatrix(p, q, 1)
            m3 = PathUtilities.Transform._translateMatrix((0, 0), centerPoint)
            transform = PathUtilities.Transform(m1, m2, m3)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.mirror:
            nameSuffix = "_Mirrored"
            cx, cy = centerPoint
            if args.mirror.startswith("x"):
                m1 = PathUtilities.Transform._matrix(m=-cx)
                m2 = PathUtilities.Transform._matrix(a=-1)
                m3 = PathUtilities.Transform._matrix(m=cx)
                transform = PathUtilities.Transform(m1, m2, m3)
                contours = transform.applyToContours(contours)

            if args.mirror.endswith("y"):
                m1 = PathUtilities.Transform._matrix(n=-cy)
                m2 = PathUtilities.Transform._matrix(d=-1)
                m3 = PathUtilities.Transform._matrix(n=cy)
                transform = PathUtilities.Transform(m1, m2, m3)
                contours = transform.applyToContours(contours)

            boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.shear:
            nameSuffix = "_Sheared"
            x, y = args.shear
            m1 = PathUtilities.Transform._matrix(b=y, c=x)
            transform = PathUtilities.Transform(m1)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.stretch:
            nameSuffix = "_Stretched"
            x, y = args.stretch
            m1 = PathUtilities.Transform._matrix(a=x, d=y)
            transform = PathUtilities.Transform(m1)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.pinwheel:
            nameSuffix = f"_PinWheel{directionSuffix}"
            colors = ["red", "orange", "gold", "lime", "green", "blue", "indigo", "violet", "purple"]
            colorIndex = 1
            shapes = [(contours, PathUtilities.colorFromName(colors[0]))]  # the original shape with the first color
            for degrees in range(45, 360, 45):
                m1 = PathUtilities.Transform._rotationMatrix(degrees, args.ccw)
                transform = PathUtilities.Transform(m1)
                rc = transform.applyToContours(contours)
                bounds = PathUtilities.BoundsRectangle.fromCoutours(rc)
                shapes.append([rc, PathUtilities.colorFromName(colors[colorIndex])])
                colorIndex += 1

                boundingRect = boundingRect.union(bounds)

        # print(glyph.referenceCommands())
        cp = ContourPlotter.ContourPlotter(boundingRect.points)

        for contours, color in shapes:
            cp.drawContours(contours, color, args.fill)

        image = cp.generateFinalImage()

        fullName = font.fullName
        if fullName.startswith("."): fullName = fullName[1:]

        imageFile = open(f"{fullName}_{glyph.glyphName}{nameSuffix}.svg", "wt", encoding="UTF-8")
        imageFile.write(image)
        imageFile.close()

        print(f"Number of contours = {len(glyph.contours)}")
        print(f"Number of segments = {[len(contour) for contour in glyph.contours]}")

    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

if __name__ == "__main__":
    main()
