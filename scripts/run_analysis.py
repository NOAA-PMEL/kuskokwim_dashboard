# scripts/run_analysis.py
import logging
import folium
import pandas as pd
import urllib.request
import datetime as dt
# 👇 Imports now use the new package name
from kuskokwim_dashboard import config, data_processing, mapping, plotting

def main():
    """
    Main script to run the full data fetching, processing, and visualization workflow for the website, does not get ice/sst data.
    """
    # --- Setup ---
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    config.IMAGE_DIR.mkdir(exist_ok=True)
    
    # --- Data Fetching and Processing ---
    gdf_conc, gdf_pred = data_processing.fetch_ice_data()
    gdf_conc_360 = data_processing.reproject_to_360(gdf_conc)
    gdf_pred_360 = data_processing.reproject_to_360(gdf_pred)

    # --- Output Dates ---
    latest_conc_date = gdf_conc['idp_filedate'].max().strftime('%Y-%m-%d')
    latest_pred_date = gdf_pred['idp_filedate'].max().strftime('%Y-%m-%d')
    logging.info(f"Latest Ice Concentration Date: {latest_conc_date}")
    logging.info(f"Latest Ice Prediction Date: {latest_pred_date}")
    with open(f"{config.OUTPUT_DIR}/lastrun.txt", "w") as f:
        print(f"Latest Ice Concentration Date: {latest_conc_date}", file=f)
        print(f"Latest Ice Prediction Date: {latest_pred_date}", file=f)
        print(f"Dashboard Updated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}", file=f)

    logging.info("Generating region images...")
    SNAP_DATE_START = dt.datetime.strftime(dt.datetime.today()-dt.timedelta(days=6),'%Y-%m-%dT09:00:00Z')
    SNAP_DATE_END = dt.datetime.strftime(dt.datetime.today()-dt.timedelta(days=1),'%Y-%m-%dT09:00:00Z')
    sst = data_processing.fetch_sst_data(SNAP_DATE_END, SNAP_DATE_END)
    plotting.matplotlib_region_map(sst.squeeze(),cmap='RdYlBu_r',
                                   label=f'Kuskokwim Surface Temperature {SNAP_DATE_END.split("T")[0]}',
                                   filename=f'{config.OUTPUT_DIR}/SFC_full.png')
    btm = data_processing.fetch_sst_data(SNAP_DATE_START, SNAP_DATE_END)
    plotting.matplotlib_region_map(btm.mean(dim='time'),cmap='RdYlBu_r',
                                   label='Kuskokwim Bottom Temperature',
                                   filename=f'{config.OUTPUT_DIR}/BTM_full.png') 
    plotting.matplotlib_region_map(sst.squeeze()-btm.mean(dim='time'),minmax=[-2,2],cmap='RdBu_r', 
                                   label='Kuskokwim Temperature Difference (SFC-BTM)',
                                   filename=f'{config.OUTPUT_DIR}/DIFF_full.png')    

    logging.info("Calculating SST and BTM Projections...")
    data_processing.generate_projected_data(date_valid=f"{SNAP_DATE_END.split('T')[0].replace('-','')}")
    
    logging.info("Populate SST and BTM Grid Bubble...")
    grid_df = pd.read_csv(config.REGIONID_FILE)    
    grid_geojson = data_processing.geojson_gridbuilder(grid_df, date_valid=SNAP_DATE_END.split('T')[0].replace('-',''))

    # --- File Output ---
    with open(config.ADFG_GRID_FILE, 'w') as f:
        f.write(grid_geojson)
    logging.info(f"ADFG grid GeoJSON saved to {config.ADFG_GRID_FILE}")

    # --- Generate Maps ---
    logging.info("Generating 'footprint.html' map...")
    m1 = mapping.create_base_map(crs="EPSG3857", tiles="cartodb positron")
    mapping.add_ice_concentration_layer(m1, gdf_conc_360.drop(columns=['idp_filedate','idp_ingestdate']))
    mapping.add_ice_prediction_layer(m1, gdf_pred_360.drop(columns=['idp_filedate','idp_ingestdate']))
    mapping.add_gebco_contours_layer(m1)
    mapping.add_mooring_marker(m1)
    mapping.add_adfg_grid_layer(m1)
    folium.LayerControl().add_to(m1)
    m1.save(config.OUTPUT_DIR / "footprint.html")

    logging.info("Generating 'noaa_folium_map.html' map...")
    m2 = mapping.create_base_map(crs="EPSG4326")
    mapping.add_ice_concentration_layer(m2, gdf_conc_360.drop(columns=['idp_filedate','idp_ingestdate']))
    mapping.add_ice_prediction_layer(m2, gdf_pred_360.drop(columns=['idp_filedate','idp_ingestdate']))
    mapping.add_sst_wms_layer(m2)
    mapping.add_adfg_grid_layer(m2, popup_on=False)
    folium.LayerControl().add_to(m2)
    m2.save(config.OUTPUT_DIR / "noaa_folium_map.html")
    logging.info("Getting SST legend image from url.")
    legend_url = mapping.get_sst_legend()
    urllib.request.urlretrieve(legend_url,'images/erddap_legend_sst.png')
    logging.info(f"URL for erddap legend: {legend_url}")



    logging.info("Loading region temperatures...")
    df = data_processing.load_temperature_data('data/kuskokwim_historic_data.csv')
    pdf = data_processing.load_temperature_data('data/kuskokwim_projected_data.csv')

    logging.info("Generating region timeseries...")
    plotting.timeseries_plots(df, pdf)
    plotting.timeseries_plotly_plots(df, pdf,size='small',offseason=False)
    plotting.timeseries_plotly_plots(df, pdf,size='large',offseason=True)

    logging.info("Workflow complete.")

if __name__ == "__main__":
    main()
