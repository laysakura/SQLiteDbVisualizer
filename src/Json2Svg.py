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

    def _draw(self):
        # self._svgDoc.addElement(self._shapeBuilder.createRect(
        #         0, 0,
        #         "200px", "100px",
        #         strokewidth = 1,
        #         stroke = "black",
        #         fill = "rgb(255, 255, 0)"))

        self._drawPageList(SvgConfig.pageList["x"],
                           SvgConfig.pageList["y"])

        # print(self._svgDoc.getXML())
        self._svgDoc.save(self._svgPath)

    def _postDraw(self):
        pass


    def _prepPysvgObj(self):
        self._svgDoc = pysvg.structure.svg()
        self._shapeBuilder = pysvg.builders.ShapeBuilder()

    def _setDrawParam(self):
        self._pageWidth = SvgConfig.page["width"]
        self._cellHeight = SvgConfig.cell["height"]
        self._nRowsInPage = self._dbinfo["dbMetadata"]["pageSize"] / self._pageWidth
        self._pageHeight = self._cellHeight * self._nRowsInPage

    def _drawPageList(self, x, y):
        for pageNum in range(1, self._dbinfo["dbMetadata"]["nPages"] + 1):
            self._drawPage(x, y + (pageNum - 1) * self._pageHeight,
                           pageNum)

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
            self._drawCell(pageX, pageY, cell, pageType)

    def _drawCell(self, pageX, pageY, cell, pageType):
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
                    fill=SvgConfig.cell["fillColor"]))
            remSize -= widthInRow
            x = pageX
            y += self._cellHeight
        self._drawCellInfo(pageX + offset % self._pageWidth,
                           pageY + (offset / self._pageWidth) * self._cellHeight,
                           cell, pageType)

    def _drawCellInfo(self, cellX, cellY, cell, pageType):
        style=pysvg.builders.StyleBuilder()
        style.setFontSize(self._cellHeight) #no need for the keywords all the time
        s = ""
        if pageType in (PageType.TABLE_LEAF, PageType.TABLE_INTERIOR) :
            s = str(cell["rid"])
        self._svgDoc.addElement(
            pysvg.text.text(s,
                            x=cellX + (self._cellHeight/2),
                            y=cellY + (self._cellHeight/2),
                            style=style.getStyle()))
