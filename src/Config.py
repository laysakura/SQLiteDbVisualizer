import __init__

basedir = __init__.basedir

main = {
    "DbInfoJsonPath": basedir + "/output.json",
    "DbInfoJsonEncoding": "utf-8",
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

    "indexInteriorPageFlag": 0x02,
    "indexLeafPageFlag": 0x0A,
    "tableInteriorPageFlag": 0x05,
    "tableLeafPageFlag": 0x0D,
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
}

overflowPageFormat = {
    "nextOverflowPageOffset": 0,
    "nextOverflowPageLen": 4,
}

variantFormat = {
    "maxLen": 9,
}
