import __init__
import Config
from DbInfoTemplate import PageType, get_dbinfo_template
import OutputJson
from array import array


class SQLiteAnalyzer(object):
    """
    @usage
    analyzer = SQLiteAnalyzer('/path/to/db.sqlite')
    analyzer.dumpJson(outPath='/path/to/dbinfo.json')
    """
    def __init__(self, dbpath):
        self._dbpath = dbpath
        self._dbdata = self._get_dbdata()
        self._dbinfo = get_dbinfo_template()
        self._read_db()

    def dumpJson(self,
                 outPath, encoding=Config.main["DbInfoJsonEncoding"]):
        OutputJson.output_dbinfo_json(self._dbinfo,
                                      outPath, encoding)

    def _read_db(self):
        assert len(self._dbdata) > 0
        self._read_db_metadata()
        self._read_db_pages()
        self._summarize_dbinfo()

    def _get_dbdata(self):
        # TODO: support big db
        assert len(self._dbpath) > 0
        with open(self._dbpath, "rb") as f_db:
            return f_db.read()

    def _read_db_metadata(self):
        hFormat = Config.dbHeaderFormat

        # Correct binstr from dbdata
        db_header_binstr = self._dbdata[hFormat["offsetInFile"] :
                                        hFormat["len"]]
        page_size_binstr = db_header_binstr[hFormat["pageSizeOffset"] :
                                            hFormat["pageSizeOffset"] + hFormat["pageSizeLen"]]
        reserved_space_binstr = db_header_binstr[hFormat["reservedSpaceOffset"] :
                                                 hFormat["reservedSpaceOffset"] + hFormat["reservedSpaceLen"]]

        # Set metadata into dbinfo
        dbMdata = self._dbinfo["dbMetadata"]
        dbMdata["pageSize"] = _binstr2int_bigendian(page_size_binstr)
        dbMdata["nPages"] = len(self._dbdata) / dbMdata["pageSize"]
        dbMdata["usablePageSize"] = dbMdata["pageSize"] - _binstr2int_bigendian(reserved_space_binstr)

    def _read_db_pages(self):
        # Read pages
        p_cnt = self._dbinfo["dbMetadata"]["nPages"]
        for pageNum in range(1, p_cnt+1):
            self._read_page(pageNum)

    def _get_page_data(self, pageNum):
        page_size = self._dbinfo["dbMetadata"]["pageSize"]
        page_offset = page_size * (pageNum - 1)
        return self._dbdata[page_offset : page_offset + page_size]

    def _read_page(self, pageNum):
        # Possibly page[pageNum] is already read (ex: overflow page)
        if self._dbinfo["pages"].has_key(pageNum):
            return
        self._dbinfo["pages"][pageNum] = {
            "pageMetadata": {
                "pageType": PageType.UNCERTAIN,
            },
            "cells": []
        }
        this_page = self._dbinfo["pages"][pageNum]

        self._read_page_metadata(pageNum)
        page_metadata = this_page["pageMetadata"]
        page_type = page_metadata["pageType"]

        # Read cells
        if page_type in (PageType.INDEX_LEAF, PageType.INDEX_INTERIOR,
                         PageType.TABLE_LEAF, PageType.TABLE_INTERIOR):
            CPAFormat = Config.cellPointerArrayFormat
            cell_pointer_array_offset = None
            if pageNum == 1:
                cell_pointer_array_offset = CPAFormat["offsetInPage1"]
            elif page_type in (PageType.INDEX_LEAF, PageType.TABLE_LEAF):
                cell_pointer_array_offset = CPAFormat["offsetInLeafPage"]
            elif page_type in (PageType.INDEX_INTERIOR, PageType.TABLE_INTERIOR):
                cell_pointer_array_offset = CPAFormat["offsetInInteriorPage"]

            self._read_cells(pageNum,
                             page_type,
                             page_metadata["nCells"],
                             cell_pointer_array_offset,
                             page_metadata["cellContentAreaOffset"])
            assert len(this_page["cells"]) == page_metadata["nCells"]

    def _read_cells(self, pageNum, page_type, n_cells,
                    cell_pointer_array_offset,
                    cell_content_area_offset):
        this_page = self._dbinfo["pages"][pageNum]
        this_page["cells"] = []

        # TODO: Visualizing table interior page is also important for performance analysis
        if page_type in (PageType.TABLE_INTERIOR, PageType.INDEX_INTERIOR):
            return

        page_data = self._get_page_data(pageNum)
        CPAFormat = Config.cellPointerArrayFormat
        CPA_offset = cell_pointer_array_offset
        CPA_elem_len = CPAFormat["elemLen"]
        for CPA_elem_offset in range(CPA_offset,
                                     CPA_offset + CPA_elem_len * n_cells,
                                     CPA_elem_len):
            CPA = page_data[CPA_elem_offset : CPA_elem_offset + CPA_elem_len]
            cell_offset = _binstr2int_bigendian(CPA)
            assert cell_offset < len(page_data)

            if page_type == PageType.TABLE_LEAF:
                self._read_table_leaf_cell(pageNum, cell_offset)
            elif page_type == PageType.INDEX_LEAF:
                self._read_index_leaf_cell(pageNum, cell_offset)

    def _read_page_metadata(self, pageNum):
        """
        @note
        Sets pageMetadata (See DbInfoTemplate.py)

        @requirement
        At least specify:
        - table leaf page
        - index (interior|leaf) page
        sice only these pages and overflow pages are important
        for this visualization end.
        Overflow pages can be specified not by reading page data
        but by reading cells with overflow pages.

        @methodology
        See: README.org - Specify page types
        """
        this_page = self._dbinfo["pages"][pageNum]

        btHFormat = Config.btreeHeaderFormat
        page_data = self._get_page_data(pageNum)
        bth_offset = btHFormat["offsetInPage1"] if pageNum == 1 else btHFormat["offsetInPage"]
        btree_header_data = page_data[bth_offset :
                                      bth_offset + max(btHFormat["leafLen"], btHFormat["interiorLen"])]
        (btree_header_flag,
         free_block_offset,
         n_cells,
         cell_content_area_offset) = self._get_btree_header(btree_header_data)
        page_type = _btree_header_flag_TO_PageType(btree_header_flag)

        # B-tree leaf page?
        page_size = len(page_data)
        min_cell_len = Config.cellFormat["minCellLen"]
        len_interior = btHFormat["interiorLen"]
        len_leaf = btHFormat["leafLen"]
        if (page_type in (PageType.TABLE_LEAF, PageType.INDEX_LEAF) and
            (len_leaf <= free_block_offset <= page_size or
             free_block_offset == 0) and
            1 <= n_cells <= page_size / min_cell_len and
            (len_leaf <= cell_content_area_offset <= page_size or
             cell_content_area_offset == 0)):
            this_page["pageMetadata"] = {
                "pageType": page_type,
                "nCells": n_cells,
                "freeBlockOffset": free_block_offset,
                "cellContentAreaOffset": cell_content_area_offset,
            }
        else:
            this_page["pageMetadata"] = {
                "pageType": PageType.UNCERTAIN
            }

    def _read_table_leaf_cell(self, pageNum, cell_offset):
        this_page = self._dbinfo["pages"][pageNum]
        page_data = self._get_page_data(pageNum)

        # Table leaf cell format:
        # [payloadSize (variant), rid (variant), payload, overflowPageNum (4byte)]

        # Payload size
        payloadSizeOffset = cell_offset
        payloadSizeVariant = page_data[payloadSizeOffset :
                                       payloadSizeOffset + Config.variantFormat["maxLen"]]
        (payloadSizeLen, payloadSize) = _variant2int_bigendian(payloadSizeVariant)

        # rid
        rid_offset = payloadSizeOffset + payloadSizeLen
        rid_variant = page_data[rid_offset :
                                rid_offset + Config.variantFormat["maxLen"]]
        (rid_len, rid) = _variant2int_bigendian(rid_variant)

        # payload
        payloadOffset = rid_offset + rid_len
        (headerSize, bodySize) = self._get_whole_payload_size_for_cell(pageNum, payloadOffset)
        payloadWholeSize = headerSize + bodySize
        localPayloadSize = self._get_local_payload_size_for_cell(payloadWholeSize)
        assert payloadSize == payloadWholeSize

        # Might-be overflow page head
        overflowPageNumLen = Config.cellFormat["overflowPageNumLen"]
        ovflw_pg_head_offset = payloadOffset + localPayloadSize
        ovflw_pg_head_binstr = page_data[ovflw_pg_head_offset :
                                         ovflw_pg_head_offset + overflowPageNumLen]
        ovflw_pg_head = _binstr2int_bigendian(ovflw_pg_head_binstr)

        # Read overflow page if necessary
        if localPayloadSize < payloadSize:
            self._read_overflow_pages(ovflw_pg_head, payloadSize - localPayloadSize)
        else:
            overflowPageNumLen = 0

        this_page["cells"].append({
            "offset": cell_offset,
            "cellSize":
                payloadSizeLen + rid_len + localPayloadSize + overflowPageNumLen,
            "payloadSize": payloadSize,
            "rid": rid,
            "payload":  # TODO: fully support it
                {"headerSize": headerSize, "bodySize": bodySize},
            "livingBtree": "???"  # TODO: support it
        })

    def _read_index_leaf_cell(self, pageNum, cell_offset):
        this_page = self._dbinfo["pages"][pageNum]
        page_data = self._get_page_data(pageNum)

        # Index leaf cell format:
        # [payloadSize (variant), payload, overflowPageNum (4byte)]

        # Payload size
        payloadSizeOffset = cell_offset
        payloadSizeVariant = page_data[payloadSizeOffset :
                                       payloadSizeOffset + Config.variantFormat["maxLen"]]
        (payloadSizeLen, payloadSize) = _variant2int_bigendian(payloadSizeVariant)

        # payload
        payloadOffset = payloadSizeOffset + payloadSizeLen
        (headerSize, bodySize) = self._get_whole_payload_size_for_cell(pageNum, payloadOffset)
        payloadWholeSize = headerSize + bodySize
        localPayloadSize = self._get_local_payload_size_for_cell(payloadWholeSize)
        assert payloadSize == payloadWholeSize

        # Might-be overflow page head
        overflowPageNumLen = Config.cellFormat["overflowPageNumLen"]
        ovflw_pg_head_offset = payloadOffset + localPayloadSize
        ovflw_pg_head_binstr = page_data[ovflw_pg_head_offset :
                                         ovflw_pg_head_offset + overflowPageNumLen]
        ovflw_pg_head = _binstr2int_bigendian(ovflw_pg_head_binstr)

        # Read overflow page if necessary
        if localPayloadSize < payloadSize:
            self._read_overflow_pages(ovflw_pg_head, payloadSize - localPayloadSize)
        else:
            overflowPageNumLen = 0

        this_page["cells"].append({
            "offset": cell_offset,
            "cellSize":
                payloadSizeLen + localPayloadSize + overflowPageNumLen,
            "payloadSize": payloadSize,
            "payload":  # TODO: fully support it
                {"headerSize": headerSize, "bodySize": bodySize},
            "livingBtree": "???"  # TODO: support it
        })

    def _get_btree_header(self, btree_header_data):
        """
        @example
        (btree_header_flag,
        free_block_offset,
        n_cells,
        cell_content_area_offset) = self._get_btree_header(btree_header_data)
        """
        btHFormat = Config.btreeHeaderFormat
        bth_data = btree_header_data
        btree_header_flag = _binstr2int_bigendian(
            bth_data[btHFormat["btreeFlagOffset"] :
                     btHFormat["btreeFlagOffset"] + btHFormat["btreeFlagLen"]])
        free_block_offset = _binstr2int_bigendian(
            bth_data[btHFormat["freeBlockOffset"] :
                     btHFormat["freeBlockOffset"] + btHFormat["freeBlockLen"]])
        n_cells = _binstr2int_bigendian(
            bth_data[btHFormat["nCellsOffset"] :
                     btHFormat["nCellsOffset"] + btHFormat["nCellsLen"]])
        cell_content_area = _binstr2int_bigendian(
            bth_data[btHFormat["cellContentAreaOffset"] :
                     btHFormat["cellContentAreaOffset"] + btHFormat["cellContentAreaLen"]])
        return (btree_header_flag, free_block_offset, n_cells, cell_content_area)

    def _get_local_payload_size_for_cell(self, payloadWholeSize):
        """
        @note
        See: README.org - Trac overflow pages

        @return
        Local payload size for this cell.

        @example
        payloadLocalSize = self._get_local_payload_size_for_cell(cell_offset, payloadWholeSize)
        if payloadLocalSize < payloadWholeSize:
            # This cell has overflow pages
            self._read_overflow_pages(overflowPageHead, payloadWholeSize - payloadLocalSize)
        """
        payloadSize = payloadWholeSize
        usableSize = self._dbinfo["dbMetadata"]["usablePageSize"]
        maxLocal = usableSize - 35
        minLocal = ((usableSize - 12) * 32/255) - 23
        if payloadSize <= maxLocal:
            return payloadSize
        localSize = minLocal + ((payloadSize - minLocal) % (usableSize - 4))
        sizeInThisPage = minLocal if localSize > maxLocal else localSize
        return sizeInThisPage

    def _get_whole_payload_size_for_cell(self, pageNum, payloadOffset):
        """
        @note
        See: README.org - Read payloads

        @return
        (payloadHeaderSize, payloadBodySize)
        """
        page_data = self._get_page_data(pageNum)
        payloadData = page_data[payloadOffset : ]

        payloadFormat = Config.payloadFormat
        variantMaxLen = Config.variantFormat["maxLen"]

        # Read header size
        headerSizeVariant = payloadData[payloadFormat["headerSizeOffset"] :
                                        payloadFormat["headerSizeOffset"] + variantMaxLen]
        (headerSizeLen, headerSize) = _variant2int_bigendian(headerSizeVariant)

        # Read serial type in header and calculate bodySize
        bodySize = 0
        stypeOffset = headerSizeLen
        while stypeOffset < headerSize:
            stypeVariant = payloadData[stypeOffset :
                                       stypeOffset + variantMaxLen]
            (stypeLen, stype) = _variant2int_bigendian(stypeVariant)
            bodySize += Config.serialType2ContentSize(stype)
            stypeOffset += stypeLen

        return headerSize, bodySize

    def _read_overflow_pages(self, pageNum, rem_len):
        assert 1 <= pageNum <= self._dbinfo["dbMetadata"]["nPages"]

        # Read for the first time
        if not self._dbinfo["pages"].has_key(pageNum):
            self._dbinfo["pages"][pageNum] = {
                "pageMetadata": {
                    "pageType": PageType.OVERFLOW,
                    "nCells": 1,
                },
                "cells": []
            }
        thisPage = self._dbinfo["pages"][pageNum]

        page_data = self._get_page_data(pageNum)

        # Read next overflow page num
        ovflwPgFormat = Config.overflowPageFormat
        next_ovflw_pg_binstr = page_data[ovflwPgFormat["nextOverflowPageOffset"] :
                                         ovflwPgFormat["nextOverflowPageOffset"] + ovflwPgFormat["nextOverflowPageLen"]]
        next_ovflw_pg = _binstr2int_bigendian(next_ovflw_pg_binstr)
        assert 0 <= next_ovflw_pg <= self._dbinfo["dbMetadata"]["nPages"]
        thisPage["pageMetadata"]["nextOverflowPageNum"] = next_ovflw_pg

        cell_size = None
        cell_area_len = self._dbinfo["dbMetadata"]["usablePageSize"] - ovflwPgFormat["nextOverflowPageLen"]

        # This page is the last overflow page
        if next_ovflw_pg == ovflwPgFormat["pageNumForFinal"]:
            assert rem_len <= cell_area_len
            cell_size = rem_len
        # Other overflow pages follow
        else:
            cell_size = cell_area_len
            self._read_overflow_pages(next_ovflw_pg, rem_len - cell_size)

        thisPage["cells"].append({
            "offset": ovflwPgFormat["nextOverflowPageOffset"] + ovflwPgFormat["nextOverflowPageLen"],
            "cellSize": cell_size,
            # TODO: parameters to specify what (record|index) (in btree) this overflow page belongs to
            #   ex: RID, index key, livingBtree
        })

    def _summarize_dbinfo(self):
        # Check the validity of dbinfo first
        dbMdata = self._dbinfo["dbMetadata"]
        for k, v in dbMdata.iteritems():
            assert v is not None
            assert len(dbMdata["btrees"]) >= 1  # At least sqlite_master

            pages = self._dbinfo["pages"]
            assert len(pages) >= 1

        # TODO: set dbinfo["dbMetadata"]["btrees"] just for drawing


