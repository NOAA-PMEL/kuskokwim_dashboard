# scripts/run_build_ADFGgrid.py
import logging
import datetime as dt
import pandas as pd
# 👇 Imports now use the new package name
from kuskokwim_dashboard import config, data_processing

def main():
    """
    Script to build ADFG grid for dashboard.
    """
    # --- ADFG grid defining ---
    grid_df = pd.read_csv(config.REGIONID_FILE)

    
    # --- Data Fetching and Processing ---
    grid_geojson = data_processing.geojson_gridbuilder(grid_df)

    # --- File Output ---
    with open(config.ADFG_GRID_FILE, 'w') as f:
        f.write(grid_geojson)

if __name__ == "__main__":
    main()
