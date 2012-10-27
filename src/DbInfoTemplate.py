class BtreeType:
    TABLE = "table"
    INDEX = "index"

class PageType:
    FIRST_PAGE = "page#1"     # has db metadata
    TABLE_INTERNAL = "table internal page"
    TABLE_LEAF = "table leaf page"
    INDEX_INTERNAL = "index internal page"
    INDEX_LEAF = "index leaf page"
    OTHER = "other page"


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
          "pageSize": -1,
          "nPages": -1,
          "btrees":
            {
              # "T0": {"type": BtreeType.TABLE },
              # "T0_ind": {"type": BtreeType.INDEX }
              # ...
            }
        },
      "pages":   # Page_no = index + 1
        [
          # {
          #   "pageType": PageType.FIRST_PAGE,
          #   "cells":
          #     [
          #       {
          #         "offset": -1,
          #         "size": -1,
          #         "livingBtree": "T0"  # One of ret["dbMetadata"]["btrees"]
          #       }
          #     ]

          # },
          # ...
        ]
    }


def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
