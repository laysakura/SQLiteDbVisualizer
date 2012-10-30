#!/usr/bin/env python

import __init__
import DbInfoTemplate
from SQLiteAnalyzer import SQLiteAnalyzer
from Json2Svg import Json2Svg
import sys
import os

def parse_args():
    if len(sys.argv) != 2:
        print("ARGS: dbpath")
        exit(1)
    return sys.argv[1]

def main():
    dbPath = parse_args()
    jsonPath = os.path.basename(dbPath) + ".json"
    svgPath = os.path.basename(dbPath) + ".svg"
    analyzer = SQLiteAnalyzer(dbPath)
    analyzer.dumpJson(outPath=jsonPath)
    json2Svg = Json2Svg(jsonPath=jsonPath, svgPath=svgPath)
    json2Svg.dumpSvg()


if __name__ == '__main__':
    main()
