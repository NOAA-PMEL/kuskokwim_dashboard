# arctic_ice_forecaster/data_processing.py
import logging
import geopandas as gpd
import pandas as pd
from arcgis.gis import GIS
from arcgis.mapping import MapImageLayer
from shapely.ops import transform
from typing import Tuple

from . import config

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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