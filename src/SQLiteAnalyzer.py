import __init__
import Config
from DbInfoTemplate import PageType
from array import array

def read_db(dbinfo, dbpath):
    dbdata = _read_db_data(dbpath)

    _read_db_metadata(dbinfo, dbdata)
    _read_db_pages(dbinfo, dbdata)
    _summarize_dbinfo(dbinfo)


def _read_db_data(dbpath):
    # TODO: support big db
    with open(dbpath, "rb") as f_db:
        return f_db.read()


def _read_db_metadata(dbinfo, dbdata):
    hFormat = Config.dbHeaderFormat

    # Correct binstr from dbdata
    db_header_binstr = dbdata[hFormat["offsetInFile"] :
                              hFormat["len"]]
    page_size_binstr = db_header_binstr[hFormat["pageSizeOffset"] :
                                        hFormat["pageSizeOffset"] + hFormat["pageSizeLen"]]
    reserved_space_binstr = db_header_binstr[hFormat["reservedSpaceOffset"] :
                                             hFormat["reservedSpaceOffset"] + hFormat["reservedSpaceLen"]]

    # Set metadata into dbinfo
    dbMdata = dbinfo["dbMetadata"]
    dbMdata["pageSize"] = _binstr2int_bigendian(page_size_binstr)
    dbMdata["nPages"] = len(dbdata) / dbMdata["pageSize"]
    dbMdata["reservedSpace"] = _binstr2int_bigendian(reserved_space_binstr)


def _read_db_pages(dbinfo, dbdata):
    # Read pages
    p_cnt = dbinfo["dbMetadata"]["nPages"]
    for page_num in range(1, p_cnt+1):
        _read_page(dbinfo, dbdata, page_num)


def _read_page(dbinfo, dbdata, page_num):
    """
    @input
    dbinfo: updated by this function

    @example
    _read_page(dbinfo, dbdata, page_num)
    """
    if dbinfo["pages"].has_key(page_num):
        return

    dbMdata = dbinfo["dbMetadata"]
    p_size = dbMdata["pageSize"]
    p_cnt = dbMdata["nPages"]

    page_data = _get_page_data(dbdata, page_num, p_size)
    page_metadata = _check_page_metadata(page_data, page_num)
    page_type = page_metadata["pageType"]

    # Read cells
    cells = []
    if page_type in (PageType.INDEX_LEAF, PageType.INDEX_INTERIOR,
                     PageType.TABLE_LEAF, PageType.TABLE_INTERIOR):
        CPAFormat = Config.cellPointerArrayFormat
        cell_pointer_array_offset = None
        if page_num == 1:
            cell_pointer_array_offset = CPAFormat["offsetInPage1"]
        elif page_type in (PageType.INDEX_LEAF, PageType.TABLE_LEAF):
            cell_pointer_array_offset = CPAFormat["offsetInLeafPage"]
        elif page_type in (PageType.INDEX_INTERIOR, PageType.TABLE_INTERIOR):
            cell_pointer_array_offset = CPAFormat["offsetInInteriorPage"]
        cells = _read_cells(dbdata,
                            page_num,
                            p_size,
                            page_type,
                            cell_pointer_array_offset,
                            page_metadata["cellContentAreaOffset"],
                            page_metadata["nCells"])
        assert len(cells) == page_metadata["nCells"]

    # Add to dbinfo["pages"]
    assert not dbinfo["pages"].has_key(page_num)
    dbinfo["pages"][page_num] = {
        "pageMetadata": page_metadata,
        "cells": cells
    }



def _read_btree_header(btree_header_data):
    """
    @example
    (btree_header_flag,
     free_block_offset,
     n_cells,
     cell_content_area_offset) = _read_btree_header(btree_header_data)
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


def _read_btree_header_flag(btree_header_flag):
    """
    >>> _read_btree_header_flag(0x00) == PageType.OTHER
    True
    >>> _read_btree_header_flag(Config.btreeHeaderFormat['tableInteriorPageFlag']) == PageType.TABLE_INTERIOR
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


def _read_cells(dbdata,
                page_num,
                page_size,
                page_type,
                cell_pointer_array_offset,
                cell_content_area_offset,
                n_cells):
    """
    @return
    Array of cell
    """
    # TODO: Visualizing table interior page is also important for performance analysis
    if page_type in (PageType.TABLE_INTERIOR, PageType.INDEX_INTERIOR):
        return []

    page_data = _get_page_data(dbdata, page_num, page_size)
    CPAFormat = Config.cellPointerArrayFormat
    CPA_offset = cell_pointer_array_offset
    CPA_elem_len = CPAFormat["elemLen"]
    cells = []
    for i, CPA_elem_offset in enumerate( range(CPA_offset,
                                 CPA_offset + CPA_elem_len * n_cells,
                                 CPA_elem_len) ):
        CPA = page_data[CPA_elem_offset : CPA_elem_offset + CPA_elem_len]
        cell_offset = _binstr2int_bigendian(CPA)
        assert cell_offset < len(page_data)

        if page_type == PageType.TABLE_LEAF:
            cell = _read_table_leaf_cell(cell_offset, dbdata, page_num, page_size)
            cells.append(cell)
        elif page_type == PageType.INDEX_LEAF:
            cell = _read_index_leaf_cell(cell_offset, dbdata, page_num, page_size)
            cells.append(cell)
    return cells


