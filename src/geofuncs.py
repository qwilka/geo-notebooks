"""

https://spatialreference.org/ref/epsg/4326/
https://geojson.org/
https://datatracker.ietf.org/doc/html/rfc7946    The GeoJSON Format
https://github.com/jazzband/geojson
https://github.com/mapado/haversine
"""
import json
import logging
import re

import geojson
import requests

logger = logging.getLogger(__name__)

try:
    from haversine import haversine
    haversine_imported = True
except ImportError as err:
    logger.warning("Module «haversine» not found; %s" % (err,) )
    haversine_imported = False


def geojson_line(coords, save=False, properties=None, color='#00FFFF'):
    """Create geojson linestring from a list of WGS84 [long, lat] coords.
    """
    # geo_json = {}
    # geo_json["geometry"]["coordinates"] = 
    ls = geojson.LineString(coords)
    if properties:
        if isinstancce(properties, dict):
            ls["properties"] = properties
        else:
            ls["properties"] = {
                "style": {
                    "stroke": True,
                    'color': color,
                    'weight': 6,
                    'opacity': 1,
                    'fill': False,
                    'clickable': True,
                    'fillOpacity': 0
                }
            }




def calc_line_KPs(coords, rnd=True, cum=True):
    KP = [0]
    for ii, coord1 in enumerate(coords[:-1]):
        long1, lat1 = coord1
        long2, lat2 = coords[ii+1]
        dist = haversine((lat1, long1), (lat2, long2))
        if cum:
            KP.append(dist + KP[-1])
        else:
            KP.append(dist)
    if rnd:
        KP = [round(ii, 3) for ii in KP]
    return KP



def get_elevations(m, payload, coords):
    payload = {
        "request": "getfeatureinfo",
        "service": "wms",
        "crs": "EPSG:4326",
        "layers": "gebco_latest_2",
        "query_layers": "gebco_latest_2",
        "BBOX": "33,138,38,143",
        "info_format": "text/plain",
        "x": "400",
        "y": "400",
        "width": "951",
        "height": "400",
        "version": "1.3.0"
    }
    payload["width"] = int(m.right-m.left)
    payload["height"] = int(m.bottom-m.top)
    payload["BBOX"] = f"{m.south:.5f},{m.west:.5f},{m.north:.5f},{m.east:.5f}"
    p = re.compile(r"value_list\s*=\s*\'(-?\d*\.?\d*)")
    elevations = []
    for long, lat in coords:
        payload["x"] = int((long-m.west)/(m.east-m.west)*payload["width"])
        payload["y"] = int((lat-m.north)/(m.south-m.north)*payload["height"])
        #print(payload["width"], payload["height"])
        #print(payload["x"], payload["y"])
        #print(payload["BBOX"])
        gebcoStr = ""
        url = 'https://www.gebco.net/data_and_products/gebco_web_services/web_map_service/mapserv'
        req = requests.get(url, params=payload)
        # https://requests.kennethreitz.org/en/latest/user/advanced/#prepared-requests
        #req = requests.Request('GET', url, data=payload)
        #prepped = req.prepare()
        #print(prepped.body)
        gebcoStr = req.text
        success = False
        if gebcoStr:
            mm = p.search(gebcoStr)
            if mm:
                elevations.append(int(mm.groups(0)[0]))
                success = True
        if not success:
            elevations.append(None)
    return elevations


