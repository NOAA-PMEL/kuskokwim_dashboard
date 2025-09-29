# scripts/run_analysis.py
import logging
import folium
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

    # --- Generate Maps ---
    logging.info("Generating 'footprint.html' map...")
    m1 = mapping.create_base_map()
    mapping.add_ice_concentration_layer(m1, gdf_conc_360.drop(columns=['idp_filedate','idp_ingestdate']))
    mapping.add_ice_prediction_layer(m1, gdf_pred_360.drop(columns=['idp_filedate','idp_ingestdate']))
    mapping.add_adfg_grid_layer(m1)
    mapping.add_gebco_contours_layer(m1)
    mapping.add_mooring_marker(m1)
    folium.LayerControl().add_to(m1)
    m1.save(config.OUTPUT_DIR / "footprint.html")

    logging.info("Generating region images...")

    logging.info("Workflow complete.")
    df = data_processing.load_temperature_data('data/kuskokwim_historic_data.csv')
    pdf = data_processing.load_temperature_data('data/kuskokwim_projected_data.csv')

    plotting.timeseries_plots(df, pdf)

if __name__ == "__main__":
    main()
