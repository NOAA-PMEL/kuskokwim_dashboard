# arctic_ice_forecaster/mapping.py
import folium
import geopandas as gpd
import datetime as dt
from . import config

def create_base_map(crs=None, tiles=None) -> folium.Map:
    """Creates and returns a basic Folium map centered on the region of interest."""
    return folium.Map(
        location=config.INITIAL_MAP_LOCATION,
        zoom_start=config.INITIAL_MAP_ZOOM,
        tiles=tiles,
        crs=crs,
    )

def add_ice_concentration_layer(m: folium.Map, gdf: gpd.GeoDataFrame):
    """Adds the ice concentration layer to the map."""
    if gdf.empty:
        return
    folium.GeoJson(
        gdf,
        name='Ice Concentration',
        style_function=lambda feature: {
            'fillColor': '#5271ff',
            'color': '#ffffff',
            'weight': 1,
            'fillOpacity': 0.0 if "00" in feature['properties']['ct'] else 0.5,
        },
        tooltip=folium.GeoJsonTooltip(fields=['ct'], aliases=['Total Concentration:'], sticky=True),
    ).add_to(m)

def add_ice_prediction_layer(m: folium.Map, gdf: gpd.GeoDataFrame):
    """Adds the ice prediction layer to the map."""
    if gdf.empty:
        return
    folium.GeoJson(
        gdf,
        name='Ice Prediction',
        style_function=lambda feature: {
            'fillColor': '#aaaaaa',
            'color': '#ffffff',
            'weight': 1,
            'fillOpacity': 0.0 if "free" in feature['properties']['type'].lower() else 0.5,
        },
        tooltip=folium.GeoJsonTooltip(fields=['type'], aliases=['Prediction:'], sticky=True),
        show=False
    ).add_to(m)
    
def add_adfg_grid_layer(m: folium.Map, popup_on: bool = True):
    """Adds the ADFG forecast grid regions to the map."""
    if popup_on:
        popup = folium.GeoJsonPopup(
            # fields=["ADFG","link","image"],
            fields=["temp_table","link"],    
            labels=False,    

            style="min-inline-size: 250px;",
            maxwidth='800px'
        )
        popup_keep_highlighted=True
    else:
        popup_keep_highlighted=False
        popup = None

    tooltip = folium.GeoJsonTooltip(
        fields=["ADFG"],
        maxwidth='200px'
    )

    with open(config.ADFG_GRID_FILE) as f:
        geojson_data = f.read()
        
    folium.GeoJson(geojson_data,
        style_function=lambda feature: {
            "fillColor": "green"
            if "pri" in feature["properties"]["test"].lower()
            else None,
            "color": "black",
            "weight": 2,
            "dashArray": "5, 5",
            "fillOpacity": .5
            if "pri" in feature["properties"]["test"].lower()
            else 0,
        },
        popup=popup,
        tooltip=tooltip,
        popup_keep_highlighted=popup_keep_highlighted,
        control=True,
        name='ADFG Regions (Forecast)',
    ).add_to(m)

def add_gebco_contours_layer(m: folium.Map):
    """Adds bathymetry contour tiles from GEBCO."""
    folium.TileLayer(
        tiles=config.GEBCO_CONTOUR_TILES_URL,
        attr='GEBCO; NOAA NCEI',
        name='Bathymetry Contours (m)',
        overlay=True,
    ).add_to(m)

def add_sst_wms_layer(m: folium.Map):
    """Adds the NOAA Sea Surface Temperature WMS layer."""
    sat_sst_time = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).strftime('%Y-%m-%dT09:00:00Z')
    noaa_layer = folium.WmsTileLayer(
        url=config.NOAA_SST_WMS_URL,
        name='JPL Sea Surface Temp',
        layers='jplMURSST41:analysed_sst',
        fmt='image/png',
        transparent=True,
        attr='NOAA NMFS SWFSC ERD',
        parameters={'time': sat_sst_time},
        version='1.3.0',
        overlay=True,
    )
    noaa_layer.add_to(m)

def add_mooring_marker(m: folium.Map):
    """Adds a marker for the M2 "Peggy" Mooring."""
    folium.Marker(
        location=[56.8706, -164.0414],
        popup="<i>M2 \"Peggy\" Mooring</i>",
        tooltip="Click for more info",
    ).add_to(m)

@staticmethod
def get_sst_legend() -> str:
    """builds url to retrieve legend as png"""
    sat_sst_time = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).strftime('%Y-%m-%dT09:00:00Z')
    legend_url = (
        f"{config.NOAA_SST_PNG_URL}?"
        f"analysed_sst%5B({sat_sst_time})%5D%5B(0.0)%5D%5B(-45.0):(65.0)%5D%5B(-180.0):(179.975)%5D"
        f"&.draw=surface&.vars=longitude%7Clatitude%7Canalysed_sst"
        f"&.colorBar=%7C%7C%7C%7C%7C&.bgColor=0xffccccff&.legend=Only"
    )
    return legend_url