#!/usr/bin/env python
# coding: utf-8

# ## COP
# 
# 

# In[1]:


import json
import re
import requests
from haversine import haversine
from ipyleaflet import (Map, basemaps, basemap_to_tiles, WMSLayer, Marker, GeoJSON, AwesomeIcon, ImageOverlay, 
                        ScaleControl, LayersControl, ZoomControl, FullScreenControl, DrawControl, LayerGroup)


# In[2]:


# https://ipyleaflet.readthedocs.io/en/latest/map_and_basemaps/basemaps.html
# basemaps.Esri.WorldImagery
# basemap=basemap_to_tiles(basemaps.Esri.WorldImagery),
# url='https://www.gebco.net/data_and_products/gebco_web_services/web_map_service/mapserv',
# https://tiles.emodnet-bathymetry.eu/wmts/1.0.0/WMTSCapabilities.xml
# https://tiles.emodnet-bathymetry.eu/2020/baselayer/{TileMatrixSet}/{TileMatrix}/{TileCol}/{TileRow}.png
# https://tiles.emodnet-bathymetry.eu/2020/baselayer/web_mercator/{TileMatrix}/{TileCol}/{TileRow}.png
OSM=basemaps.OpenStreetMap.Mapnik
worldImagery = basemap_to_tiles(basemaps.Esri.WorldImagery)
gebco =WMSLayer(
    url='https://www.gebco.net/data_and_products/gebco_web_services/web_map_service/mapserv',
    layers='GEBCO_LATEST',
    format='image/png',
    transparent=True,
    attribution='GEBCO'
)
emodnet =WMSLayer(
    url='https://tiles.emodnet-bathymetry.eu/2020/baselayer/web_mercator/1/{TileCol}/{TileRow}.png',
    tms=True
)
m = Map(
    basemap=OSM,
    center=(42.9, 36.4),
    zoom=6,
    zoom_control=False,
    attribution_control=False
    )
m.add_control(ZoomControl(position='topright'))
m.add_control(LayersControl(position='topleft'))
m.add_control(ScaleControl(position='bottomright', metric=True, imperial=False))
m.add_control(FullScreenControl())


# In[3]:


def calc_line_KPs(coords, rnd=True, cum=True):
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


# In[4]:


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

p = re.compile(r"value_list\s*=\s*\'(-?\d*\.?\d*)")

def get_elevations(m, payload, coords):
    payload["width"] = int(m.right-m.left)
    payload["height"] = int(m.bottom-m.top)
    payload["BBOX"] = f"{m.south:.5f},{m.west:.5f},{m.north:.5f},{m.east:.5f}"
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


# In[5]:


get_elev = True


# In[6]:


draw_control = DrawControl()
draw_control.polyline =  {
    "shapeOptions": {
        "color": "#00FFFF",
        "weight": 6,
        "opacity": 1.0,
        "fillOpacity": 0
    }
}

def handle_draw(self, action, geo_json):
    """Do something with the GeoJSON when it's drawn on the map"""    
    #feature_collection['features'].append(geo_json)
    print(action)
    fname = "./data/geojson_from_map.json"
    if str(action)=="deleted": return None
    with open(fname, 'w') as fh:
        coords = geo_json["geometry"]["coordinates"]
        KP = calc_line_KPs(coords)
        geo_json["properties"]["style"]["fillOpacity"] = 0
        geo_json["properties"]["KP"] = KP
        if get_elev: geo_json["properties"]["elevation"] = get_elevations(m, payload, coords)
        json.dump(geo_json, fh)
        print(f"geojson data written to file {fname}")
draw_control.on_draw(handle_draw)
m.add_control(draw_control)


# # ((33.95833333333333, 138.99999999999997), (37.09583333333333, 142.44583333333335))
# image = ImageOverlay(name="elevation/depth contours",
#     url="./data/COP_elevation-depth_contours2.png",
#     bounds=((33.99999999999999, 138.6), (35.7, 140.4))
# )
# m.add_layer(image);

