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

oppositeDirection = {
    Bezier.dir_up: Bezier.dir_down,
    Bezier.dir_down: Bezier.dir_up,
    Bezier.dir_flat: Bezier.dir_flat,
    # Bezier.dir_mixed: Bezier.dir_mixed
}

widthSelection = {
    RasterSamplingTestArgs.widthMethodLeftmost: (True, False),
    RasterSamplingTestArgs.widthMethodRightmost: (False, True),
    RasterSamplingTestArgs.widthMethodLeastspread: (True, True)
}

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

class RasterSamplingTest(object):
    def __init__(self, args):
        self._args = args

        if args.fontFile.endswith(".ufo"):
            self._font = UFOFont(args.fontFile)
        else:
            self._font = GTFont(args.fontFile, fontName=args.fontName, fontNumber=args.fontNumber)

    @classmethod
    def sortByP0(cls, list):
        if len(list) == 0: return
        list.sort(key=lambda b: b.startX)

    @classmethod
    def rasterLength(cls, raster):
        return PathUtilities.length(raster.controlPoints)

    @classmethod
    def curvesAtY(cls, curveList, y):
        return list(filter(lambda curve: curve.boundsRectangle.crossesY(y), curveList))

    @classmethod
    def leftmostPoint(cls, points, outline):
        leftmostX = 65536
        leftmostIndex = -1
        for index, point in enumerate(points):
            # if point is None, the curve is a line
            # that's colinear with the raster
            if point is not None:
                ipx, _ = outline.pointXY(point)
                if ipx < leftmostX:
                    leftmostX = ipx
                    leftmostIndex = index

        return leftmostIndex

    @classmethod
    def leftmostIntersection(cls, intersections, curves, direction):
        leftmostX = 65536
        leftmostC = -1

        for index, curve in enumerate(curves):
            if cls.direction(curve) == direction:
                ipx, _ = curve.pointXY(intersections[index])
                if ipx < leftmostX:
                    leftmostX = ipx
                    leftmostC = index

        return intersections[leftmostC]

    @classmethod
    def rightmostIntersection(cls, intersections, curves, direction):
        rightmostX = -65536
        rightmostC = -1

        for index, curve in enumerate(curves):
            if cls.direction(curve) == direction:
                ipx, _ = curve.pointXY(intersections[index])
                if ipx > rightmostX:
                    rightmostX = ipx
                    rightmostC = index

        return intersections[rightmostC]

    @classmethod
    def bestFit(cls, rasters, outline):
        midpoints = []
        widths = []
        for raster in rasters:
            mp = raster.midpoint
            midpoints.append(mp)
            widths.append(round(cls.rasterLength(raster), 2))

        # linregress(midpoints) can generate warnings if the best fit line is
        # vertical. So we swap x, y and do the best fit that way.
        # (which of course, will generate warnings if the best fit line is horizontal)
        xs, ys = outline.unzipPoints(midpoints)
        b, a, rValue, pValue, stdErr = scipy.stats.linregress(ys, xs)

        return widths, midpoints, b, a, rValue, pValue, stdErr

    @classmethod
    def direction(cls, curve):
        startY = curve.startY
        endY = curve.endY

        minY = min(startY, endY)
        maxY = max(startY, endY)

        #
        # For the purposes of edge detection
        # we don't care if the curve actually
        # has a mixed direction, only that it
        # tends upward or downward.
        #
        # ocps = curve.controlPoints[1:-1]
        # for ocp in ocps:
        #     ocpx, ocpy = curve.pointXY(ocp)
        #     if ocpy < minY or ocpy > maxY: return Bezier.dir_mixed

        # if we get here, the curve is either order 1 or
        # has a uniform direction. Curves with order 2 or higher
        # with startY and endY equal are likely mixed and got caught
        # above.
        if startY < endY: return Bezier.dir_up
        if startY > endY: return Bezier.dir_down
        return Bezier.dir_flat

    @classmethod
    def pathCoordinate(cls, path):
        # This assumes that the y-coordinate is a positive integer
        return int(re.findall("M-?[0-9\.]+,(\d+)", path.attrib["d"])[0])

    @classmethod
    def lengthInPx(cls, value):
        pxPerInch = 96
        unitsPerInch = {"in": 1, "cm": 2.54, "mm": 25.4, "pt": 72, "pc": 6, "px": pxPerInch}

        # this RE will match all valid length specifications, and some that aren't
        # we assume that the input value is well-formed
        number, units = re.findall("([+-]?[0-9.]+)([a-z]{2})?", value)[0]
        perInch = unitsPerInch.get(units if units else "px")

        # ignore any invalid unit specification
        return float(number) * pxPerInch / (perInch if perInch else pxPerInch)

    def scaleContours(self, contours):
        upem = self._font.unitsPerEm()
        if upem > 1000:
            scaleFactor = 1000 / upem
            scaleTransform = PathUtilities.GTTransform.scale(scaleFactor, scaleFactor)
            return scaleTransform.applyToContours(contours)

        return contours

    def medianLines(self, line, median):
        startX, startY = line.pointXY(line.start)
        endX, endY = line.pointXY(line.end)
        m2 = median / 2

        p1 = line.xyPoint(startX - m2, startY)
        p2 = line.xyPoint(endX - m2, endY)
        leftLine = self.outline.segmentFromPoints([p1, p2])

        p1 = line.xyPoint(startX + m2, startY)
        p2 = line.xyPoint(endX + m2, endY)
        rightLine = self.outline.segmentFromPoints([p1, p2])

        return leftLine, rightLine

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

        if useBezierOutline:
            pen = SegmentPen(font.glyphSet, logger)
            font.glyphSet[glyph.name()].draw(pen)
            outline = BOutline(self.scaleContours(pen.contours))
        else:
            spen = SVGPathPen(font.glyphSet, logger)
            font.glyphSet[glyph.name()].draw(spen)
            scaled = self.scaleContours(spen.outline)
            outline = SVGPathOutline.fromContours(scaled)

        self.outline = outline

        contourCount = len(outline.contours)
        if contourCount > 3:
            print(f"{indent}(this glyph has {contourCount} contours, so results may not be useful)")

        outlineBounds = outline.boundsRectangle
        outlineBoundsLeft = outlineBounds.left if outlineBounds.left >= 0 else 0
        outlineBoundsCenter = outlineBoundsLeft + outlineBounds.width / 2

        curveList = []

        baseline = [(min(0, outlineBounds.left), 0), (outlineBounds.right, 0)]
        baselineBounds = PathUtilities.GTBoundsRectangle(*baseline)

        for contour in outline:
            for curve in contour:
                curveList.append(curve)

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

        if args.widthMethod == RasterSamplingTestArgs.widthMethodLeftmost:
            p2function = self.leftmostIntersection
        elif args.widthMethod == RasterSamplingTestArgs.widthMethodRightmost:
            p2function = self.rightmostIntersection

        doLeft, doRight = widthSelection[args.widthMethod]

        rastersLeft = []
        rastersRight = []
        missedRasterCount = 0
        height = outlineBounds.height
        lowerBound = round(outlineBounds.bottom + height * .30)
        upperBound = round(outlineBounds.bottom + height * .70)
        interval = round(height * .02)
        left, _, right, _ = overallBounds.points
        for y in range(lowerBound, upperBound, interval):
            p1 = outline.xyPoint(left, y)
            p2 = outline.xyPoint(right, y)
            raster = outline.segmentFromPoints([p1, p2])

            curvesAtY = self.curvesAtY(curveList, y)
            if len(curvesAtY) == 0:
                missedRasterCount += 1
                continue

            intersections = [c.intersectWithLine(raster) for c in curvesAtY]

            # leftmostX = 65536
            # leftmostCurve = -1
            # for index, ip in enumerate(intersections):
            #     # if ip is None, the curve is a line
            #     # that's colinear with the raster
            #     if ip is not None:
            #         ipx, _ = outline.pointXY(ip)
            #         if ipx < leftmostX:
            #             leftmostX = ipx
            #             leftmostCurve = index

            leftmostCurve = self.leftmostPoint(intersections, outline)
            p1 = intersections[leftmostCurve]
            direction = oppositeDirection[self.direction(curvesAtY[leftmostCurve])]

            missedLeft = missedRight = False

            if doLeft:
                p2 = self.leftmostIntersection(intersections, curvesAtY, direction)

                if p1 != p2:
                    rastersLeft.append(outline.segmentFromPoints([p1, p2]))
                else:
                    missedLeft = True

            if doRight:
                p2 = self.rightmostIntersection(intersections, curvesAtY, direction)

                if p1 != p2:
                    rastersRight.append(outline.segmentFromPoints([p1, p2]))
                else:
                    missedRight = True

            # if missedLeft or missedRight:
            #     missedRasterCount += 1
            #     continue

            cp.drawPaths([outline.pathFromSegments(raster)], color=PathUtilities.GTColor.fromName("red"))

        if doLeft and doRight:
            widthsL, midpointsL, bL, aL, rValueL, pValueL, stdErrL = self.bestFit(rastersLeft, outline)
            widthsR, midpointsR, bR, aR, rValueR, pValueR, stdErrR = self.bestFit(rastersRight, outline)

            if stdErrL <= stdErrR:
                rasters = rastersLeft
                widths, midpoints, b, a, rValue, pValue, stdErr = widthsL, midpointsL, bL, aL, rValueL, pValueL, stdErrL
            else:
                rasters = rastersRight
                widths, midpoints, b, a, rValue, pValue, stdErr = widthsR, midpointsR, bR, aR, rValueR, pValueR, stdErrR
        else:
            rasters = rastersLeft if doLeft else rastersRight
            widths, midpoints, b, a, rValue, pValue, strErr = self.bestFit(rasters, outline)

        r2 = rValue * rValue

        for raster in rasters:
            cp.drawPointsAsCircles(raster.controlPoints, 4, [PathUtilities.GTColor.fromName("blue")])

        for midpoint in midpoints:
            cp.drawPointsAsCircles([midpoint], 4, [PathUtilities.GTColor.fromName("green")])

        my0 = outlineBounds.bottom
        myn = outlineBounds.top
        cp.pushStrokeAttributes(width=2, opacity=0.25, color=PathUtilities.GTColor.fromName("green"))

        # x = by + a
        p1 = outline.xyPoint(my0 * b + a, my0)
        p2 = outline.xyPoint(myn * b + a, myn)
        line = outline.segmentFromPoints([p1, p2])
        cp.drawPaths([outline.pathFromSegments(line)])
        cp.popStrokeAtributes()

        if missedRasterCount > 0:
            print(f"{missedRasterCount} rasters did not intersect the glyph.")

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
        leftLine, rightLine = self.medianLines(line, median)
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
        midRasterOffset = (self.pathCoordinate(paths[firstRaster]) + self.pathCoordinate(paths[-4])) / 2

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

        pltWidth = self.lengthInPx(pltRoot.attrib["width"])
        pltHeight = self.lengthInPx(pltRoot.attrib["height"])
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
