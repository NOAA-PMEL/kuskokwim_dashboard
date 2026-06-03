# scripts/run_archive_builder.py
import logging
import datetime as dt

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
    current_year_df = data_processing.combine_past_years(data_type='SST')
    current_year_df.to_csv(config.CURRENT_YEAR_DATA_FILE, index=False)
    logging.info(f"Combined current year data shape: {current_year_df.shape}")

    current_year_df = data_processing.combine_past_years(data_type='BOT')
    current_year_df.to_csv(config.CURRENT_YEAR_DATA_BOTTOM_FILE, index=False)
    logging.info(f"Combined current year data shape: {current_year_df.shape}")

    # current_year_df = data_processing.combine_current_ice_data()
    # current_year_df.to_csv(config.CURRENT_YEAR_DATA_ICE_FILE, index=False)
    # logging.info(f"Combined current year data shape: {current_year_df.shape}")

    # --- Projected Data ---
    """
    Build a file that has a singular input format like the historic data
    """
    SNAP_DATE_END = dt.datetime.strftime(dt.datetime.today()-dt.timedelta(days=1),'%Y%m%d')
    projected_df = data_processing.combine_projected_data(SNAP_DATE_END)
    logging.info(f"Combined projected data shape: {projected_df.shape}")
    projected_df.to_csv(config.PROJECTED_DATA_FILE, index=False)

if __name__ == "__main__":
    main()
