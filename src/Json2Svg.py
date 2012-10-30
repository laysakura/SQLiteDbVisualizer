import SvgConfig
import DbFormatConfig
from DbInfoTemplate import PageType
import json
import pysvg.structure
import pysvg.builders
import pysvg.text


class Json2Svg(object):
    def __init__(self, jsonPath, svgPath,
                 jsonEncoding=DbFormatConfig.main["dbInfoJsonEncoding"]):
        with open(jsonPath) as f_json:
            self._dbinfo = json.load(f_json, jsonEncoding)
        self._svgPath = svgPath

    def dumpSvg(self):
        self._preDraw()
        self._draw()
        self._postDraw()

    def _preDraw(self):
        self._prepPysvgObj()
        self._setDrawParam()
        self._setBtreeColorDict()

    def _draw(self):
        self._drawBackground()
        self._drawBtreeList(SvgConfig.btreeList["x"],
                            SvgConfig.btreeList["y"])
        self._drawPageList(SvgConfig.pageList["x"],
                           self._pageListY)

    def _postDraw(self):
        self._svgDoc.save(self._svgPath)


    def _prepPysvgObj(self):
        self._svgDoc = pysvg.structure.svg()
        self._shapeBuilder = pysvg.builders.ShapeBuilder()

    def _setDrawParam(self):
        # BtreeList
        self._btreeLegendHeight = SvgConfig.btreeList["legendHeight"]
        self._btreeLegendNCol = SvgConfig.btreeList["legendNCol"]
        self._nBtree = len(self._dbinfo["dbMetadata"]["btrees"])
        self._btreeLegendNRow = self._nBtree / self._btreeLegendNCol + 1
        self._btreeListWidth = SvgConfig.page["width"]
        self._btreeListHeight = self._btreeLegendHeight * self._btreeLegendNRow
        self._btreeLegendWidth = self._btreeListWidth / self._btreeLegendNCol

        # PageList
        self._pageWidth = SvgConfig.page["width"]
        self._cellHeight = SvgConfig.cell["height"]
        self._nRowsInPage = self._dbinfo["dbMetadata"]["pageSize"] / self._pageWidth
        self._pageHeight = self._cellHeight * self._nRowsInPage
        self._pageListY = SvgConfig.btreeList["y"] + self._btreeListHeight
        self._pageListHeight = self._pageHeight * self._dbinfo["dbMetadata"]["nPages"]

        # Background
        self._backgroundWidth = (
            max(SvgConfig.btreeList["x"], SvgConfig.pageList["x"]) +  # Max offset
            max(self._btreeListWidth, SvgConfig.page["width"])    # Max width
        )
        self._backgroundHeight = (
            SvgConfig.btreeList["y"] +  # Y of top element
            self._btreeListHeight + self._pageListHeight  # Sum of each element height
        )

    def _setBtreeColorDict(self):
        btreeList = self._dbinfo["dbMetadata"]["btrees"]
        self._btreeColorDict = {}
        for i, btree in enumerate(btreeList):
            colorPalette = SvgConfig.btreeColorPalette
            self._btreeColorDict[btree["name"]] = colorPalette[i % len(colorPalette)]

    def _drawBackground(self):
        self._svgDoc.addElement(
            self._shapeBuilder.createRect(
                0, 0,
                self._backgroundWidth, self._backgroundHeight,
                fill=SvgConfig.background["fillColor"]))

    def _drawPageList(self, x, y):
        for pageNum in range(1, self._dbinfo["dbMetadata"]["nPages"] + 1):
            self._drawPage(x, y + (pageNum - 1) * self._pageHeight,
                           pageNum)

    def _drawBtreeList(self, x, y):
        btreeList = self._dbinfo["dbMetadata"]["btrees"]
        for i, btree in enumerate(btreeList):
            legendX = x + self._btreeLegendWidth * (i % self._btreeLegendNCol)
            legendY = y + self._btreeLegendHeight * (i / self._btreeLegendNCol)
            self._drawBtreeLegend(legendX, legendY, btree)

    def _drawBtreeLegend(self, x, y, btree):
        # Color sample
        self._svgDoc.addElement(
            self._shapeBuilder.createRect(
                x, y,
                SvgConfig.btreeList["legendHeight"] - 1,
                SvgConfig.btreeList["legendHeight"] - 1,
                fill=self._btreeColorDict[btree["name"]],
                strokewidth=SvgConfig.btreeList["legendStrokeWidth"],
                stroke=SvgConfig.btreeList["legendStrokeColor"]))

        # Btree name
        style = pysvg.builders.StyleBuilder()
        style.setFontSize(SvgConfig.btreeList["legendFontSize"])
        self._svgDoc.addElement(
            pysvg.text.text(btree["name"],
                            x=x + SvgConfig.btreeList["legendHeight"],
                            y=y + SvgConfig.btreeList["legendDiffY"],
                            style=style.getStyle()))

    def _drawPage(self, x, y, pageNum):
        pageType = self._dbinfo["pages"][str(pageNum)]["pageMetadata"]["pageType"]
        self._svgDoc.addElement(
            self._shapeBuilder.createRect(
                x, y,
                self._pageWidth, self._pageHeight,
                fill=SvgConfig.page["fillColor"],
                strokewidth=SvgConfig.page["strokeWidth"],
                stroke=SvgConfig.page[pageType + "strokeColor"]))
        self._drawCells(x, y, pageNum)

    def _drawCells(self, pageX, pageY, pageNum):
        page = self._dbinfo["pages"][str(pageNum)]
        pageType = page["pageMetadata"]["pageType"]
        cells = page["cells"]
        for cell in cells:
            self._drawCell(pageX, pageY,
                           self._btreeColorDict[page["pageMetadata"]["livingBtree"]],
                           cell, pageType)

    def _drawCell(self, pageX, pageY, fillColor, cell, pageType):
        offset = cell["offset"]
        remSize = cell["cellSize"]
        x = pageX + offset % self._pageWidth
        y = pageY + (offset / self._pageWidth) * self._cellHeight
        while remSize > 0:
            widthInRow = min(remSize, self._pageWidth - x)
            self._svgDoc.addElement(
                self._shapeBuilder.createRect(
                    x, y,
                    widthInRow, self._cellHeight,
                    fill=fillColor))
            remSize -= widthInRow
            x = pageX
            y += self._cellHeight
        self._drawCellInfo(pageX + offset % self._pageWidth,
                           pageY + (offset / self._pageWidth) * self._cellHeight,
                           cell, pageType)

    def _drawCellInfo(self, cellX, cellY, cell, pageType):
        style = pysvg.builders.StyleBuilder()
        style.setFontSize(self._cellHeight)
        s = ""
        if pageType in (PageType.TABLE_LEAF, PageType.TABLE_INTERIOR) :
            s = str(cell["rid"])
        self._svgDoc.addElement(
            pysvg.text.text(s,
                            x=cellX + (self._cellHeight/2),
                            y=cellY + (self._cellHeight/2),
                            style=style.getStyle()))
