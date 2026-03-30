# arctic_ice_forecaster/data_processing.py
import logging
import glob
import os
import geopandas as gpd
import pandas as pd
import datetime as dt
from erddapy import ERDDAP
from shapely.geometry import Point
from arcgis.gis import GIS
from arcgis.mapping import MapImageLayer
from shapely.ops import transform
from typing import Tuple

import xarray as xr

from . import config

# Set up basic logging
logging.basicConfig(filename=f'{config.LOG_FILE_NAME}',level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_sst_data(start_date, end_date) -> xr.DataArray:
        """Fetches JPL MUR SST data via ERDDAP."""
        print("Fetching SST data from ERDDAP...")

        # 1. Initialize with basic info
        e = ERDDAP(
            server="https://coastwatch.pfeg.noaa.gov/erddap",
            protocol="griddap",
            response="nc"
        )
        e.dataset_id = "jplMURSST41"

        # 2. Set variables
        e.variables = ["analysed_sst"]

        # 3. Use the literal constraint keys expected by the griddap protocol
        # This prevents the library from "guessing" and defaulting to global.
        e.constraints.update({
            "time>=": start_date,
            "time<=": end_date,
            "latitude>=": 55.0,
            "latitude<=": 60.5,
            "longitude>=": -168.0,
            "longitude<=": -158.0,
        })

        # 4. Generate the URL manually and download via xarray
        # This bypasses the picky 'to_xarray' internal checks
        url = e.get_download_url()
        print(f"Requesting data from: {url}")  # This helps us debug if it fails again

        ds = e.to_xarray()

        return ds.analysed_sst 

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

def process_file(filename):
    """
    Processes a single *proj file to extract region, date, and value information.
    """
    # Extract RegionID (6 characters following "ADFG_")
    region_id = filename.split('ADFG_')[1][:6]
    
    # Extract value column name
    val_col_name = filename.split('proj_')[-2][-3:]

    # Read the file
    df = pd.read_csv(filename)
    
    # Retrieve the year from the first column (YYYYMMDD)
    year_val = int(str(int(df.iloc[0, 0]))[:4])
    
    # Remove the first column
    df_data = df.drop(columns=[df.columns[0]])
    
    # Transpose the remaining array
    df_transposed = df_data.transpose().reset_index()
    df_transposed.columns = ['Month_Day', val_col_name]
    
    # Add Year and Calculate DOY
    df_transposed['Year'] = year_val
    date_str = df_transposed['Year'].astype(str) + df_transposed['Month_Day']
    df_transposed['Yearday'] = pd.to_datetime(date_str, format='%Y%m%d').dt.dayofyear
    
    # Add RegionID column
    df_transposed['RegionID'] = region_id
    
    return df_transposed[['Month_Day', 'Year', 'Yearday', 'RegionID', val_col_name]]

def combine_projected_data() -> pd.DataFrame:
    """
    Reads all *proj files from the data directory and combines them into a
    single DataFrame with columns: regionid, doy, year, sst, ice, bot.
    
    Returns:
        A combined DataFrame with all projected data.
    """
    
    data_dir = config.DATA_DIR
    proj_files = glob.glob(str(data_dir / "*proj*"))
    proj_files =[f for f in proj_files if 'ICE' not in f and '_data' not in f]
    
    if not proj_files:
        logging.warning(f"No *proj files found in {data_dir}")
        return pd.DataFrame()
    
    dfs = []
    for file_path in proj_files:
        try:
            # Dictionary to hold dataframes grouped by RegionID
            region_groups = {}

            for f in proj_files:
                region_id = f.split('ADFG_')[1][:6]
                df_proc = process_file(f)
                
                if region_id not in region_groups:
                    region_groups[region_id] = df_proc
                else:
                    # Merge BOT and SST data for the same RegionID
                    region_groups[region_id] = pd.merge(
                        region_groups[region_id], 
                        df_proc, 
                        on=['Month_Day', 'Year', 'Yearday', 'RegionID'], 
                        how='outer'
                    )

            # Append all unique RegionID datasets together
            dfs = pd.concat(region_groups.values(), ignore_index=True)
            logging.info(f"Processed {len(proj_files)} files into a combined DataFrame with shape: {dfs.shape}")
        except Exception as e:
            logging.error(f"Failed to read {file_path}: {e}")
    
    # if not dfs:
    #     logging.warning("No valid projected data files were read")
    #     return pd.DataFrame()

    return dfs

def generate_projected_data(date_valid: str) -> None:
    """
    Projected SST and BTM data generator
    """
    site_list = pd.read_csv(config.REGIONID_FILE)
    site_list = site_list[site_list['active'] == 'y']

    # 2. Define the seasonal window (March 5 to July 31)
    start_m, start_d = 3, 5
    end_m, end_d = 7, 31

    for index, site in site_list.iterrows():

        reg_id = site['regID']
        shf_scale = site['shf_scale']

        sst_file = config.DATA_DIR / f"{reg_id}_SST_{date_valid}.csv"
        ice_file = config.DATA_DIR / f"{reg_id}_ICEproj_{date_valid}.csv"
        shf_file = config.DATA_DIR / "KU2_dTQnet.csv"
        output_file = config.DATA_DIR / f"{reg_id}_SSTproj.csv"

        # Validate required input files exist before reading. Skip if missing.
        missing_files = [str(p) for p in (sst_file, ice_file, shf_file) if not p.exists()]
        if missing_files:
            logging.warning(
                f"Skipping {reg_id} because required files are missing: {', '.join(missing_files)}"
            )
            continue

        try:
            df_sst = pd.read_csv(f'{sst_file}',dtype={'Time':str})
            df_shf = pd.read_csv(shf_file,index_col='DOY').mean(axis=1).to_frame('Qnet')
            df_ice = pd.read_csv(ice_file)

            btm_data = {
                'BTM': df_sst.mean(numeric_only=True).SST,
                'Time': df_sst.iloc[-1]
            }

            result_df = pd.DataFrame(btm_data)
            result_df.to_csv(output_file.replace('SSTproj','BTM'), index=False)
            print(f"Successfully created: {output_file.replace('SSTproj','BTM')}")
            print(f"Loading {reg_id}")
        except Exception as e:
            print(f"Skipping {reg_id}: {e}")
            continue
    
        # Convert Time columns to datetime objects
        df_sst['Time'] = pd.to_datetime(df_sst['Time'], format='%Y%m%d')
        df_ice['Time'] = pd.to_datetime(df_ice['Time'], format='%Y%m%d')
    
        # Identify unique years in the historical SST data
        sst_years = df_sst['Time'].dt.year.unique()
    
        # Determine the columns for the output (MMDD headers)
        # We use a dummy leap year (2000) to generate all possible MMDD strings
        dummy_range = pd.date_range("2000-03-05", "2000-07-31")
        mmdd_cols = [d.strftime('%m%d') for d in dummy_range]
    
        all_results = []
    
        # Loop through each historical year to find initialization dates
        for year in sst_years:
            year_start = dt.datetime(year, start_m, start_d)
            year_end = dt.datetime(year, end_m, end_d)
            current_range = pd.date_range(year_start, year_end)
    
            for init_date in current_range:
                # Check Sea Ice: Initialize only if no ice tomorrow
                ice_row = df_ice[df_ice['Time'] == init_date]
                if ice_row.empty or ice_row['ICE'].values[0] > 0:
                    # print(f"Ice Detected {reg_id}: Skipping Prediction")
                    continue
    
                # Get the SST 5-day trailing mean for the initialization date
                # MATLAB: mean(T_hist.SST(isample-4:isample))
                mask = (df_sst['Time'] <= init_date)
                last_5_days = df_sst[mask].tail(5)
    
                if len(last_5_days) < 5:
                    continue
    
                t_sample = last_5_days['SST'].mean()
    
                # Calculate Projection based on Heat Flux (SHF)
                # Get DOY range for the remainder of the season
                doy_start = init_date.timetuple().tm_yday
                doy_end = year_end.timetuple().tm_yday
    
                # Slice SHF climatology
                shf_slice = df_shf[(df_shf.index >= doy_start) & (df_shf.index <= doy_end)].copy()
    
                if shf_slice.empty:
                    continue
    
                # Math: (Cumulative Qnet * Scale) shifted to match T_sample
                shf_slice['proj'] = (shf_slice['Qnet'] * shf_scale).cumsum().to_frame()
                t_adj = shf_slice['proj'].iloc[0] - t_sample
                shf_slice['proj'] = shf_slice['proj'] - t_adj
    
                # Create a row for the final table
                row_data = {"YYYYMMDD": init_date.strftime('%Y%m%d')}
    
                # Map projections back to the correct MMDD columns
                for i, p_row in pd.DataFrame(shf_slice).iterrows():
                    mmdd_key = (dt.datetime(year, 1, 1) + dt.timedelta(days=int(i) - 1)).strftime('%m%d')
                    if mmdd_key in mmdd_cols:
                        row_data[mmdd_key] = p_row['proj']
    
                all_results.append(row_data)

        # 3. Create DataFrame and Write CSV
        if all_results:
            final_df = pd.DataFrame(all_results)
            # Ensure columns are in order: YYYYMMDD then MMDD dates
            ordered_cols = ["YYYYMMDD"] + mmdd_cols
            final_df = final_df.reindex(columns=ordered_cols)

            final_df.to_csv(output_file, index=False)
            print(f"Successfully created: {output_file}")
            final_df.to_csv(output_file.replace('SSTproj','BTMproj'), index=False)
            print(f"Successfully created: {output_file.replace('SSTproj','BTMproj')}")
            logging.info(f"Projected data saved to {output_file} ")
        else:
            logging.warning("No projected data to save.")

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

@staticmethod
def load_region_metadata() -> pd.DataFrame:
    """Reads the ADF&G region definitions from the CSV."""

    try:
        df = pd.read_csv(config.REGIONID_FILE, header=0, index_col='regID')
        return df
    except Exception as e:
        logging.error(f"Failed to load region metadata: {e}")
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
        
    Returns:qq
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
            continue
        #skip any inactive regions for now, but could add a different set of properties for them if desired
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