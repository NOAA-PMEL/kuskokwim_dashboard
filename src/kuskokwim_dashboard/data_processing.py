# arctic_ice_forecaster/data_processing.py
import logging
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from arcgis.gis import GIS
from arcgis.mapping import MapImageLayer
from shapely.ops import transform
from typing import Tuple

from . import config

# Set up basic logging
logging.basicConfig(filename=f'{config.LOG_FILE_NAME}',level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_ice_data() -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Fetches the latest ice concentration and prediction data from the NOAA MapServer.

    Returns:
        A tuple containing two GeoDataFrames: (ice_concentration, ice_prediction).
    """
    try:
        logging.info("Connecting to ArcGIS GIS anonymously...")
        gis = GIS()
        ice_chart_service = MapImageLayer(config.NOAA_ICE_CHART_URL, gis)
        
        logging.info("Querying ice concentration layer...")
        ice_concentration_layer = ice_chart_service.layers[0]
        concentration_sdf = ice_concentration_layer.query(where="1=1", as_df=True)
        gdf_conc = gpd.GeoDataFrame(concentration_sdf, geometry='SHAPE').set_crs(epsg=4326)

        logging.info("Querying ice prediction layer...")
        ice_prediction_layer = ice_chart_service.layers[2]
        prediction_sdf = ice_prediction_layer.query(where="1=1", as_df=True)
        gdf_pred = gpd.GeoDataFrame(prediction_sdf, geometry='SHAPE').set_crs(epsg=4326)

        return gdf_conc, gdf_pred
    except Exception as e:
        logging.error(f"Failed to fetch ice data: {e}")
        # Return empty GeoDataFrames on failure
        return gpd.GeoDataFrame(), gpd.GeoDataFrame()

def convert_to_360_transform(x: float, y: float, z: float = None) -> Tuple[float, float]:
    """Shapely transform function to convert longitude from [-180, 180] to [-360, 0]."""
    return (x - 360, y) if x > 0 else (x, y)

def reproject_to_360(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Applies a longitude transformation to a GeoDataFrame to prevent wrapping issues
    across the antimeridian.

    Args:
        gdf: The input GeoDataFrame with CRS EPSG:4326.

    Returns:
        A new GeoDataFrame with transformed coordinates.
    """
    if gdf.empty:
        logging.warning("Input GeoDataFrame is empty. Skipping reprojection.")
        return gdf

    logging.info("Reprojecting GeoDataFrame to prevent dateline wrapping...")
    gdf_transformed = gdf.copy()
    gdf_transformed['SHAPE'] = gdf_transformed['SHAPE'].apply(
        lambda geom: transform(convert_to_360_transform, geom)
    )
    return gdf_transformed

def load_temperature_data(file_path: str) -> pd.DataFrame:
    """
    Loads sea surface temperature data from a CSV file.

    Args:
        file_path: Path to the CSV file.

    Returns:
        A DataFrame containing the temperature data.
    """
    try:
        logging.info(f"Loading temperature data from {file_path}...")
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        logging.error(f"Failed to load temperature data: {e}")
        return pd.DataFrame()

def jplsst_getter(adfg_id: str, erddap_url: str, sat_sst_time: str) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    """


    Note:
    Byte flag_masks 1, 2, 4, 8, 16;
    String flag_meanings "open_sea land open_lake open_sea_with_ice_in_the_grid open_lake_with_ice_in_the_grid";

    So we want to exclude land and look at with and without ice, that means 1 (open water, no ice) and 9 (open water, with ice)
    """
    sites = pd.read_csv(config.REGIONID_FILE)
    coords = sites[sites['regID']==adfg_id]

    try:
        url =f"""{erddap_url}analysed_sst%5B({sat_sst_time}):1:({sat_sst_time})%5D%5B({coords['S'].values[0]}):1:({coords['N'].values[0]})%5D%5B({coords['W'].values[0]}):1:({coords['E'].values[0]})%5D,
analysis_error%5B({sat_sst_time}):1:({sat_sst_time})%5D%5B({coords['S'].values[0]}):1:({coords['N'].values[0]})%5D%5B({coords['W'].values[0]}):1:({coords['E'].values[0]})%5D,
mask%5B({sat_sst_time}):1:({sat_sst_time})%5D%5B({coords['S'].values[0]}):1:({coords['N'].values[0]})%5D%5B({coords['W'].values[0]}):1:({coords['E'].values[0]})%5D,
sea_ice_fraction%5B({sat_sst_time}):1:({sat_sst_time})%5D%5B({coords['S'].values[0]}):1:({coords['N'].values[0]})%5D%5B({coords['W'].values[0]}):1:({coords['E'].values[0]})%5D"""
        
        url = "".join(url.split('\n'))
        df = pd.read_csv(url)
        mean_wice = df[df['mask']==9].mean(numeric_only=True).to_frame().T
        mean_wice['time'] = sat_sst_time
        mean_woice = df[df['mask']==1].mean(numeric_only=True).to_frame().T
        mean_woice['time'] = sat_sst_time
        #ToDo: Mask Out Land above too for coastal boxes

        return df, mean_wice, mean_woice, sat_sst_time
    except Exception as e:
        logging.error(f"Failed to load temperature data: {e}:")
        return pd.DataFrame()

def ASIP_Prediction(df: pd.DataFrame, ice_pred: gpd.geodataframe) -> pd.DataFrame():
    """pass in dataframe with coords of center of box, 
    and determine if its within the ASIP prediction shape file."""
    df['coords'] = df['coords'].apply(Point)
    points = gpd.GeoDataFrame(df, geometry='coords', crs="EPSG:4326").to_crs(ice_pred.crs)

    forpointInPolys = gpd.tools.sjoin(points, 
                                      ice_pred.rename({'SHAPE':'geometry'}), 
                                      predicate="within", 
                                      how='left')
    if forpointInPolys['st_area(shape)'].isna().all():
        print('No ice')
        return 0
    else:
        print('Ice at location in prediction')
        return 1

def geojson_gridbuilder(df: pd.DataFrame) -> str:
    """
    Converts a DataFrame of grid regions into a GeoJSON FeatureCollection.
    
    Args:
        df: DataFrame with columns: regID, active, W, E, N, S
        
    Returns:
        A formatted GeoJSON string representing grid regions as polygons.
    """
    json_header = """{
    "type": "FeatureCollection",
    "name": "grid_ADFG",
    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
    "features": [
    """
    features = []
    
    for _, row in df.iterrows():
        adfg_id = row.regID.split('_')[1]
        coords = [[row.W, row.S], [row.E, row.S], [row.E, row.N], [row.W, row.N], [row.W, row.S]]
        
        if row['active'] == 'y':
            properties = {
                "ADFG": adfg_id,
                "test": "pri_reg",
                "image_title": "<strong>click image below for indepth analysis</strong>",
                "image": f'<br><a href="{adfg_id}.html" target="_blank"><img src="{adfg_id}.image.png" width="250px"/>',
                "temp_table": "<table><tr><th>SST</th><th>BotTemp</th><th>SeaIce</th></tr><tr><td>-1.8C/29F</td><td>-1.8C/29F</td><td>1 (ice)</td></tr></table>",
                "link": f'<a href="{adfg_id}.html" target="_blank">more info</a>'
            }
        else:
            properties = {
                "ADFG": adfg_id,
                "test": "grid",
                "image_title": "<strong>click image below for indepth analysis</strong>",
                "image": "<br><strong>Coming Soon</strong>",
                "temp_table": "",
                "link": "coming_soon"
            }
        
        feature = {
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }
        features.append(feature)
    
    import json
    json_body = ",\n".join(json.dumps(f) for f in features)
    json_tail = "\n]\n}"
    
    return json_header + json_body + json_tail