import SvgConfig
import DbFormatConfig
import DbInfoTemplate
from DbInfoTemplate import PageType
import json
import pysvg.structure
import pysvg.builders
import pysvg.text


class Json2Svg(object):
    def initByJsonStr(self, jsonStr, svgPath,
                      jsonEncoding=DbFormatConfig.main["dbInfoJsonEncoding"],
                      filterBtrees=[],
                      displayRid=False,
                      displayFreelistPages=True,
                      longshot=False):
        self._dbinfo = json.loads(jsonStr, jsonEncoding)
        self._svgPath = svgPath
        self._filterBtrees = filterBtrees
        self._displayRid = displayRid
        self._displayFreelistPages = displayFreelistPages
        self._longshot = longshot
        self._initCommons()

    def initByJsonPath(self, jsonPath, svgPath,
                       jsonEncoding=DbFormatConfig.main["dbInfoJsonEncoding"],
                       filterBtrees=[],
                       displayRid=False,
                       displayFreelistPages=True,
                       longshot=False):
        with open(jsonPath) as f_json:
            self._dbinfo = json.load(f_json, jsonEncoding)
        self._svgPath = svgPath
        self._filterBtrees = filterBtrees
        self._displayRid = displayRid
        self._displayFreelistPages = displayFreelistPages
        self._longshot = longshot
        self._initCommons()

    def _initCommons(self):
        assert not (self._displayRid and self._longshot)
        btreeList = self._dbinfo["dbMetadata"]["btrees"]

        if len(self._filterBtrees) > 0:
            self._filteredBtreeList = [
                btree for btree in btreeList
                if btree["name"] in self._filterBtrees]
        else:
            self._filteredBtreeList = btreeList

    def dumpSvg(self):
        self._preDraw()
        self._draw()
        self._postDraw()

    def _preDraw(self):
        self._prepPysvgObj()
        if self._longshot:
            self._setDrawParamLongshot()
        else:
            self._setDrawParam()
        self._setBtreeColorDict()

    def _draw(self):
        if self._longshot:
            self._drawBtreeList(SvgConfig.btreeList["x"],
                                SvgConfig.btreeList["y"])
            self._drawPageListLongshot(SvgConfig.pageList["x"],
                                       self._pageListY)
        else:
            self._drawBtreeList(SvgConfig.btreeList["x"],
                                SvgConfig.btreeList["y"])
            self._drawPageList(SvgConfig.pageList["x"],
                               self._pageListY)

    def _postDraw(self):
        self._svgDoc.save(
            self._svgPath,
            encoding=SvgConfig.main["encoding"])

    def _prepPysvgObj(self):
        self._svgDoc = pysvg.structure.Svg()
        self._shapeBuilder = pysvg.builders.ShapeBuilder()

    def _setDrawParam(self):
        # BtreeList
        self._btreeLegendHeight = SvgConfig.btreeList["legendHeight"]
        self._btreeLegendNCol = SvgConfig.btreeList["legendNCol"]
        self._nBtree = len(self._filteredBtreeList)
        self._btreeLegendNRow = self._nBtree / self._btreeLegendNCol + 1
        self._btreeListWidth = SvgConfig.page["width"]
        self._btreeListHeight = self._btreeLegendHeight * self._btreeLegendNRow
        self._btreeLegendWidth = self._btreeListWidth / self._btreeLegendNCol

        # PageList
        self._pageWidth = SvgConfig.page["width"]
        self._pageListWidth = (SvgConfig.page["width"] +
                               SvgConfig.pageList["pageNumWidth"])
        self._cellHeight = SvgConfig.cell["height"]
        self._nRowsInPage = (self._dbinfo["dbMetadata"]["pageSize"] /
                             self._pageWidth)
        self._pageHeight = self._cellHeight * self._nRowsInPage
        self._pageListY = SvgConfig.btreeList["y"] + self._btreeListHeight
        self._pageListHeight = (self._pageHeight *
                                self._dbinfo["dbMetadata"]["nPages"])

    def _setDrawParamLongshot(self):
        # BtreeList
        self._btreeLegendHeight = SvgConfig.btreeList["legendHeight"]
        self._btreeLegendNCol = SvgConfig.btreeList["legendNCol"]
        self._nBtree = len(self._filteredBtreeList)
        self._btreeLegendNRow = self._nBtree / self._btreeLegendNCol + 1
        self._btreeListWidth = (SvgConfig.pageListLongshot["nCols"] *
                                SvgConfig.pageLongshot["size"])
        self._btreeListHeight = self._btreeLegendHeight * self._btreeLegendNRow
        self._btreeLegendWidth = self._btreeListWidth / self._btreeLegendNCol

        # PageList
        self._pageListY = SvgConfig.btreeList["y"] + self._btreeListHeight

    def _setBtreeColorDict(self):
        self._btreeColorDict = {}
        for i, btree in enumerate(self._filteredBtreeList):
            colorPalette = SvgConfig.btreeColorPalette
            self._btreeColorDict[btree["name"]] = colorPalette[
                i % len(colorPalette)]

    def _isFilteredBtreePage(self, pageNum):
        pageMetadata = self._dbinfo["pages"][str(pageNum)]["pageMetadata"]
        isBtreePage = (pageMetadata["pageType"] in (
                           PageType.INDEX_LEAF, PageType.INDEX_INTERIOR,
                           PageType.TABLE_LEAF, PageType.TABLE_INTERIOR))
        isFiltered = (self._filterBtrees == [] or
                      (self._filterBtrees != [] and
                       pageMetadata["livingBtree"] in self._filterBtrees))
        return isBtreePage & isFiltered

    def _isFreelistPageToDisplay(self, pageNum):
        pageMetadata = self._dbinfo["pages"][str(pageNum)]["pageMetadata"]
        return (
            self._displayFreelistPages == True and
            pageMetadata["pageType"] in (
                PageType.FREELIST_TRUNK, PageType.FREELIST_LEAF,
                PageType.FREELIST_MAP)
        )

    def _drawPageList(self, x, y):
        nDrawnPage = 0
        for pageNum in range(1, self._dbinfo["dbMetadata"]["nPages"] + 1):
            # Filter pages to draw
            if (self._isFilteredBtreePage(pageNum) or
                self._isFreelistPageToDisplay(pageNum)):
                self._drawPage(
                    x,
                    y + nDrawnPage * self._pageHeight,
                    pageNum)
                self._drawPageNum(
                    x + SvgConfig.page["width"],
                    y + nDrawnPage * self._pageHeight,
                    pageNum)
                nDrawnPage += 1

    def _drawPageListLongshot(self, x, y):
        offsetX = 0
        offsetY = 0
        for pageNum in range(1, self._dbinfo["dbMetadata"]["nPages"] + 1):
            pageMetadata = self._dbinfo["pages"][str(pageNum)]["pageMetadata"]
            pageType = pageMetadata["pageType"]

            # color
            fillColor = SvgConfig.pageLongshot["defaultColor"]
            if self._isFilteredBtreePage(pageNum):
                fillColor = self._btreeColorDict[pageMetadata["livingBtree"]]
            elif self._isFreelistPageToDisplay(pageNum):
                page = self._dbinfo["pages"][str(pageNum)]
                pageMetadata = page["pageMetadata"]
                if pageMetadata["pageType"] in (
                    PageType.FREELIST_TRUNK, PageType.FREELIST_LEAF):
                    btreeName = DbInfoTemplate.pgnoRoot2btreeName(
                        self._dbinfo,
                        pageMetadata["pgnoRoot"])
                    if btreeName is not None:
                        fillColor = self._btreeColorDict[btreeName]

            # offset
            pageSize = SvgConfig.pageLongshot["size"]
            nCols = SvgConfig.pageListLongshot["nCols"]
            offsetX = pageSize * ((pageNum - 1) % nCols)
            offsetY = pageSize * ((pageNum - 1) / nCols)

            self._svgDoc.addElement(
                self._shapeBuilder.createRect(
                    x + offsetX, y + offsetY,
                    SvgConfig.btreeList["legendHeight"] - 1,
                    SvgConfig.btreeList["legendHeight"] - 1,
                    fill=fillColor,
                    strokewidth=SvgConfig.pageLongshot["strokeWidth"],
                    stroke=SvgConfig.page[pageType + "strokeColor"]))

    def _drawBtreeList(self, x, y):
        for i, btree in enumerate(self._filteredBtreeList):
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
            pysvg.text.Text(btree["name"].encode(SvgConfig.main["encoding"]),
                            x=x + SvgConfig.btreeList["legendHeight"],
                            y=y + SvgConfig.btreeList["legendTopMargin"],
                            style=style.getStyle()))

    def _drawPage(self, x, y, pageNum):
        page = self._dbinfo["pages"][str(pageNum)]
        pageType = page["pageMetadata"]["pageType"]
        self._svgDoc.addElement(
            self._shapeBuilder.createRect(
                x, y,
                self._pageWidth, self._pageHeight,
                fill=SvgConfig.page["fillColor"],
                strokewidth=SvgConfig.page["strokeWidth"],
                stroke=SvgConfig.page[pageType + "strokeColor"]))

        # Draw inside of pages
        if pageType in (
            PageType.INDEX_LEAF, PageType.INDEX_INTERIOR,
            PageType.TABLE_LEAF, PageType.TABLE_INTERIOR,
            PageType.OVERFLOW):
            self._drawCells(x, y, pageNum)
        elif pageType == PageType.FREELIST_TRUNK:
            # TODO: Draw freelist trunk page contents
            pass

    def _drawPageNum(self, x, y, pageNum):
        style = pysvg.builders.StyleBuilder()
        style.setFontSize(SvgConfig.pageList["pageNumFontSize"])
        self._svgDoc.addElement(
            pysvg.text.Text(str(pageNum),
                            x=x + SvgConfig.pageList["pageNumLeftMargin"],
                            y=y + SvgConfig.pageList["pageNumTopMargin"],
                            style=style.getStyle()))

    def _drawCells(self, pageX, pageY, pageNum):
        page = self._dbinfo["pages"][str(pageNum)]
        pageType = page["pageMetadata"]["pageType"]
        # TODO: Give livingBtree for overflow page
        cellColor = "#cccccc"
        if pageType in (PageType.TABLE_LEAF, PageType.TABLE_INTERIOR,
                        PageType.INDEX_LEAF, PageType.INDEX_INTERIOR):
            livingBtree = page["pageMetadata"]["livingBtree"]
            cellColor = self._btreeColorDict[livingBtree]
        cells = page["cells"]
        for cell in cells:
            self._drawCell(pageX, pageY,
                           cellColor,
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
        self._drawCellInfo(
            pageX + offset % self._pageWidth,
            pageY + (offset / self._pageWidth) * self._cellHeight,
            cell, pageType)

    def _drawCellInfo(self, cellX, cellY, cell, pageType):
        if (self._displayRid and
            pageType in (PageType.TABLE_LEAF, PageType.TABLE_INTERIOR)):
            self._drawRid(cellX, cellY, cell["rid"], pageType)

    def _drawRid(self, x, y, rid, pageType):
        style = pysvg.builders.StyleBuilder()
        style.setFontSize(SvgConfig.cell["ridFontSize"])
        s = str(rid)
        self._svgDoc.addElement(
            pysvg.text.Text(
                s,
                x=x + (self._cellHeight / 2),
                y=y + (self._cellHeight / 2),
                style=style.getStyle()))
