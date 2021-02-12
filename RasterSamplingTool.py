"""\
Raster Sampling Tool

Created on February 5, 2021

@author Eric Mader
"""

import os
import pathlib
from sys import argv, exit, stderr
from TestArgumentIterator import TestArgs
import RasterSamplingTest

class RasterSamplingToolArgs(TestArgs):
    def __init__(self):
        self.inputDir = ""
        self.outputDir = ""
        TestArgs.__init__(self)

    @classmethod
    def forArguments(cls, argumentList):
        args = RasterSamplingToolArgs()
        args.fontFile = "(dummy)"  # so TestArgumentIterator doesn't complain about missing "--font"...
        args.processArguments(argumentList)
        return args

    def processArgument(self, argument, arguments):
        if argument == "--input":
            self.inputDir = arguments.nextExtra("input directory")
        elif argument == "--output":
            self.outputDir = arguments.nextExtra("output directory")
        else:
            TestArgs.processArgument(self, argument, arguments)


def main():
    argumentList = argv
    args = None
    programName = os.path.basename(argumentList.pop(0))
    if len(argumentList) == 0:
        print(__doc__, file=stderr)
        exit(1)

    try:
        toolArgs = RasterSamplingToolArgs.forArguments(argumentList)
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    testCount = failedCount = 0
    for path in pathlib.Path(toolArgs.inputDir).rglob("*.[ot]t[cf]"):
        testArgs = RasterSamplingTest.RasterSamplingTestArgs()
        testArgs.fontFile = str(path)
        testArgs.fontNumber = 0
        testArgs.glyphName = toolArgs.glyphName
        testArgs.glyphID = toolArgs.glyphID
        testArgs.charCode = toolArgs.charCode
        reldir = os.path.dirname(os.path.relpath(path, os.path.dirname(toolArgs.inputDir)))
        testArgs.outdir = os.path.join(toolArgs.outputDir, reldir)
        testArgs.silent = True
        os.makedirs(testArgs.outdir, exist_ok=True)

        print(f"{os.path.relpath(path, toolArgs.inputDir)}:")

        while True:
            try:
                test = RasterSamplingTest.RasterSamplingTest(testArgs)
                test.run()
            except StopIteration:
                break
            except:
                failedCount += 1
                print("Failed\n")

            testCount += 1
            if not testArgs.fontFile.endswith(".ttc"): break
            testArgs.fontNumber += 1

    print(f"{testCount} tests, {failedCount} failures.")

if __name__ == "__main__":
    main()