def _btree_header_flag_TO_PageType(btree_header_flag):
    """
    >>> _btree_header_flag_TO_PageType(0x00) == PageType.UNCERTAIN
    True
    >>> _btree_header_flag_TO_PageType(Config.btreeHeaderFormat['tableInteriorPageFlag']) == PageType.TABLE_INTERIOR
    True
    """
    btHFormat = Config.btreeHeaderFormat
    d = {
        btHFormat["indexInteriorPageFlag"]: PageType.INDEX_INTERIOR,
        btHFormat["indexLeafPageFlag"]: PageType.INDEX_LEAF,
        btHFormat["tableInteriorPageFlag"]: PageType.TABLE_INTERIOR,
        btHFormat["tableLeafPageFlag"]: PageType.TABLE_LEAF,
    }
    if not d.has_key(btree_header_flag):
        return PageType.UNCERTAIN
    return d[btree_header_flag]


def _print_intlist_in_hex(intlist):
    print [hex(i) for i in intlist]


def _binstr2int_bigendian(binstr):
    """
    >>> s = chr(int('00000001', 2)) + chr(int('00000001', 2))
    >>> _binstr2int_bigendian(s)
    257
    """
    ret = 0
    rev_byte_list = reversed(binstr)
    for n_dig, byte in enumerate(rev_byte_list):
        ret += ord(byte) * pow(256, n_dig)
    return ret


