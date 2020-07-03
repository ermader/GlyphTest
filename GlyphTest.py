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
import ContourPlotter

class GlyphTestAgrumentIterator(ArgumentIterator):
    def nextExtraAsCharCode(self, valueName):
        """\
        Returns the next extra argument as a character code: either a hex
        integer preceded by an optional 0x or U+, or a single character.
        Raise ValueError if there are no more arguments, or if the next
        argument starts with “--”, or if the char code is zero.
        """
        charCode = None
        value = self.nextExtra(valueName)
        m = fullmatch(r"(?:0x|U\+)?([0-9A-Za-z]+)", value)
        if m:
            v = m.groups()[0]
            charCode = int(v, 16)
        elif len(value) == 1:
                charCode = ord(value)

        if not charCode or charCode == 0:
            raise ValueError(f"Argument “{valueName}” for option “{self._optionName}” should be a positive hex integer or a single character; got “{value}”.")
        return charCode

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
            raise ValueError("One of --glyphName, --glyphID, --charCode must be sepcified.")



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

        arguments = GlyphTestAgrumentIterator(argumentList)
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
            elif argument == "--glyphID":
                args.glyphID = arguments.nextExtraAsPosInt("glyph ID")
            elif argument == "--charCode":
                args.charCode = arguments.nextExtraAsCharCode("character code")
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

def _getFontName(ttFont, nameID):
    nameRecord = ttFont["name"].getName(nameID, 3, 1, 0x0409) # PostScriptName, Windows, Unicode BMP, English
    if nameRecord is None:
        nameRecord = ttFont["name"].getName(nameID, 1, 0) # PostScriptName, Mac, Roman
    if nameRecord is not None:
        return str(nameRecord)
    return None

def _getPostScriptName(ttFont):
    return _getFontName(ttFont, 6)
    # postScriptNameRecord = ttFont["name"].getName(6, 3, 1) # PostScriptName, Windows, Unicode BMP
    # if postScriptNameRecord is None:
    #     postScriptNameRecord = ttFont["name"].getName(6, 1, 0) # PostScriptName, Mac, Roman
    # if postScriptNameRecord is not None:
    #     return str(postScriptNameRecord)
    # return None

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

        cp = ContourPlotter.ContourPlotter(glyph.bounds)

        for contour in glyph.contours:
            cp.drawContour(contour)

        image = cp.generateFinalImage()

        fullName = _getFullName(font)
        if fullName.startswith("."): fullName = fullName[1:]
        imageFile = open(f"{fullName}_{glyphName}.svg", "wt", encoding="UTF-8")
        imageFile.write(image)
        imageFile.close()

        print(f"Number of contours = {len(glyph.contours)}")
        print(f"Number of segments = {[len(contour) for contour in glyph.contours]}")

    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

if __name__ == "__main__":
    main()
