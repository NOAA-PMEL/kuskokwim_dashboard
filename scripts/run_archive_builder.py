# scripts/run_archive_builder.py
import logging
import pandas as pd
# 👇 Imports now use the new package name
from kuskokwim_dashboard import config, data_processing 

def main():
    """
    Script to build historical data archive from daily data files
    """

    # --- Historic Data ---
    """
    Historic data files have columns
    Year | DOY | RegionID | SST | BOT | ICE 
     - kuskokwim_historic_data.csv is up to 2024 doy 185

     Once a year this needs to be built with the daily files of SST/ICE/BOT

    """

    # --- Current Data ---

    # --- Projected Data ---
    """
    Build a file that has a singular input format like the historic data
    """
    projected_df = data_processing.read_projected_data()
    logging.info(f"Combined projected data shape: {projected_df.shape}")
    projected_df.to_csv(config.PROJECTED_DATA_FILE, index=False)

if __name__ == "__main__":
    main()
