# arctic_ice_forecaster/config.py
from pathlib import Path
import datetime as dt

# --- Project Directories ---
# Use pathlib for robust, cross-platform path handling
BASE_DIR = Path(__name__).resolve().parent.parent
PROJ_DIR = BASE_DIR / "kuskokwim_dashboard"
DATA_DIR = PROJ_DIR / "data"
CONFIG_DIR = PROJ_DIR / "config"
OUTPUT_DIR = PROJ_DIR / "output"
IMAGE_DIR = PROJ_DIR / "images"
LOG_DIR = PROJ_DIR / "logs"

# --- Data Sources ---
NOAA_ICE_CHART_URL = "https://mapservices.weather.noaa.gov/vector/rest/services/obs/asip_ice_chart/MapServer"
GEBCO_CONTOUR_TILES_URL = "https://tiles.arcgis.com/tiles/C8EMgrsFcRFL6LrL/arcgis/rest/services/GEBCO_contours/MapServer/tile/{z}/{y}/{x}"
NOAA_SST_WMS_URL = 'https://coastwatch.pfeg.noaa.gov/erddap/wms/jplMURSST41/request?'
NOAA_SST_PNG_URL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.transparentPng"
NOAA_SST_URL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.csvp?"
COASTWATCH_ERDDAP_URL = "https://coastwatch.pfeg.noaa.gov/erddap/"

# --- Map Settings ---
INITIAL_MAP_LOCATION = (59.75, -164.25)
INITIAL_MAP_ZOOM = 4
ADFG_GRID_FILE = CONFIG_DIR / "grid_ADFG.geojson"
GEBCO_BATHY = DATA_DIR / "gebco_subset.nc"

# --- Comprehensive Records File ---
REGIONID_FILE = CONFIG_DIR / "Grid_Main.csv"

# --- Generated Files ---
PROJECTED_DATA_FILE = DATA_DIR / "kuskokwim_projected_data.csv"
CURRENT_YEAR_DATA_FILE = DATA_DIR / "kuskokwim_currentyear_data.csv"

# --- Logging ---
LOG_FILE_NAME = f"{LOG_DIR}/{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"