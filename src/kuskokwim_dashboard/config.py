# arctic_ice_forecaster/config.py
from pathlib import Path

# --- Project Directories ---
# Use pathlib for robust, cross-platform path handling
BASE_DIR = Path(__name__).resolve().parent.parent
PROJ_DIR = BASE_DIR / "kuskokwim_dashboard"
DATA_DIR = PROJ_DIR / "data"
OUTPUT_DIR = PROJ_DIR / "output"
IMAGE_DIR = PROJ_DIR / "images"

# --- Data Sources ---
NOAA_ICE_CHART_URL = "https://mapservices.weather.noaa.gov/vector/rest/services/obs/asip_ice_chart/MapServer"
GEBCO_CONTOUR_TILES_URL = "https://tiles.arcgis.com/tiles/C8EMgrsFcRFL6LrL/arcgis/rest/services/GEBCO_contours/MapServer/tile/{z}/{y}/{x}"
NOAA_SST_WMS_URL = 'https://coastwatch.pfeg.noaa.gov/erddap/wms/jplMURSST41/request?'
NOAA_SST_PNG_URL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.transparentPng"

# --- Map Settings ---
INITIAL_MAP_LOCATION = (59.75, -164.25)
INITIAL_MAP_ZOOM = 4
ADFG_GRID_FILE = DATA_DIR / "grid_ADFG.geojson"

# --- Analysis Parameters ---
# TODO: Deprecate ADFG_REGIONS in favor of REGIONID_FILE contents
ADFG_REGIONS = ['625831', '635830', '635900', '645900', '645931'] 

# --- Comprehensive Records File ---
REGIONID_FILE = "Grid_Main.csv"
