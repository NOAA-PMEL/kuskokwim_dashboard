# scripts/run_analysis.py
import logging
import folium
import urllib.request
import datetime as dt
# 👇 Imports now use the new package name
from kuskokwim_dashboard import config, data_processing, mapping, plotting

def main():
    """
    Main script to run the full data fetching, processing, and visualization workflow.
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
    mapping.add_adfg_grid_layer(m2)
    mapping.add_sst_wms_layer(m2)
    folium.LayerControl().add_to(m2)
    m2.save(config.OUTPUT_DIR / "noaa_folium_map.html")
    logging.info("Getting SST legend image from url.")
    legend_url = mapping.get_sst_legend()
    urllib.request.urlretrieve(legend_url,'images/erddap_legend_sst.png')

    logging.info("Generating region images...")

    logging.info("Loading region temperatures...")
    df = data_processing.load_temperature_data('data/kuskokwim_historic_data.csv')
    pdf = data_processing.load_temperature_data('data/kuskokwim_projected_data.csv')

    logging.info("Generating region timeseries...")
    plotting.timeseries_plots(df, pdf)
    plotting.timeseries_plotly_plots(df, pdf)

# # TODO: implement loop over new data format for ice, sst and bottom temp
#     logging.info("Loading region temperatures...")
#     station_info = pd.read_csv(config.REGIONID_FILE)

#     for _i, station in station_info.iterrows():
#         df = data_processing.load_temperature_data('data/{station}_SST.csv')
#         pdf = data_processing.load_temperature_data('data/kuskokwim_projected_data.csv')

#         logging.info("Generating region timeseries...")
#         plotting.timeseries_plots(df, pdf)
#         plotting.timeseries_plotly_plots(df, pdf)

    logging.info("Workflow complete.")

if __name__ == "__main__":
    main()
