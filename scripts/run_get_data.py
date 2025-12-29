# scripts/run_analysis.py
import logging
import datetime as dt
import pandas as pd
# 👇 Imports now use the new package name
from kuskokwim_dashboard import config, data_processing

def main():
    """
    Main script to just the data request.
    """
    # --- Setup ---
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    config.IMAGE_DIR.mkdir(exist_ok=True)
    
    # --- Data Fetching and Processing ---
    gdf_conc, gdf_pred = data_processing.fetch_ice_data()

    # --- Output Dates ---
    latest_conc_date = gdf_conc['idp_filedate'].max().strftime('%Y-%m-%d')
    latest_pred_date = gdf_pred['idp_filedate'].max().strftime('%Y-%m-%d')
    logging.info(f"Latest Ice Concentration Date: {latest_conc_date}")
    logging.info(f"Latest Ice Prediction Date: {latest_pred_date}")
    with open(f"{config.OUTPUT_DIR}/lastrun.txt", "w") as f:
        print(f"Latest Ice Concentration Date: {latest_conc_date}", file=f)
        print(f"Latest Ice Prediction Date: {latest_pred_date}", file=f)
        print(f"Dashboard Updated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}", file=f)

    logging.info("Obtaining SST Values and Statistics...")
    # iday = 0
    for iday in range(0,5,1):
        for _i, rows in pd.read_csv(config.REGIONID_FILE).iterrows():
            sat_sst_time = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1+iday)).strftime('%Y-%m-%dT00:00:00Z')
            if iday ==0:
                filedate = sat_sst_time.split('T')[0].replace('-','')
            try:
                _idf, mean_wice, mean_woice, sst_date = data_processing.jplsst_getter(rows['regID'],config.NOAA_SST_URL,sat_sst_time)
            except Exception as e:
                logging.error(f"Error obtaining SST data for {rows['regID']} on {sat_sst_time}: {e}")
                continue

            print(rows['regID'], mean_wice['time'].str.split('T')[0][0].replace('-',''),mean_wice['analysed_sst (degree_C)'].values[0])
            with open(f'{config.DATA_DIR}/{rows['regID']}_SST_{filedate}.csv', "a") as f:
                if iday == 0:
                    print('Time', 'SST', file = f, sep = ',')
                print(mean_woice['time'].str.split('T')[0][0].replace('-',''),
                    mean_woice['analysed_sst (degree_C)'].values[0], file = f, sep = ',')

    logging.info("Calculating Ice Flag Predictions...")
    for _i, rows in pd.read_csv(config.REGIONID_FILE).iterrows():
        _idf, mean_wice, mean_woice, sst_date = data_processing.jplsst_getter(rows['regID'],config.NOAA_SST_URL,sat_sst_time)
        df = pd.DataFrame()
        df['coords'] = list(zip(mean_wice['longitude (degrees_east)'],mean_wice['latitude (degrees_north)']))
        
        ice_flag = data_processing.ASIP_Prediction(df,gdf_pred)
        with open(f'{config.DATA_DIR}/{rows['regID']}_ICEproj_{gdf_conc['idp_filedate'].iloc[0].strftime("%Y%m%d")}.csv', "w") as f:
            print('Time', 'ICE', file = f, sep = ',')
            print(gdf_conc['idp_filedate'].iloc[0].strftime("%Y%m%d"), ice_flag, file = f, sep = ',')

    logging.info("Workflow complete.")

if __name__ == "__main__":
    main()
