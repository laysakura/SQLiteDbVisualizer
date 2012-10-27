#!/usr/bin/env python

import __init__
import Config
import DbInfoTemplate
import SQLiteAnalyzer
import OutputJson
import sys

def parse_args():
    if len(sys.argv) != 2:
        print("ARGS: dbpath")
        exit(1)
    return sys.argv[1]

def main():
    dbpath = parse_args()

    dbinfo = DbInfoTemplate.get_dbinfo_template()

    SQLiteAnalyzer.read_db(dbinfo, dbpath)

    OutputJson.output_dbinfo_json(dbinfo,
                                  Config.main["DbInfoJsonPath"],
                                  Config.main["DbInfoJsonEncoding"])

if __name__ == '__main__':
    main()
