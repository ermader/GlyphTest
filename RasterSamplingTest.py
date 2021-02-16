"""\
Raster Sampling Tests

Created on October 26, 2020

@author Eric Mader
"""

import os
from sys import argv, exit, stderr
import xml.etree.ElementTree as ET
import re
from io import StringIO
import math
import logging
import warnings
import statistics
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import scipy.stats
import statsmodels.api
import CharNames  # From UnicodeData...
from GlyphTest import GTFont
from Bezier import Bezier, BOutline, drawOutline
import BezierUtilities as buitls
from SegmentPen import SegmentPen
from SVGPathPen import SVGPathPen
from svgpathtools import Line, Path, is_bezier_segment, wsvg
from SVGPathOutline import SVGPathOutline, SVGPathContour, SVGPathSegment
import SVGPathUtilities
from UFOFont import UFOFont
import PathUtilities
import ContourPlotter
from TestArgumentIterator import TestArgs
import TextUtilities

# Polynomial = np.polynomial.Polynomial

class RasterSamplingTestArgs(TestArgs):

    widthMethodLeftmost = 0
    widthMethodRightmost = 1
    widthMethodLeastspread = 2
    boundsTypes = {"typographic": (True, False), "glyph": (False, True), "both": (True, True)}
    widthMethods = {"leftmost": widthMethodLeftmost, "rightmost": widthMethodRightmost, "leastspread": widthMethodLeastspread}

    def __init__(self):
        self.typoBounds = self.glyphBounds = False
        self.widthMethod = self.widthMethodLeftmost
        self.outdir = ""
        # self.indir = ""
        self.silent = False
        TestArgs.__init__(self)

    @classmethod
    def forArguments(cls, argumentList):
        args = RasterSamplingTestArgs()
        args.processArguments(argumentList)
        return args

    def processArgument(self, argument, arguments):
        if argument == "--bounds":
            boundsType = arguments.nextExtra("bounds")
            if boundsType in self.boundsTypes.keys():
                self.typoBounds, self.glyphBounds = self.boundsTypes[boundsType]
        elif argument == "--widthMethod":
            widthMethod = arguments.nextExtra("width method")
            if widthMethod in self.widthMethods.keys():
                self.widthMethod = self.widthMethods[widthMethod]
        else:
            TestArgs.processArgument(self, argument, arguments)

def splitCurve(curve, splits):
    p1, p2, p3 = curve.controlPoints
    q1 = p1
    r3 = p3
    q2 = PathUtilities.midpoint([p1, p2])
    r2 = PathUtilities.midpoint([p2, p3])
    q3 = r1 = PathUtilities.midpoint([q2, r2])
    q = Bezier([q1, q2, q3])
    r = Bezier([r1, r2, r3])

    if q.direction != Bezier.dir_mixed:
        splits.append(q)
    else:
        splitCurve(q, splits)

    if r.direction != Bezier.dir_mixed:
        splits.append(r)
    else:
        splitCurve(r, splits)

def sortByP0(list):
    if len(list) == 0: return
    list.sort(key=lambda b: b.startX)

def rasterLength(raster):
    return PathUtilities.length(raster.controlPoints)

def curvesAtY(curveList, y):
    return list(filter(lambda curve: curve.boundsRectangle.crossesY(y), curveList))

def leftmostIntersection(curves, raster):
    leftmostX = leftmostY = 65536

    for curve in curves:
        ipx, ipy = curve.pointXY(curve.intersectWithLine(raster))
        if ipx < leftmostX:
            leftmostY = ipy
            leftmostX = ipx

    return curves[0].xyPoint(leftmostX, leftmostY)

def rightmostIntersection(curves, raster):
    rightmostX = rightmostY = -65536

    for curve in curves:
        ipx, ipy = curve.pointXY(curve.intersectWithLine(raster))
        if ipx > rightmostX:
            rightmostY = ipy
            rightmostX = ipx

    return curves[0].xyPoint(rightmostX, rightmostY)

