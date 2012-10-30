import __init__
from DbInfoTemplate import PageType


background = {
    "fillColor": "#ffffff",
}

page = {
    "width": 512,

    "fillColor": "#ffffff",
    "strokeWidth": 2,
    PageType.TABLE_LEAF + "strokeColor": "#ff3333",
    PageType.TABLE_INTERIOR + "strokeColor": "#aa0000",
    PageType.INDEX_LEAF + "strokeColor": "#3333ff",
    PageType.INDEX_INTERIOR + "strokeColor": "#0000aa",
    PageType.OVERFLOW + "strokeColor": "#33ff33",
    PageType.UNCERTAIN + "strokeColor": "#666666",
}

btreeList = {  # Top element
    "x": 0,
    "y": 10,

    "legendFontSize": 6,
    "legendHeight": 6,
    "legendNCol": 2,

    "legendDiffY": 4,
    "legendStrokeWidth": "1",
    "legendStrokeColor": "#000000",
}

btreeColorPalette = [
    #Basically Red,Yellow,Green,Blue,Purple rotation
    "MistyRose",
    "DarkOrange",
    "LightGreen",
    "CornflowerBlue",
    "MediumPurple",

    "LightCoral",
    "Khaki",
    "GreenYellow",
    "Turquoise",
    "DarkViolet",
]

pageList = {  # Top element
    "x": 0,
    "yPadFromBtreeList": 0,
}

cell = {
    "height": 4,
}

