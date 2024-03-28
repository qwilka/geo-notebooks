"""
Coordinate transformation functions
"""


from pyproj import CRS, Transformer



def toWSG84(coords_epsg, EPSG, always_xy=False):
    crs_EPSG = CRS.from_epsg(EPSG)
    crs_4326 = CRS.from_epsg(4326)
    trans = Transformer.from_crs(crs_EPSG, crs_4326, always_xy=always_xy)
    op_coords = []
    for coords in coords_epsg:
        _coor = trans.transform(coords[0], coords[1])
        op_coords.append(_coor)
    return op_coords


def fromWSG84(coords_WGS84, EPSG, always_xy=False):
    """coords_WGS84 list of WGS84 coordinates [[11.120575, 55.673816]]
    """
    crs_EPSG = CRS.from_epsg(EPSG)
    crs_4326 = CRS.from_epsg(4326)
    trans = Transformer.from_crs(crs_4326, crs_EPSG, always_xy=always_xy)
    op_coords = []
    for coords in coords_WGS84:
        _coor = trans.transform(coords[0], coords[1])
        op_coords.append(_coor)
    return op_coords