def direction(curve):
    startY = curve.startY
    endY = curve.endY

    # if curve.order == 1:
    #     if startY < endY: return Bezier.dir_up
    #     if startY > endY: return Bezier.dir_down
    #     return Bezier.dir_flat

    minY = min(startY, endY)
    maxY = max(startY, endY)
    # cps = curve.controlPoints
    #
    # if curve.order == 2:
    #     cp1x, cp1y = curve.pointXY(cps[1])
    #     if cp1y < minY or cp1y > maxY: return Bezier.dir_mixed
    #     if startY < endY: return Bezier.dir_up
    #     if startY > endY: return Bezier.dir_down
    #
    # if curve.order == 3:
    #     cp2x, cp2y = curve.pointXY(cps[2])
    #     if cp2y < minY or cp2y > maxY: return Bezier.dir_mixed
    #     if startY < endY: return Bezier.dir_up
    #     if startY > endY: return Bezier.dir_down
    #
    # # For now, assume any higher-order curves are mixed
    # return Bezier.dir_mixed

    ocps = curve.controlPoints[1:-1]
    for ocp in ocps:
        ocpx, ocpy = curve.pointXY(ocp)
        if ocpy < minY or ocpy > maxY: return Bezier.dir_mixed

    # if we get here, the curve is either order 1 or
    # has a uniform direction. Curves with order 2 or higher
    # with startY and endY equal are likely mixed and got caught
    # above.
    if startY < endY: return Bezier.dir_up
    if startY > endY: return Bezier.dir_down
    return Bezier.dir_flat

def pathCoordinate(path):
    # This assumes that the y-coordinate is a positive integer
    return int(re.findall("M-?[0-9\.]+,(\d+)", path.attrib["d"])[0])

def lengthInPx(value):
    pxPerInch = 96
    unitsPerInch = {"in": 1, "cm": 2.54, "mm": 25.4, "pt": 72, "pc": 6, "px": pxPerInch}

    # this RE will match all valid length specifications, and some that aren't
    # we assume that the input value is well-formed
    number, units = re.findall("([+-]?[0-9.]+)([a-z]{2})?", value)[0]
    perInch = unitsPerInch.get(units if units else "px")

    # ignore any invalid unit specification
    return float(number) * pxPerInch / (perInch if perInch else pxPerInch)

def scaleContours(contours, unitsPerEM):
    if unitsPerEM > 1000:
        scaleFactor = 1000 / unitsPerEM
        scaleTransform = PathUtilities.GTTransform.scale(scaleFactor, scaleFactor)
        return scaleTransform.applyToContours(contours)

    return contours

def medianLines(outline, line, median):
    startX, startY = line.pointXY(line.start)
    endX, endY = line.pointXY(line.end)
    m2 = median / 2

    p1 = line.xyPoint(startX - m2, startY)
    p2 = line.xyPoint(endX - m2, endY)
    leftLine = outline.segmentFromPoints([p1, p2])


    p1 = line.xyPoint(startX + m2, startY)
    p2 = line.xyPoint(endX + m2, endY)
    rightLine = outline.segmentFromPoints([p1, p2])

    return leftLine, rightLine