# def handle_click(**kwargs):
#     if kwargs["type"] in ["click", "contextmenu"]:
#         print(kwargs)

# m.on_interaction(handle_click)

# #dir(m)
# #m.get_state()
# print(m.west, m.south, m.east, m.north)

# In[7]:


geojson_file1 = "./data/BarMar_H2_pipeline_deepwater_route.json"
with open(geojson_file1, 'r') as f:
    east_data = json.load(f)
east_json = GeoJSON(name='deepwater route', data=east_data)
m.add_layer(east_json)


# with open('./data/COP_west_route_4.json', 'r') as f:
#     west_data = json.load(f)
# west_json = GeoJSON(name='West route', data=west_data)
# m.add_layer(west_json)

# with open('./data/COP_centre_route_5.json', 'r') as f:
#     west_data = json.load(f)
# west_json = GeoJSON(name='Centre route', data=west_data)
# m.add_layer(west_json)

# In[8]:


m


# In[9]:


#dir(m)
pass


# #m.get_state()
# print(m.west, m.south, m.east, m.north)
# print(m.left, m.right, m.right-m.left, m.pixel_bounds)
# print(m.bottom, m.top, m.bottom-m.top, m.pixel_bounds)

# # https://requests.readthedocs.io/en/latest/user/quickstart/#passing-parameters-in-urls
# payload = {
#     "request": "getfeatureinfo",
#     "service": "wms",
#     "crs": "EPSG:4326",
#     "layers": "gebco_latest_2",
#     "query_layers": "gebco_latest_2",
#     "BBOX": "33,138,38,143",
#     "info_format": "text/plain",
#     "x": "400",
#     "y": "400",
#     "width": "951",
#     "height": "400",
#     "version": "1.3.0"
# }
# payload["width"] = int(m.right-m.left)
# payload["height"] = int(m.bottom-m.top)
# payload["BBOX"] = f"{m.south:.5f},{m.west:.5f},{m.north:.5f},{m.east:.5f}"
# payload
# #r = requests.get('https://www.gebco.net/data_and_products/gebco_web_services/web_map_service/mapserv', params=payload)
# #r.text

