"""\
Raster Sampling Tool

Created on February 5, 2021

@author Eric Mader
"""

import os
import pathlib
from sys import argv, exit, stderr
import RasterSamplingTest

def main():

    # inputDir = "/Users/emader/Downloads/TestFonts"
    inputDir = "/Users/emader/TTCTest"
    outDir = os.path.join(inputDir, "RasterSamplingTests")

    testCount = failedCount = 0
    for path in pathlib.Path(inputDir).rglob("*.[ot]t[cf]"):
        args = RasterSamplingTest.RasterSamplingTestArgs()
        args.fontFile = str(path)
        args.fontNumber = 0
        args.glyphName = "l"
        reldir = os.path.dirname(os.path.relpath(path, inputDir))
        args.outdir = os.path.join(outDir, reldir)
        args.silent = True
        os.makedirs(args.outdir, exist_ok=True)

        print(f"{os.path.relpath(path, inputDir)}:")

        while True:
            try:
                test = RasterSamplingTest.RasterSamplingTest(args)
                test.run()
            except StopIteration:
                break
            except:
                failedCount += 1
                print("Failed\n")

            testCount += 1
            if not args.fontFile.endswith(".ttc"): break
            args.fontNumber += 1

    print(f"{testCount} tests, {failedCount} failures.")

if __name__ == "__main__":
    main()
