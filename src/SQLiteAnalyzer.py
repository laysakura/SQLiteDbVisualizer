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

    # Set metadata into dbinfo
    dbMdata = dbinfo["dbMetadata"]
    dbMdata["pageSize"] = _binstr2int_bigendian(page_size_binstr)
    dbMdata["nPages"] = len(dbdata) / dbMdata["pageSize"]


def _read_db_pages(dbinfo, dbdata):
    dbMdata = dbinfo["dbMetadata"]
    p_size = dbMdata["pageSize"]
    p_cnt = dbMdata["nPages"]

    # Read page#1
    page_data = dbdata[0 : p_size]
    page_info = _read_page(page_data, first_page=True)
    dbinfo["pages"].append(page_info)

    # Read following pages
    for page_offset in range(p_size, p_size * p_cnt, p_size):
        page_data = dbdata[page_offset : page_offset + p_size]
        page_info = _read_page(page_data)
        dbinfo["pages"].append(page_info)


def _read_page(page_data, first_page=False):
    """
    @example
    page_info = _read_page(page_data)
    dbinfo['pages'].append(page_info)
    """
    # B-tree header info
    btHFormat = Config.btreeHeaderFormat
    bth_offset = btHFormat["offsetInPage1"] if first_page else btHFormat["offsetInPage"]
    btree_header_data = page_data[bth_offset :
                                  bth_offset + btHFormat["len"]]
    (btree_header_flag,
     n_cells,
     cell_content_area_offset) = _read_btree_header(btree_header_data)
    page_type = _read_btree_header_flag(btree_header_flag)

    # Read cells
    CPAFormat = Config.cellPointerArrayFormat
    cells = _read_cells(page_data,
                        CPAFormat["offsetInPage1"] if first_page else CPAFormat["offsetInPage"],
                        cell_content_area_offset,
                        n_cells)
    assert len(cells) == n_cells

    # Return page_info
    page_info = {
        "pageType": page_type,
        "cells": cells
    }
    return page_info



def _read_btree_header(btree_header_data):
    """
    @example
    (btree_header_flag,
     n_cells,
     cell_content_area_offset) = _read_btree_header(btree_header_data)
    """
    btHFormat = Config.btreeHeaderFormat
    bth_data = btree_header_data
    btree_header_flag = _binstr2int_bigendian(
        bth_data[btHFormat["btreeFlagOffset"] :
                 btHFormat["btreeFlagOffset"] + btHFormat["btreeFlagLen"]])
    n_cells = _binstr2int_bigendian(
        bth_data[btHFormat["nCellsOffset"] :
                 btHFormat["nCellsOffset"] + btHFormat["nCellsLen"]])
    cell_content_area = _binstr2int_bigendian(
        bth_data[btHFormat["cellContentAreaOffset"] :
                 btHFormat["cellContentAreaOffset"] + btHFormat["cellContentAreaLen"]])
    return (btree_header_flag, n_cells, cell_content_area)


def _read_btree_header_flag(btree_header_flag):
    """
    >>> _read_btree_header_flag(0x00) == PageType.OTHER
    True
    >>> _read_btree_header_flag(Config.btreeHeaderFormat['tableInternalPageFlag']) == PageType.TABLE_INTERNAL
    True
    """
    btHFormat = Config.btreeHeaderFormat
    d = {
        btHFormat["indexInternalPageFlag"]: PageType.INDEX_INTERNAL,
        btHFormat["indexLeafPageFlag"]: PageType.INDEX_LEAF,
        btHFormat["tableInternalPageFlag"]: PageType.TABLE_INTERNAL,
        btHFormat["tableLeafPageFlag"]: PageType.TABLE_LEAF,
    }
    if not d.has_key(btree_header_flag):
        return PageType.OTHER
    return d[btree_header_flag]


def _read_cells(page_data,
                cell_pointer_array_offset,
                cell_content_area_offset,
                n_cells):
    CPAFormat = Config.cellPointerArrayFormat
    CPA_offset = cell_pointer_array_offset
    CPA_elem_len = CPAFormat["elemLen"]
    cells = []
    for CPA_elem_offset in range(CPA_offset,
                                 CPA_offset + CPA_elem_len * n_cells,
                                 CPA_elem_len):
        CPA = page_data[CPA_elem_offset : CPA_elem_offset + CPA_elem_len]
        cell_offset = _binstr2int_bigendian(CPA)
        assert cell_offset < len(page_data)

        cell_len_variant = page_data[cell_offset : cell_offset + Config.variantFormat["maxLen"]]
        (n_digit, cell_len) = _variant2int_bigendian(cell_len_variant)

        cells.append({
            "offset": cell_offset,
            "size": cell_len,
            "livingBtree": "???"
        })
    return cells


def _summarize_dbinfo(dbinfo):
    # Check the validity of dbinfo first
    dbMdata = dbinfo["dbMetadata"]
    assert dbMdata["pageSize"] > 0
    assert dbMdata["nPages"] > 0
    pages = dbinfo["pages"]
    assert len(pages) > 0

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
