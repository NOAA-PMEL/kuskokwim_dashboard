# scripts/run_analysis.py
import logging
import folium
import pandas as pd
import urllib.request
import datetime as dt
# 👇 Imports now use the new package name
from kuskokwim_dashboard import data_processing

def main():
    """
    Main script to run the full data fetching, processing, and visualization workflow for the website, does not get ice/sst data.
    """
    SNAP_DATE_END = '2026-04-15'

    data_processing.generate_projected_data(date_valid=f"{SNAP_DATE_END.split('T')[0].replace('-','')}")


if __name__ == "__main__":
    main()
