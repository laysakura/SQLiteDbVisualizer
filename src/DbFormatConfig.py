import __init__

basedir = __init__.basedir

main = {
    "dbInfoJsonPath": basedir + "/output.json",
    "dbInfoJsonEncoding": "utf-8",
}

dbHeaderFormat = {
    "offsetInFile": 0,
    "len": 100,
    "pageSizeOffset": 16,
    "pageSizeLen": 2,
    "reservedSpaceOffset": 20,
    "reservedSpaceLen": 1,
}

btreeHeaderFormat = {
    # Page#1 has special format
    "offsetInPage1": dbHeaderFormat["offsetInFile"] + dbHeaderFormat["len"],
    "offsetInPage": 0,

    "leafLen": 8,
    "interiorLen": 12,  # leafLen + len(right most child page num)

    "btreeFlagOffset": 0,
    "btreeFlagLen": 1,
    "freeBlockOffset": 1,
    "freeBlockLen": 2,
    "nCellsOffset": 3,
    "nCellsLen": 2,
    "cellContentAreaOffset": 5,
    "cellContentAreaLen": 2,
    "rightmostChildPageNumOffset": 8,
    "rightmostChildPageNumLen": 4,

    "indexInteriorPageFlag": 0x02,
    "indexLeafPageFlag": 0x0A,
    "tableInteriorPageFlag": 0x05,
    "tableLeafPageFlag": 0x0D,

    "firstPageLivingBtreeStr": "sqlite_master",
    "uncertainLivingBtreeStr": "????",
}

sqlite_master = {
    "tableName": "sqlite_master",
}

cellPointerArrayFormat = {
    "offsetInPage1": btreeHeaderFormat["offsetInPage1"] + btreeHeaderFormat["leafLen"],
    "offsetInLeafPage": btreeHeaderFormat["offsetInPage"] + btreeHeaderFormat["leafLen"],
    "offsetInInteriorPage": btreeHeaderFormat["offsetInPage"] + btreeHeaderFormat["interiorLen"],

    "elemLen": 2,
}

cellFormat = {
    # See "Extracting SQLite records - DFRWS"
    # Payload is:
    # - For table btree leaf: content (record)
    # - For table btree interior: none
    # - For index btree {leaf,interior}: key
    "minCellLen": 5,

    "overflowPageNumLen": 4,
    "leftChildPageNumLen": 4,
}

payloadFormat = {
    "headerSizeOffset": 0,
}

overflowPageFormat = {
    "nextOverflowPageOffset": 0,
    "nextOverflowPageLen": 4,

    "pageNumForFinal": 0x00,
}

varintFormat = {
    "maxLen": 9,
}


def serialType2ContentSize(stype):
    """
    @note
    See: http://www.sqlite.org/fileformat2.html - Serial Type Codes Of The Record Format
    """
    assert stype not in (10, 11)
    if stype in range(0, 4+1):
        return stype
    elif stype in (5, 7):
        return stype + 1
    elif stype == 6:
        return 8
    elif stype in (8, 9):
        return 0
    elif stype >= 12 and stype % 2 == 0:
        return (stype - 12) / 2
    elif stype >= 13 and stype % 2 == 1:
        return (stype - 13) / 2
    else:
        assert False
