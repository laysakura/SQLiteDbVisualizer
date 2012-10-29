import SvgConfig
import DbFormatConfig
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
        # self._svgDoc.addElement(pysvg.text.text("Hello World",
        #                                         x = 210, y = 110))

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
        self._svgDoc.addElement(
            self._shapeBuilder.createRect(x, y,
                                          self._pageWidth, self._pageHeight,
                                          fill=SvgConfig.page["fillColor"]))
        self._drawCells(x, y, pageNum)

    def _drawCells(self, pageX, pageY, pageNum):
        cells = self._dbinfo["pages"][str(pageNum)]["cells"]
        for cell in cells:
            self._drawCell(pageX, pageY, cell)

    def _drawCell(self, pageX, pageY, cell):
        offset = cell["offset"]
        size = remSize = cell["cellSize"]
        x = pageX + offset % self._pageWidth
        y = pageY + (offset / self._pageWidth) * self._cellHeight
        while remSize > 0:
            widthInRow = self._pageWidth - x
            self._svgDoc.addElement(
                self._shapeBuilder.createRect(
                    x, y,
                    widthInRow, self._cellHeight,
                    fill=SvgConfig.cell["fillColor"]))
            remSize -= widthInRow
            x = pageX
            y += self._cellHeight
