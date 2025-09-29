# arctic_ice_forecaster/mapping.py
import folium
import geopandas as gpd
import datetime as dt
from . import config

def create_base_map() -> folium.Map:
    """Creates and returns a basic Folium map centered on the region of interest."""
    return folium.Map(
        location=config.INITIAL_MAP_LOCATION,
        zoom_start=config.INITIAL_MAP_ZOOM,
        tiles="cartodb positron"
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
    ).add_to(m)
    
def add_adfg_grid_layer(m: folium.Map):
    """Adds the ADFG forecast grid regions to the map."""
    popup = folium.GeoJsonPopup(
        # fields=["ADFG","link","image"],
        fields=["image_title","image"],    
        labels=False,    

        style="min-inline-size: 250px;",
        maxwidth='800px'
    )

    tooltip = folium.GeoJsonTooltip(
        fields=["ADFG"],
        maxwidth='200px'
    )

    folium.GeoJson(open(config.ADFG_GRID_FILE).read(),
        style_function=lambda feature: {
            "fillColor": "green"
            if "pri" in feature["properties"]["test"].lower()
            else "#ffff00",
            "color": "black",
            "weight": 2,
            "dashArray": "5, 5",
        },
        popup=popup,
        tooltip=tooltip,
        popup_keep_highlighted=True,
        control=True,
        name='ADFG Regions (Forecast)',
    ).add_to(m)

def add_gebco_contours_layer(m: folium.Map):
    """Adds bathymetry contour tiles from GEBCO."""
    folium.TileLayer(
        tiles=config.GEBCO_CONTOUR_TILES_URL,
        attr='GEBCO; NOAA NCEI',
        name='GEBCO Contours',
        overlay=True,
    ).add_to(m)

def add_sst_wms_layer(m: folium.Map):
    """Adds the NOAA Sea Surface Temperature WMS layer."""
    sat_sst_time = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=6)).strftime('%Y-%m-%dT00:00:00Z')
    noaa_layer = folium.WmsTileLayer(
        url=config.NOAA_SST_WMS_URL,
        name='NOAA Sea Surface Temp',
        layers='erdMBsstd8dayF_LonPM180:sst',
        fmt='image/png',
        transparent=True,
        attr='NOAA NMFS SWFSC ERD',
        parameters={'time': sat_sst_time},
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