# # https://requests.readthedocs.io/en/latest/user/quickstart/#passing-parameters-in-urls
# payload = {
#     "request": "getfeatureinfo",
#     "service": "wms",
#     "crs": "EPSG:4326",
#     "layers": "gebco_latest_2",
#     "query_layers": "gebco_latest_2",
#     "BBOX": "33,138,38,143",
#     "info_format": "text/plain",
#     "x": "400",
#     "y": "400",
#     "width": "951",
#     "height": "400",
#     "version": "1.3.0"
# }
# 
# p = re.compile(r"value_list\s*=\s*\'(-?\d*\.?\d*)")
# 
# def get_depths(m, payload, coords):
#     payload["width"] = int(m.right-m.left)
#     payload["height"] = int(m.bottom-m.top)
#     payload["BBOX"] = f"{m.south:.5f},{m.west:.5f},{m.north:.5f},{m.east:.5f}"
#     depths = []
#     for long, lat in coords:
#         payload["x"] = int((long-m.west)/(m.east-m.west)*payload["width"])
#         payload["y"] = int((lat-m.north)/(m.south-m.north)*payload["height"])
#         #print(payload["width"], payload["height"])
#         #print(payload["x"], payload["y"])
#         #print(payload["BBOX"])
#         gebcoStr = ""
#         url = 'https://www.gebco.net/data_and_products/gebco_web_services/web_map_service/mapserv'
#         req = requests.get(url, params=payload)
#         # https://requests.kennethreitz.org/en/latest/user/advanced/#prepared-requests
#         #req = requests.Request('GET', url, data=payload)
#         #prepped = req.prepare()
#         #print(prepped.body)
#         gebcoStr = req.text
#         success = False
#         if gebcoStr:
#             mm = p.search(gebcoStr)
#             if mm:
#                 depths.append(int(mm.groups(0)[0]))
#                 success = True
#         if not success:
#             depths.append(None)
#     return depths
#         
# coords = [[139.155735,34.269056],[139.180457,34.303087],[139.18595,34.339372]]
# coords = [[139.1633,34.2472]]
# # west route
# west_coords = [[139.155735,34.269056],[139.180457,34.303087],[139.18595,34.339372],[139.218912,34.384705],[139.23814,34.420954],[139.207925,34.457188],[139.18595,34.493406],[139.152988,34.522821],[139.109038,34.556749],[139.098051,34.583881],[139.059595,34.608745],[139.026633,34.633601],[138.98543,34.656191],[138.960709,34.692322],[138.982683,34.730694],[138.999164,34.769049],[139.054101,34.802876],[139.062342,34.852464],[139.098051,34.890762],[139.114532,34.929042],[139.087064,34.985303],[139.076076,35.028036],[139.059595,35.070747],[139.089811,35.117927],[139.120026,35.162835],[139.128266,35.223422],[139.199685,35.286205],[139.295824,35.313098],[139.405698,35.32654],[139.471623,35.339981],[139.523813,35.355659],[139.556775,35.369094]]
# east_coords = [[139.177662, 34.241938], [139.205131, 34.262365], [139.238093, 34.29413], [139.273802, 34.316812], [139.306764, 34.34629], [139.325992, 34.37349], [139.364448, 34.423336], [139.39741, 34.448247], [139.446853, 34.502574], [139.479816, 34.538772], [139.507284, 34.586258], [139.537499, 34.624679], [139.567715, 34.676633], [139.581449, 34.735323], [139.58969, 34.787207], [139.600677, 34.841312], [139.617158, 34.902138], [139.647373, 34.967419], [139.672095, 35.005663], [139.685875, 35.043785], [139.70785, 35.088734], [139.732571, 35.14264], [139.757295, 35.214449], [139.77927, 35.261546], [139.773776, 35.304135], [139.73532, 35.335501], [139.705105, 35.380289], [139.68313, 35.411626]]
# #depths = get_depths(m, payload, coords)
# #print(depths)

# teststr = "Layer 'GEBCO_LATEST_2'\n  Feature 0: \n    x = '-19.977083'\n    y = '50.964583'\n    value_list = '-3621'"
# p = re.compile(r"value_list\s*=\s*\'(-?\d*\.?\d*)")
# mm = p.search(teststr)
# mm.group(0)
# int(mm.groups(0)[0])

# # west route depths
# west_depths = [-77, -90, -188, -127, -132, -150, -343, -456, -441, -473, -384, -136, -10, 118, 117, 249, 162, 210, 242, 211, 179, 328, 323, 134, 181, 276, 10, 45, 8, 10, 40, 27]
# print(west_depths)

# # east route depths
# east_depths = [-61, -106, -127, -57, -69, -128, -109, -195, -110, -91, -435, -948, -1548, -1740, -1853, -863, -806, -395, -496, -724, -100, -319, -86, -52, -5, -34, -38, -22]
# print(east_depths)

# from haversine import haversine

# distances = []
# coords = west_coords
# for ii, coord1 in enumerate(coords[:-1]):
#     long1, lat1 = coord1
#     long2, lat2 = coords[ii+1]
#     #print(coord1, coord2)
#     dist = haversine((lat1, long1), (lat2, long2))
#     distances.append(dist)
# west_distances = distances
# #print(distances)

# distances = []
# coords = east_coords
# for ii, coord1 in enumerate(coords[:-1]):
#     long1, lat1 = coord1
#     long2, lat2 = coords[ii+1]
#     #print(coord1, coord2)
#     dist = haversine((lat1, long1), (lat2, long2))
#     distances.append(dist)
# east_distances = distances
# print(distances)