class RasterSamplingTest(object):
    def __init__(self, args):
        self._args = args

        if args.fontFile.endswith(".ufo"):
            self._font = UFOFont(args.fontFile)
        else:
            self._font = GTFont(args.fontFile, fontName=args.fontName, fontNumber=args.fontNumber)

    def run(self):
        useBezierOutline = True  # should be in the args...
        args = self._args
        font = self._font
        indent = ""

        fullName = font.fullName
        if fullName.startswith("."): fullName = fullName[1:]

        if args.silent:
            indent = "    "
            print(f"{indent}{fullName}:")

        level = logging.DEBUG if args.debug else logging.WARNING
        logging.basicConfig(level=level)
        logger = logging.getLogger("raster-sampling-test")

        glyph = args.getGlyph(font)
        glyphName = glyph.name()
        charCode = font.unicodeForName(glyphName)
        charInfo = f"U+{charCode:04X} {CharNames.CharNames.getCharName(charCode)}"

        unitsPerEM = font.unitsPerEm()

        if useBezierOutline:
            pen = SegmentPen(font.glyphSet, logger)
            font.glyphSet[glyph.name()].draw(pen)
            outline = BOutline(scaleContours(pen.contours, unitsPerEM))
        else:
            spen = SVGPathPen(font.glyphSet, logger)
            font.glyphSet[glyph.name()].draw(spen)
            scaled = scaleContours(spen.outline, unitsPerEM)
            outline = SVGPathOutline.fromContours(scaled)

        contourCount = len(outline.contours)
        if contourCount > 3:
            print(f"{indent}(this glyph has {contourCount} contours, so results may not be useful)")

        outlineBounds = outline.boundsRectangle
        outlineBoundsLeft = outlineBounds.left if outlineBounds.left >= 0 else 0
        outlineBoundsCenter = outlineBoundsLeft + outlineBounds.width / 2

        upList = []
        downList = []
        flatList = []
        mixedList = []

        baseline = [(min(0, outlineBounds.left), 0), (outlineBounds.right, 0)]
        baselineBounds = PathUtilities.GTBoundsRectangle(*baseline)

        for contour in outline:
            for curve in contour:
                dir = direction(curve)
                if dir == Bezier.dir_up:
                    upList.append(curve)
                elif dir == Bezier.dir_down:
                    downList.append(curve)
                elif dir == Bezier.dir_flat:
                    flatList.append(curve)
                # else: mixedList.append(curve)
                else:
                    startY = curve.startY
                    endY = curve.endY
                    if endY > startY: upList.append(curve)
                    elif endY < startY: downList.append(curve)
                    else: flatList.append(curve)
                # else:
                #     dirfun = lambda x, y: (x < y) - (x > y)
                #     nTangents = 10
                #     ycoords = []
                #     for i in range(nTangents + 1):
                #         t = i / nTangents
                #         px, py = curve.pointXY(curve.get(t))
                #         ycoords.append(py)
                #     dirs = [dirfun(ycoords[i], ycoords[i + 1]) for i in range(nTangents - 1)]
                #     up = 1 in dirs
                #     down = -1 in dirs
                #     if up and not down:
                #         upList.append(curve)
                #     elif down and not up:
                #         downList.append(curve)
                #     else:
                #         mixedList.append(curve)

        sortByP0(upList)
        sortByP0(downList)
        sortByP0(flatList)

        if not args.silent:
            print("up list:")
            for b in upList: print(b.controlPoints)

            print("\ndown list:")
            for b in downList: print(b.controlPoints)

            print("\nflat list:")
            for b in flatList: print(b.controlPoints)

            if len(mixedList) > 0:
                print("\nmixed list:")
                # dirfun = lambda x, y: (x < y) - (x > y)

                for b in mixedList:
                    print(b.controlPoints)

                    # splits = []
                    # splitCurve(b, splits)
                    #
                    # for s in splits: print(f"    {controlPoints(s)}")
                    # nTangents = 10
                    # ycoords = []
                    # for i in range(nTangents + 1):
                    #     t = i / nTangents
                    #     px, py = b.pointXY(b.get(t))
                    #     # tx, ty = b._tangent(t)
                    #     # print(f"    ({px}, {py}), ({tx}, {ty})")
                    #     ycoords.append(py)
                    # dirs = [dirfun(ycoords[i], ycoords[i+1]) for i in range(nTangents-1)]
                    # up = 1 in dirs
                    # down = -1 in dirs
                    # if up and not down: print("    really dir_up")
                    # elif down and not up: print("    really dir_down")
                    # else: print("    really dir_mixed")
                print()
        # else:
        #     print(f"{os.path.relpath(args.fontFile, args.indir)}:")

        overallBounds = baselineBounds.union(outlineBounds)
        cp = ContourPlotter.ContourPlotter(overallBounds.points)

        # Make room for two lines in the content margins
        cp._contentMargins.top *= 2
        cp._contentMargins.bottom *= 2

        # Make sure the content margins are wide enough to
        # hold the label strings.
        ctFont = TextUtilities.ctFont(cp.labelFont, cp.labelFontSize)
        fullNameWidth = TextUtilities.stringWidth(fullName, ctFont)
        charInfoWidth = TextUtilities.stringWidth(charInfo, ctFont)
        labelWidth = max(fullNameWidth, charInfoWidth)
        if labelWidth > overallBounds.width:
            margin = (labelWidth - overallBounds.width) / 2
            cp._contentMargins.left = margin
            cp._contentMargins.right = margin
        else:
            margin = cp._contentMargins.left

        cp.pushStrokeAttributes(dash="2,4")
        cp.drawPointsAsSegments(baseline, color=PathUtilities.GTColor.fromName("cyan"))
        cp.drawContours([outlineBounds.contour], color=PathUtilities.GTColor.fromName("magenta"))
        cp.popStrokeAtributes()

        cp.drawPaths(outline)

        cp.drawText(outlineBoundsCenter + margin, cp._labelFontSize * 2, "center", fullName)
        cp.drawText(outlineBoundsCenter + margin, cp._labelFontSize / 4, "center", charInfo)

        rasters = []
        height = outlineBounds.height
        lowerBound = round(outlineBounds.bottom + height * .30)
        upperBound = round(outlineBounds.bottom + height * .70)
        interval = round(height * .02)
        left, _, right, _ = overallBounds.points
        for y in range(lowerBound, upperBound, interval):
            p1 = outline.xyPoint(left, y)
            p2 = outline.xyPoint(right, y)
            raster = outline.segmentFromPoints([p1, p2])

            upCurvesAtY = curvesAtY(upList, y)
            if len(upCurvesAtY) == 0: continue

            if args.widthMethod == RasterSamplingTestArgs.widthMethodLeftmost:
                p1 = leftmostIntersection(upCurvesAtY, raster)
            elif args.widthMethod == RasterSamplingTestArgs.widthMethodRightmost:
                p1 = rightmostIntersection(curvesAtY(upList, y), raster)

            downCurvesAtY = curvesAtY(downList, y)
            if len(downCurvesAtY) == 0: continue
            p2 = leftmostIntersection(downCurvesAtY, raster)
            rasters.append(outline.segmentFromPoints([p1, p2]))
            cp.drawPaths([outline.pathFromSegments(raster)], color=PathUtilities.GTColor.fromName("red"))

        midpoints = []
        widths = []
        for raster in rasters:
            mp = raster.midpoint
            midpoints.append(mp)
            widths.append(round(rasterLength(raster), 2))
            cp.drawPointsAsCircles(raster.controlPoints, 4, [PathUtilities.GTColor.fromName("blue")])
            cp.drawPointsAsCircles([mp], 4, [PathUtilities.GTColor.fromName("green")])

        # linregress(midpoints) can generate warnings if the best fit line is
        # vertical. So we swap x, y and do the best fit that way.
        # (which of course, will generate warnings if the best fit line is horizontal)
        xs, ys = outline.unzipPoints(midpoints)
        b, a, rValue, pValue, stdErr = scipy.stats.linregress(ys, xs)
        r2 = rValue * rValue

        my0 = outlineBounds.bottom
        myn = outlineBounds.top
        cp.pushStrokeAttributes(width=2, opacity=0.25, color=PathUtilities.GTColor.fromName("green"))

        # x = by + a
        p1 = outline.xyPoint(my0 * b + a, my0)
        p2 = outline.xyPoint(myn * b + a, myn)
        line = outline.segmentFromPoints([p1, p2])
        cp.drawPaths([outline.pathFromSegments(line)])
        cp.popStrokeAtributes()

        print(f"{indent}a = {round(a, 2)}, b = {round(b, 4)}, R\u00B2 = {round(r2, 4)}")

        strokeAngle = round(PathUtilities.slopeAngle(line.controlPoints), 1)

        avgWidth = round(statistics.mean(widths), 2)
        quartiles = statistics.quantiles(widths, n=4, method="inclusive")
        q1 = round(quartiles[0], 2)
        median = round(quartiles[1], 2)
        q3 = round(quartiles[2], 2)
        minWidth = round(min(widths), 2)
        maxWidth = round(max(widths), 2)
        print(f"{indent}angle = {strokeAngle}\u00B0")
        print(f"{indent}widths: min = {minWidth}, Q1 = {q1}, median = {median}, mean = {avgWidth}, Q3 = {q3}, max = {maxWidth}")
        if args.silent: print()

        cp.pushStrokeAttributes(width=2, opacity=0.25, color=PathUtilities.GTColor.fromName("orange"))
        leftLine, rightLine = medianLines(outline, line, median)
        cp.drawPaths([outline.pathFromSegments(leftLine)])
        cp.drawPaths([outline.pathFromSegments(rightLine)])
        cp.popStrokeAtributes()


        cp.setFillColor(PathUtilities.GTColor.fromName("black"))

        cp.drawText(outlineBoundsCenter + margin, -cp._labelFontSize * 1.5, "center",
                    f"Stroke angle = {strokeAngle}\u00B0")
        cp.drawText(outlineBoundsCenter + margin, -cp._labelFontSize * 3, "center", f"Best fit R\u00B2 = {round(r2, 4)}")

        image = cp.generateFinalImage()

        root = ET.fromstring(image)
        svgNameSpace = root.tag[1:-4]  # remove initial "{" and final "}svg"
        nameSpaces = {"svg": svgNameSpace}

        viewBox = re.findall("([0-9.]+)+", root.attrib['viewBox'])
        rWidth = float(viewBox[2])
        rHeight = float(viewBox[3])

        # root[1] is the diagram
        diagTranslations = re.findall("translate\(([0-9.]+), ([0-9.]+)\)", root[1].attrib["transform"])
        diagTranslationBefore = float(diagTranslations[0][1])
        diagTranslationAfter = float(diagTranslations[1][1])
        paths = root[1].findall("svg:path", nameSpaces)

        # the fist three paths are the bounding boxes and the baseline
        # then a path for each contour in the glyph followed by a
        # path for each raster line, and finally the stroke midpoint line
        firstRaster = 2 + len(outline.contours)
        midRasterOffset = (pathCoordinate(paths[firstRaster]) + pathCoordinate(paths[-4])) / 2

        # Turn off the debug info from matplotlib
        matplotlib.set_loglevel("warn")
        matplotlib.use("svg")
        figWidth, figHeight = matplotlib.rcParams["figure.figsize"]
        gridSpec = {"height_ratios": [10, 70, 20], "hspace": 0.1}
        figSize = [figWidth, figHeight * 1.25]
        fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, sharex=True, gridspec_kw=gridSpec, figsize=figSize)

        ax1.set_title(f"Stroke Widths of {fullName}_{glyphName}")
        ax1.set_axis_off()

        collLabels = ["Min", "Q1", "Median", "Mean", "Q3", "Max"]
        cellText = [[f"{minWidth}", f"{q1}", f"{median}", f"{avgWidth}", f"{q3}", f"{maxWidth}"]]
        ax1.table(cellText=cellText, cellLoc="center", colLabels=collLabels, loc="upper center", edges="closed")

        n, bins, patches = ax2.hist(widths, bins=12, align='mid', density=True)

        # add a 'best fit' line
        mu = statistics.mean(widths)
        sigma = statistics.stdev(widths)
        if sigma == 0.0: sigma = 1.0  # hack: if all widths are the same, sigma == 0...
        y = ((1 / (np.sqrt(2 * np.pi) * sigma)) *
             np.exp(-0.5 * (1 / sigma * (bins - mu)) ** 2))

        widths.sort()

        dens = statsmodels.api.nonparametric.KDEUnivariate(widths)
        dens.fit(bw=0.9)
        densVals = dens.evaluate(widths)

        ax2.plot(bins, y, 'm--', widths, densVals, "r--")
        ax2.vlines([avgWidth, median], 0, max(max(n), densVals.max()), colors=["tab:green", "tab:orange"])
        ax2.set_ylabel('Probability density')

        ax3.set_xlabel('Width')
        ax3.boxplot(widths, vert=False, showmeans=True, meanline=True, flierprops={"markerfacecolor": "r"})

        pltString = StringIO()
        plt.savefig(pltString, format="svg")
        pltString.seek(0)
        pltImage = pltString.read()
        pltRoot = ET.fromstring(pltImage)

        pltWidth = lengthInPx(pltRoot.attrib["width"])
        pltHeight = lengthInPx(pltRoot.attrib["height"])
        histOffset = diagTranslationBefore - midRasterOffset - diagTranslationAfter - (pltHeight / 2)

        root.set("viewBox", f"0 0 {rWidth + pltWidth} {rHeight}")
        root.append(pltRoot)
        root[2].set("x", f"{rWidth}")
        root[2].set("y", f"{histOffset}")

        ET.register_namespace("", nameSpaces["svg"])
        svgName = os.path.join(args.outdir, f"RasterSamplingTest {fullName}_{glyphName}.svg")
        ET.ElementTree(root).write(svgName, xml_declaration=True,
                                   encoding="UTF-8")

        plt.close(fig)


def main():
    argumentList = argv
    args = None
    programName = os.path.basename(argumentList.pop(0))
    if len(argumentList) == 0:
        print(__doc__, file=stderr)
        exit(1)
    try:
        args = RasterSamplingTestArgs.forArguments(argumentList)
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    test = RasterSamplingTest(args)
    test.run()

if __name__ == "__main__":
    main()