def _variant2int_bigendian(binstr):
    """
    @note
    See variant format (very simple):
    http://forensicsfromthesausagefactory.blogspot.jp/2011/05/analysis-of-record-structure-within.html

    @return
    (VariantLength, effNumber)

    >>> s = chr(int('10000001', 2)) + chr(int('00101001', 2))
    >>> _variant2int_bigendian(s)
    (2, 169)
    >>> s = chr(int('10000001', 2)) + chr(int('00000001', 2))
    >>> _variant2int_bigendian(s)
    (2, 129)
    >>> s = chr(int('10000000', 2)) + chr(int('10000000', 2)) + chr(int('10000000', 2)) +  chr(int('10000000', 2)) +  chr(int('10000000', 2)) +  chr(int('10000000', 2)) +  chr(int('10000000', 2)) +  chr(int('10000000', 2)) +  chr(int('10000000', 2))
    >>> _variant2int_bigendian(s)
    (9, 128)
    """
    s01 = ""
    i = 0
    for i, c in enumerate(binstr):
        byte = ord(c)
        if i == Config.variantFormat["maxLen"] - 1:
            s01 += "%08s" % (bin(byte)[2:])
        else:
            eff7bit = int("01111111", 2) & byte
            s01 += "%07s" % (bin(eff7bit)[2:])
            msb = (byte & int("10000000", 2)) >> 7
            if msb == 0:
                break
    s01 = s01.replace(' ', '0')
    return (i+1, int(s01, 2))


def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