def _read_table_leaf_cell(cell_offset, dbdata, page_num, page_size):
    """
    @input
    dbdata, page_num: for overflow page
    """
    page_data = _get_page_data(dbdata, page_num, page_size)

    # Table leaf cell format:
    # [payloadSize (variant), rid (variant), payload, overflowPageNum (4byte)]

    # Payload size
    payload_size_offset = cell_offset
    payload_size_variant = page_data[payload_size_offset :
                                     payload_size_offset + Config.variantFormat["maxLen"]]
    (payload_size_len, payload_size) = _variant2int_bigendian(payload_size_variant)
    # TODO: support overflow page

    # rid
    rid_offset = payload_size_offset + payload_size_len
    rid_variant = page_data[rid_offset :
                            rid_offset + Config.variantFormat["maxLen"]]
    (rid_len, rid) = _variant2int_bigendian(rid_variant)

    return {
        "offset": cell_offset,
        "cellSize": None,  # TODO:
                           # - Get record size and
                           # - Make sure all cells have 4byte overflow page num
        "payloadSize": payload_size,
        "rid": rid,
        "record": None,  # TODO: support it
        "livingBtree": "???"  # TODO: support it
    }


def _read_index_leaf_cell(cell_offset, dbdata, page_num, page_size):
    """
    @input
    dbdata, page_num: for overflow page
    """
    page_data = _get_page_data(dbdata, page_num, page_size)

    # Index leaf cell format:
    # [payloadSize (variant), payload, overflowPageNum (4byte)]

    # Payload size
    payload_size_offset = cell_offset
    payload_size_variant = page_data[payload_size_offset :
                                     payload_size_offset + Config.variantFormat["maxLen"]]
    (payload_size_len, payload_size) = _variant2int_bigendian(payload_size_variant)

    return {
        "offset": cell_offset,
        "cellSize": None,  # TODO:
                           # - Get record size and
                           # - Make sure all cells have 4byte overflow page num
        "payloadSize": payload_size,
        "livingBtree": "???"  # TODO: support it
    }

def _read_overflow_page(dbdata, page_num, rem_len):
    pass


def _check_page_metadata(page_data, page_num):
    """
    @return
    pageMetadata (See DbInfoTemplate.py)

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
    btHFormat = Config.btreeHeaderFormat
    bth_offset = btHFormat["offsetInPage1"] if page_num == 1 else btHFormat["offsetInPage"]
    btree_header_data = page_data[bth_offset :
                                  bth_offset + max(btHFormat["leafLen"], btHFormat["interiorLen"])]
    (btree_header_flag,
     free_block_offset,
     n_cells,
     cell_content_area_offset) = _read_btree_header(btree_header_data)
    page_type = _read_btree_header_flag(btree_header_flag)

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
        page_metadata = {
            "pageType": page_type,
            "nCells": n_cells,
            "freeBlockOffset": free_block_offset,
            "cellContentAreaOffset": cell_content_area_offset,
        }
        return page_metadata
    else:
        page_metadata = {
            "pageType": PageType.UNCERTAIN
        }
        return page_metadata


def _get_page_data(dbdata, page_num, page_size):
    page_offset = page_size * (page_num - 1)
    return dbdata[page_offset : page_offset + page_size]


def _summarize_dbinfo(dbinfo):
    # Check the validity of dbinfo first
    dbMdata = dbinfo["dbMetadata"]
    for k, v in dbMdata.iteritems():
        assert v is not None
    assert len(dbMdata["btrees"]) >= 1  # At least sqlite_master

    pages = dbinfo["pages"]
    assert len(pages) >= 1

    # TODO: set dbinfo["dbMetadata"]["btrees"] just for drawing


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

    >>> s = chr(int('10000001', 2)) + chr(int('00000001', 2))
    >>> _variant2int_bigendian(s)
    (2, 257)
    >>> s = chr(int('10000000', 2)) + chr(int('10000000', 2)) + chr(int('10000000', 2)) +  chr(int('10000000', 2)) +  chr(int('10000000', 2)) +  chr(int('10000000', 2)) +  chr(int('10000000', 2)) +  chr(int('10000000', 2)) +  chr(int('10000000', 2))
    >>> _variant2int_bigendian(s)
    (9, 128L)
    """
    new_binstr = ""
    i = 0
    for i, c in enumerate(binstr):
        byte = ord(c)
        if i == Config.variantFormat["maxLen"] - 1:
            new_binstr += chr(byte)
        else:
            eff7bit = int("01111111", 2) & byte
            new_binstr += chr(eff7bit)
            msb = (byte & int("10000000", 2)) >> 7
            if msb == 0:
                break
    return (i+1, _binstr2int_bigendian(new_binstr))


def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
