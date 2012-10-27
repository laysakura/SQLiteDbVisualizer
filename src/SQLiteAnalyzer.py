import __init__
import Config
from DbInfoTemplate import PageType
from array import array

def read_db(dbinfo, dbpath):
    dbdata = _read_db_data(dbpath)

    _read_db_metadata(dbinfo, dbdata)
    print(dbinfo)

    _read_db_pages(dbinfo, dbdata)
    print(dbinfo)

    _summarize_dbinfo(dbinfo)
    print(dbinfo)


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
    dbHFormat = Config.dbHeaderFormat
    btHFormat = Config.btreeHeaderFormat
    CPAFormat = Config.cellPointerArrayFormat

    dbMdata = dbinfo["dbMetadata"]
    p_size = dbMdata["pageSize"]
    p_cnt = dbMdata["nPages"]
    pages = dbinfo["pages"]

    # Read page#1
    pages.append({
      "pageType": PageType.FIRST_PAGE,
      "cells": []
    })


    print("nCellsOffset: " + str(btHFormat["nCellsOffset"]) )

    # Read following pages
    for page_offset in range(p_size, p_size * p_cnt, p_size):
        page_data = dbdata[page_offset : page_offset + p_size]

        # B-tree header info
        btree_header = page_data[btHFormat["offsetInPage"] :
                                 btHFormat["offsetInPage"] + btHFormat["len"]]
        btree_header_flag = _binstr2int_bigendian(
            btree_header[btHFormat["btreeFlagOffset"] :
                         btHFormat["btreeFlagOffset"] + btHFormat["btreeFlagLen"]])
        n_cells = _binstr2int_bigendian(
            btree_header[btHFormat["nCellsOffset"] :
                         btHFormat["nCellsOffset"] + btHFormat["nCellsLen"]])
        cell_content_area = _binstr2int_bigendian(
            btree_header[btHFormat["cellContentAreaOffset"] :
                         btHFormat["cellContentAreaOffset"] + btHFormat["cellContentAreaLen"]])

        # B-tree flag
        if btree_header_flag == btHFormat["indexInternalPageFlag"]:
            pages.append({
              "pageType": PageType.INDEX_INTERNAL,
              "cells": []
            })
        elif btree_header_flag == btHFormat["indexLeafPageFlag"]:
            pages.append({
              "pageType": PageType.INDEX_LEAF,
              "cells": []
            })
        elif btree_header_flag == btHFormat["tableInternalPageFlag"]:
            pages.append({
              "pageType": PageType.TABLE_INTERNAL,
              "cells": []
            })
        elif btree_header_flag == btHFormat["tableLeafPageFlag"]:
            pages.append({
              "pageType": PageType.TABLE_LEAF,
              "cells": []
            })

        # Read cells
        CPA_offset = CPAFormat["offsetInPage"]
        CPA_elem_len = CPAFormat["elemLen"]
        for CPA_elem_offset in range(CPA_offset, CPA_elem_len * n_cells, CPA_elem_len):
            CPA = page_data[CPA_elem_offset : CPA_elem_offset + CPA_elem_len]
            cell_offset = _binstr2int_bigendian(CPA)
            assert cell_offset < p_size

            cell_len_variant = page_data[cell_offset : cell_offset + Config.variantFormat["maxLen"]]
            (n_digit, cell_len) = _variant2int_bigendian(cell_len_variant)

            pages[len(pages)-1]["cells"].append({
              "offset": cell_offset,
              "size": cell_len,
              "livingBtree": "???"
            })


def _summarize_dbinfo(dbinfo):
    # Check the validity of dbinfo first
    dbMdata = dbinfo["dbMetadata"]
    assert dbMdata["pageSize"] > 0
    assert dbMdata["nPages"] > 0
    pages = dbinfo["pages"]
    assert len(pages) > 0
    assert pages[0]["pageType"] == PageType.FIRST_PAGE

    # set dbinfo["dbMetadata"]["btrees"] just for drawin


def _print_intlist_in_hex(intlist):
    print [hex(i) for i in intlist]


def _binstr2int_bigendian(binstr):
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
