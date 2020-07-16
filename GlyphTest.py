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
from FontDocTools.ArgumentIterator import ArgumentIterator
from FontDocTools.Color import Color
import ContourPlotter
import PathUtilities

_colors = {
    'black': (0, 0, 0),
    'orange': (255, 165, 0),
    'darkorange': (155, 140, 0),
    'gold': (255, 215, 0),
    'cyan': (0, 255, 255),
    'indigo': (75, 0, 130),
    'violet': (238, 130, 238),
    'silver': (192, 192, 192),
    'gray': (128, 128, 128),
    'white': (255, 255, 255),
    'maroon': (128, 0, 0),
    'red': (255, 0, 0),
    'fuchsia': (255, 0, 255),
    'green': (0, 128, 0),
    'lime': (0, 255, 0),
    'olive': (128, 128, 0),
    'yellow': (255, 255, 0),
    'navy': (0, 0, 128),
    'blue': (0, 0, 255),
    'teal': (0, 128, 128),
    'aqua': (0, 255, 255),
    'magenta': (0, 255, 255)
}

def colorFromName(name):
    if name in _colors:
        red, green, blue = _colors[name]
        return Color(red, green, blue)

    return None

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
        self.rotate = None
        self.mirror = None
        self.shear = None
        self.stretch = None
        self.project = None
        self.pinwheel = None

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
            elif argument ==  "--color":
                colorName = arguments.nextExtra("color")
                args.color = colorFromName(colorName)
                if args.color is None: raise ValueError(f"{colorName} is not a valid color name")
            elif argument == "--rotate":
                args.rotate = arguments.nextExtraAsPosInt("rotation")
            elif argument == "--shear":
                args.shear = True
            elif argument == "--stretch":
                args.stretch = True
            elif argument == "--mirror":
                args.mirror = True
            elif argument == "--project":
                args.project = True
            elif argument == "--pinwheel":
                args.pinwheel = True
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

def _getFontName(ttFont, nameID):
    nameRecord = ttFont["name"].getName(nameID, 3, 1, 0x0409) # PostScriptName, Windows, Unicode BMP, English
    if nameRecord is None:
        nameRecord = ttFont["name"].getName(nameID, 1, 0) # PostScriptName, Mac, Roman
    if nameRecord is not None:
        return str(nameRecord)
    return None

def _getPostScriptName(ttFont):
    return _getFontName(ttFont, 6)

def _getFullName(ttFont):
    return _getFontName(ttFont, 4)

def openFont(args):
    # TTFont sometimes logs warnings while opening fonts that we’re
    # not concerned with. Let’s turn them off.
    getLogger("fontTools.ttLib").setLevel(ERROR)

    # Now onward with our own business.
    if args.fontFile.endswith(".ttf") or args.fontFile.endswith(".otf"):
        font = ttFont.TTFont(args.fontFile)
    else:
        assert args.fontFile.endswith(".ttc") or args.fontFile.endswith(".otc")
        # assert (args.fontName is None) == (args.fontNumber is not None)
        if args.fontName:
            fontNumber = 0
            fontNames = []
            while True:
                try:
                    font = ttFont.TTFont(args.fontFile, fontNumber=fontNumber)
                except TTLibError:
                    raise ValueError(
                        "Could not find font " + args.fontName + " within file " + args.fontFile + ". Available names: " + ", ".join(
                            fontNames) + ".")
                postScriptName = _getPostScriptName(font)
                if postScriptName == args.fontName:
                    break
                fontNames.append(postScriptName)
                font.close()
                fontNumber += 1
        # else:
        #     try:
        #         font = ttFont.TTFont(args.fontFile, fontNumber=args.fontNumber)
        #     except TTLibError as error:
        #         if fontNumber > 0:
        #             raise StopIteration()
        #         raise error

    if not "glyf" in font:
        raise ValueError(f"{_getFullName(font)} does not have a 'glyf' table.")

    return font

def getGlyphName(args, font):
    if args.glyphName: return args.glyphName
    if args.glyphID: return font.getGlyphName(args.glyphID)
    if args.charCode: return font.getBestCmap()[args.charCode]

    return None

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
        font = openFont(args)
        glyphName = getGlyphName(args, font)
        glyph = Glyph(font, glyphName)

        fontBasename = basename(args.fontFile)
        fontPostscriptName = _getPostScriptName(font)
        print(f"Drawing glyph {glyphName} from font {fontBasename}/{fontPostscriptName}")

        contours = glyph.contours
        boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
        centerPoint = boundingRect.centerPoint

        nameSuffix = ""
        colors = None
        shapes = [(contours, args.color)]
        if args.rotate:
            nameSuffix = f"_Rotated_{args.rotate}"
            contours = PathUtilities.rotateContoursAbout(contours, centerPoint, args.rotate)
            boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.project:
            nameSuffix = "_Projected"
            m1 = PathUtilities.Transform._translateMatrix(centerPoint, (0, 0))
            m2 = PathUtilities.Transform._perspectiveMatrix(0, .001, 1)
            m3 = PathUtilities.Transform._translateMatrix((0, 0), centerPoint)
            transform = PathUtilities.Transform(m1, m2, m3)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.mirror:
            nameSuffix = "_Mirrored"
            cx, _ = centerPoint
            m1 = PathUtilities.Transform._matrix(m=-cx)
            m2 = PathUtilities.Transform._matrix(a=-1)
            m3 = PathUtilities.Transform._matrix(m=cx)
            transform = PathUtilities.Transform(m1, m2, m3)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.shear:
            nameSuffix = "_Sheared"
            m1 = PathUtilities.Transform._matrix(c=0.5)
            transform = PathUtilities.Transform(m1)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.stretch:
            nameSuffix = "_Stretched"
            m1 = PathUtilities.Transform._matrix(a=2.0)
            transform = PathUtilities.Transform(m1)
            contours = transform.applyToContours(contours)
            boundingRect = PathUtilities.BoundsRectangle.fromCoutours(contours)
            shapes = [(contours, args.color)]
        elif args.pinwheel:
            nameSuffix = "_PinWheel"
            colors = ["red", "orange", "gold", "lime", "green", "blue", "indigo", "violet", "purple"]
            colorIndex = 1
            shapes = [(contours, colorFromName(colors[0]))]  # the original shape with the first color
            for degrees in range(45, 360, 45):
                m1 = PathUtilities.Transform._rotationMatrix(degrees)
                transform = PathUtilities.Transform(m1)
                rc = transform.applyToContours(contours)
                bounds = PathUtilities.BoundsRectangle.fromCoutours(rc)
                shapes.append([rc, colorFromName(colors[colorIndex])])
                colorIndex += 1

                boundingRect = boundingRect.union(bounds)

        cp = ContourPlotter.ContourPlotter(boundingRect.points)

        for contours, color in shapes:
            for contour in contours:
                cp.drawContour(contour, color)

        image = cp.generateFinalImage()

        fullName = _getFullName(font)
        if fullName.startswith("."): fullName = fullName[1:]

        imageFile = open(f"{fullName}_{glyphName}{nameSuffix}.svg", "wt", encoding="UTF-8")
        imageFile.write(image)
        imageFile.close()

        print(f"Number of contours = {len(glyph.contours)}")
        print(f"Number of segments = {[len(contour) for contour in glyph.contours]}")

    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

if __name__ == "__main__":
    main()
