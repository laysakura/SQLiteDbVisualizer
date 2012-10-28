# This includes dynamically analyzed data from SQLite databases.
# Redundant information for visualization is contained.


class BtreeType:
    TABLE = "table"
    INDEX = "index"

class PageType:
    # FIRST_PAGE = "page#1"     # has db metadata
    TABLE_INTERIOR = "table interior page"
    TABLE_LEAF = "table leaf page"
    INDEX_INTERIOR = "index interior page"
    INDEX_LEAF = "index leaf page"
    OVERFLOW = "overflow page"
    UNCERTAIN = "uncertain page"


def get_dbinfo_template():
    """
    >>> dbinfo = get_dbinfo_template()
    >>> dbinfo['dbMetadata'] is not None
    True
    >>> dbinfo['pages'] is not None
    True
    >>> dbinfo['dbMetadata']['pageSize'] is not None
    True
    """
    return {
      "dbMetadata":
        {
          "pageSize": None, # UINT
          "nPages": None, # UINT
          "reservedSpace": None, # UINT
          "btrees":
            {
                "JUST FOR PASS ASSERTION": {},
              # "T0": {"type": BtreeType.TABLE },
              # "T0_ind": {"type": BtreeType.INDEX }
              # ...
            }
        },
      "pages":
        {
          # 1:  # Pages are read not always sequentially (ex: overflow page)
          #   {
          #     "pageMetadata":
          #       {
          #         "pageType": PageType.TABLE_LEAF,
          #         "nCells": None, # UINT  [TABLE_LEAF, TABLE_INTERIOR, INDEX_LEAF, INDEX_INTERIOR]
          #         "freeBlockOffset": None, # UINT  [TABLE_LEAF, TABLE_INTERIOR, INDEX_LEAF, INDEX_INTERIOR]
          #         "cellContentAreaOffset": None, # UINT  [TABLE_LEAF, TABLE_INTERIOR, INDEX_LEAF, INDEX_INTERIOR]
          #         "nextOverflowPageNum": None, # UINT  [OVERFLOW]
          #       }
          #
          #     # Table leaf example:
          #     "cells":
          #       [
          #         {
          #           "offset": None, # UINT
          #           "cellSize": None, # UINT
          #           "payloadSize": None, # UINT
          #           "rid": None, # UINT,
          #           "record": None, # Not supported yet
          #           "livingBtree": "T0"  # One of ret["dbMetadata"]["btrees"]
          #         },
          #         ...
          #       ]
          #   },
          # 2:
          #   {
          #     "pageType": PageType.INDEX_LEAF,
          #
          #     # Index (leaf|interior) example:
          #     "cells":
          #       [
          #         {
          #           "offset": None, # UINT
          #           "cellSize": None, # UINT
          #           "leftChildPageNum": None, #UINT  # Only for index interior page
          #           "payloadSize": None, # UINT
          #           "key": None, # Not supported yet,
          #           "livingBtree": "I0"  # One of ret["dbMetadata"]["btrees"]
          #         },
          #         ...
          #       ]
          #   },
          # ...
        }
    }


def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
