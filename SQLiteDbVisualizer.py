#!/usr/bin/env python

import __init__
import Config
import DbInfoTemplate
from SQLiteAnalyzer import SQLiteAnalyzer
import sys
import os

def parse_args():
    if len(sys.argv) != 2:
        print("ARGS: dbpath")
        exit(1)
    return sys.argv[1]

def main():
    dbpath = parse_args()
    analyzer = SQLiteAnalyzer(dbpath)
    analyzer.dumpJson(outPath=os.path.basename(dbpath) + ".json")


if __name__ == '__main__':
    main()
