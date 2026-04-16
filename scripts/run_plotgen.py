# scripts/run_analysis.py
import logging
import folium
import pandas as pd
import urllib.request
import datetime as dt
# 👇 Imports now use the new package name
from kuskokwim_dashboard import config, data_processing, plotting

def main():
    """
    Main script to run the full data fetching, processing, and visualization workflow for the website, does not get ice/sst data.
    """

    logging.info("Generating region images...")
    SNAP_DATE_START = dt.datetime.strftime(dt.datetime.today()-dt.timedelta(days=6),'%Y-%m-%dT09:00:00Z')
    SNAP_DATE_END = dt.datetime.strftime(dt.datetime.today()-dt.timedelta(days=1),'%Y-%m-%dT09:00:00Z')
    sst = data_processing.fetch_sst_data(SNAP_DATE_END, SNAP_DATE_END)

    plotting.matplotlib_region_map(sst.squeeze(),cmap='RdYlBu_r',
                                   label=f'Kuskokwim Surface Temperature {SNAP_DATE_END.split("T")[0]}',
                                   filename=f'{config.OUTPUT_DIR}/SFC_full.png',layer='sfc')
    btm = data_processing.fetch_sst_data(SNAP_DATE_START, SNAP_DATE_END)
    plotting.matplotlib_region_map(btm.mean(dim='time'),cmap='RdYlBu_r',
                                   label='Kuskokwim Bottom Temperature',
                                   filename=f'{config.OUTPUT_DIR}/BTM_full.png',layer='btm') 
    plotting.matplotlib_region_map(sst.squeeze()-btm.mean(dim='time'),minmax=[-2,2],cmap='RdBu_r', 
                                   label='Kuskokwim Temperature Difference (SFC-BTM)',
                                   filename=f'{config.OUTPUT_DIR}/DIFF_full.png',layer='diff')    

    logging.info("Calculating SST and BTM Projections...")
    data_processing.generate_projected_data(date_valid=f"{SNAP_DATE_END.split('T')[0].replace('-','')}")
    
    logging.info("Populate SST and BTM Grid Bubble...")
    grid_df = pd.read_csv(config.REGIONID_FILE)    
    grid_geojson = data_processing.geojson_gridbuilder(grid_df, date_valid=SNAP_DATE_END.split('T')[0].replace('-',''))

    # --- File Output ---
    with open(config.ADFG_GRID_FILE, 'w') as f:
        f.write(grid_geojson)
    logging.info(f"ADFG grid GeoJSON saved to {config.ADFG_GRID_FILE}")

    projected_df = data_processing.combine_projected_data(date_valid=SNAP_DATE_END.split('T')[0].replace('-',''))
    logging.info(f"Combined projected data shape: {projected_df.shape}")
    projected_df.to_csv(config.PROJECTED_DATA_FILE, index=False)

    logging.info("Loading region temperatures...")
    df = data_processing.load_temperature_data('data/kuskokwim_historic_data.csv')
    pdf = data_processing.load_temperature_data('data/kuskokwim_projected_data.csv')
    cdf = data_processing.load_temperature_data('data/kuskokwim_currentyear_data.csv')

    logging.info("Generating region timeseries...")
    # plotting.timeseries_plots(df, pdf)
    plotting.timeseries_plotly_plots(df, cdf, pdf,size='small',offseason=False)
    plotting.timeseries_plotly_plots(df, cdf, pdf,size='large',offseason=False)


    logging.info("Workflow complete.")

if __name__ == "__main__":
    main()
