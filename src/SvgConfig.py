import __init__
from DbInfoTemplate import PageType


btreeList = { } # Top element

pageList = {  # Top element
    "x": 0,
    "y": 0,
}

page = {
    "width": 512,

    "fillColor": "#ffffff",
    "strokeWidth": 2,
    PageType.TABLE_LEAF + "strokeColor": "#ff3333",
    PageType.TABLE_INTERIOR + "strokeColor": "#cc3333",
    PageType.INDEX_LEAF + "strokeColor": "#3333ff",
    PageType.INDEX_INTERIOR + "strokeColor": "#3333cc",
}

cell = {
    "height": 4,
    "fillColor": "#ffaaaa",
}
