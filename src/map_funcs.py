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

from ipyleaflet import DrawControl

try:
    from haversine import haversine
    haversine_imported = True
except ImportError as err:
    logger.warning("Module «haversine» not found (required to calculate KPs); %s" % (err,) )
    haversine_imported = False



def calc_line_KPs(coords, rnd=True, cum=True):
    if not haversine_imported:
        raise Exception('calc_line_KPs: required module «haversine» not imported')
    KP = [0]
    for ii, coord1 in enumerate(coords[:-1]):
        long1, lat1 = coord1
        long2, lat2 = coords[ii+1]
        #print(coord1, coord2)
        dist = haversine((lat1, long1), (lat2, long2))
        #distances.append(dist)
        #print(type(dist), dist, len(distances))
        if cum:
            KP.append(dist + KP[-1])
        #if len(distances)>0 and cum:
        #    dist = dist + distances[-1]
        #    KP.append(dist)
        #    #print(dist, distances[-1])
        else:
            KP.append(dist)
        #print(distances)
    if rnd:
        KP = [round(ii, 3) for ii in KP]
    return KP



def get_elevations(map, coords):
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
    payload["width"] = int(map.right-map.left)
    payload["height"] = int(map.bottom-map.top)
    payload["BBOX"] = f"{map.south:.5f},{map.west:.5f},{map.north:.5f},{map.east:.5f}"
    p = re.compile(r"value_list\s*=\s*\'(-?\d*\.?\d*)")
    elevations = []
    for long, lat in coords:
        payload["x"] = int((long-map.west)/(map.east-map.west)*payload["width"])
        payload["y"] = int((lat-map.north)/(map.south-map.north)*payload["height"])
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


#dc_geoj_output_file = "draw_control_output.geojson"





def leaflet_draw_control(map, geojfile=None, KP=False, elevation=False, color="#00FFFF", weight=5):
    """Add ipyleaflet draw_control to map"""
    # if geojfile:
    #     dc_geoj_output_file = geojfile
    linestyle = {
        "color": color,
        "weight": weight,
        "opacity": 1.0,
        "fillOpacity": 0        
    }
    draw_control = DrawControl()
    draw_control.polyline =  {
        "shapeOptions": linestyle
    }

    def handle_draw(self, action, geo_json):
        """Do something with the GeoJSON when it's drawn on the map"""    
        #feature_collection['features'].append(geo_json)
        print(action)
        # fname = fname
        if str(action)=="deleted":
            return None
        geo_json["properties"]["style"] = linestyle
        coords = geo_json["geometry"]["coordinates"]
        if KP:
            KPs = calc_line_KPs(coords)
            geo_json["properties"]["KP"] = KPs
        if elevation:
            geo_json["properties"]["elevation"] = get_elevations(map, coords)
        if geojfile:
            with open(geojfile, 'w') as fh:
                json.dump(geo_json, fh)
                print(f"geojson data written to file {geojfile}")
        else:
            print(geo_json)

    draw_control.on_draw(handle_draw)
    map.add_control(draw_control)
    return draw_control
    # https://github.com/jupyter-widgets/ipyleaflet/pull/826
    #draw_control.data = [route_json1, route_json2]

