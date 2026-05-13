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

    logging.info("Calculating SST and BTM Projections...")
    data_processing.generate_projected_data(date_valid=f"{SNAP_DATE_END.split('T')[0].replace('-','')}")

    logging.info("Workflow complete.")

if __name__ == "__main__":
    main()
