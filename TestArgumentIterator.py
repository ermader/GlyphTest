"""\
Command line argument processor for glyph tests.

Created on October 26, 2020

@author Eric Mader
"""
from re import fullmatch
from FontDocTools.ArgumentIterator import ArgumentIterator

class TestArgumentIterator(ArgumentIterator):
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
        if fontFile.endswith(".ttc") or fontFile.endswith(".otf"):
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

class TestArgs:
    def __init__(self, argumentList):
        self.debug = False
        self.fontFile = None
        self.fontName = None
        self.glyphName = None
        self.glyphID = None
        self.charCode = None
        # self.steps = 20

        arguments = TestArgumentIterator(argumentList)
        argumentsSeen = {}

        for argument in arguments:
            if argument in argumentsSeen:
                raise ValueError("Duplicate option “" + argument + "”.")
            argumentsSeen[argument] = True

            self.processArgument(argument, arguments)

        self.completeInit()

    def processArgument(self, argument, arguments):
        if argument == "--font":
            self.fontFile, self.fontName = arguments.nextExtraAsFont("font")
        elif argument == "--glyph":
            extra = arguments.nextExtra("glyph")
            if len(extra) == 1:
                self.charCode = ord(extra)
            elif extra[0] == "/":
                self.glyphName = extra[1:]
            elif extra[0] == "u":
                self.charCode = TestArgs.getHexCharCode(extra[1:])
            elif extra[0:3] == "gid":
                self.glyphID = TestArgs.getGlyphID(extra[3:])
        # elif argument == "--steps":
        #     self.steps = arguments.nextExtraAsPosInt("steps")
        elif argument == "--debug":
            self.debug = True
        else:
            raise ValueError(f"Unrecognized option “{argument}”.")

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
        Return a new TestArgs object representing the given
        argument list.
        Raise ValueError if the argument list is missing required options,
        is missing required extra arguments for options,
        has unsupported options, or has unsupported extra arguments.
        """

        # pylint: disable=too-many-branches

        arguments = TestArgumentIterator(argumentList)
        args = TestArgs()
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

    def getGlyph(self, font):
        if self.glyphName: return font.glyphForName(self.glyphName)
        if self.glyphID: return font.glyphForIndex(self.glyphID)
        if self.charCode: return font.glyphForCharacter(self.charCode)
