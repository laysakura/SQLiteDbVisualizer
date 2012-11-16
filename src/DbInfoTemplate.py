# This includes dynamically analyzed data from SQLite databases.
# Redundant information for visualization is contained.


class BtreeType:
    TABLE = "table"
    INDEX = "index"


class PageType:
    TABLE_INTERIOR = "table interior page"
    TABLE_LEAF = "table leaf page"
    INDEX_INTERIOR = "index interior page"
    INDEX_LEAF = "index leaf page"
    OVERFLOW = "overflow page"
    FREELIST_TRUNK = "freelist trunk page"
    FREELIST_LEAF = "freelist leaf page"
    UNCERTAIN = "uncertain page"


class CellContent:
    LEFT_CHILD_PAGE_NUM = "left child page num"
    PAYLOAD_SIZE = "payload size"
    RID = "rid"
    PAYLOAD = "payload"
    OVERFLOW_PAGE_HEAD = "overflow page head"


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
          "pageSize": None,  # UINT
          "nPages": None,  # UINT
          "usablePageSize": None,  # UINT
          "btrees":
            [
              # {
              #   "type": BtreeType.INDEX,
              #   "name": "idx_T0",
              #   "tableName": "T0",
              #   "rootPage": 8
              # },
              # ...
            ],
          "freelistTrunkHead": None,  # UINT
          "nFreelistPages": None,  # UINT
        },
      "pages":
        {
          # 1:  # Pages are read not always sequentially (ex: overflow page)
          #   {
          #     # [TABLE_LEAF, TABLE_INTERIOR,
          #     #  INDEX_LEAF, INDEX_INTERIOR,
          #     #  OVERFLOW,
          #     #  FREELIST_TRUNK]
          #     "pageMetadata":
          #       {
          #         # [TABLE_LEAF, TABLE_INTERIOR,
          #         #  INDEX_LEAF, INDEX_INTERIOR,
          #         #  OVERFLOW,
          #         #  FREELIST_TRUNK, FREELIST_LEAF]
          #         "pageType": PageType.TABLE_LEAF,
          #
          #         # [TABLE_LEAF, TABLE_INTERIOR,
          #         #  INDEX_LEAF, INDEX_INTERIOR, OVERFLOW]
          #         "nCells": None,  # UINT
          #
          #         # [TABLE_LEAF, TABLE_INTERIOR, INDEX_LEAF, INDEX_INTERIOR]
          #         "freeBlockOffset": None, # UINT
          #
          #         # [TABLE_LEAF, TABLE_INTERIOR, INDEX_LEAF, INDEX_INTERIOR]
          #         "cellContentAreaOffset": None, # UINT
          #
          #         # [OVERFLOW]
          #         "nextOverflowPageNum": None, # UINT
          #
          #         # [TABLE_LEAF, TABLE_INTERIOR,
          #         #  INDEX_LEAF, INDEX_INTERIOR, OVERFLOW]
          #         "livingBtree": "T0"  # One of ret["dbMetadata"]["btrees"]
          #
          #         # [TABLE_INTERIOR, INDEX_INTERIOR]
          #         "rightmostChildPageNum": None, # UINT
          #
          #         # [FREELIST_TRUNK]
          #         # "nextFreelistTrunkPageNum": None,  # UINT
          #
          #         # [FREELIST_TRUNK]
          #         # "nFreelistLeaves": None,  # UINT
          #       }
          #
          #     # [TABLE_LEAF, TABLE_INTERIOR,
          #     #  INDEX_LEAF, INDEX_INTERIOR, OVERFLOW]
          #     "cells":
          #       [
          #         {
          #           # [TABLE_LEAF, TABLE_INTERIOR,
          #           #  INDEX_LEAF, INDEX_INTERIOR, OVERFLOW]
          #           "offset": None, # UINT
          #
          #           # [TABLE_LEAF, TABLE_INTERIOR,
          #           #  INDEX_LEAF, INDEX_INTERIOR, OVERFLOW]
          #           "cellSize": None, # UINT
          #
          #           # [TABLE_INTERIOR, INDEX_INTERIOR]
          #           "leftChildPage": None, # UINT
          #
          #           # [TABLE_LEAF, TABLE_INTERIOR]
          #           "rid": None, # UINT
          #
          #           # [TABLE_LEAF, INDEX_LEAF, INDEX_INTERIOR]
          #           "overflowPage": None, # UINT
          #
          #           # [TABLE_LEAF, INDEX_LEAF, INDEX_INTERIOR]
          #           "payload":  # TODO: payload contents?
          #             {
          #               "offset": None, # UINT
          #               "headerSize": None, # UINT
          #               "bodySize": None, # UINT
          #               "cols": [
          #                 {
          #                   "stype": None,  # UINT
          #                   "size": None,  # UINT (Got from stype)
          #                   "content": None:  # INT is only supported.
          #                 }
          #               ]
          #             },
          #         },
          #         ...
          #       ]
          #     # [FREELIST_TRUNK]
          #     "freelistLeafPageNums": [3, 4, 8, ...],  # Leaf page num
          #   },
          # 2:
          #   ...
          # ...
        }
    }


def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
