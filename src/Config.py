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
}

btreeHeaderFormat = {
    # Page#1 has special format
    "offsetInPage1": dbHeaderFormat["offsetInFile"] + dbHeaderFormat["len"],
    "offsetInPage": 0,

    "len": 12,
    "btreeFlagOffset": 0,
    "btreeFlagLen": 1,
    "freeSpaceOffset": 1,
    "freeSpaceLen": 2,
    "nCellsOffset": 3,
    "nCellsLen": 2,
    "cellContentAreaOffset": 5,
    "cellContentAreaLen": 2,

    "indexInternalPageFlag": 0x02,
    "indexLeafPageFlag": 0x0A,
    "tableInternalPageFlag": 0x05,
    "tableLeafPageFlag": 0x0D,
}

cellPointerArrayFormat = {
    "offsetInPage1": btreeHeaderFormat["offsetInPage1"] + btreeHeaderFormat["len"],
    "offsetInPage": btreeHeaderFormat["offsetInPage"] + btreeHeaderFormat["len"],

    "elemLen": 2,
}

variantFormat = {
    "maxLen": 9,
}
