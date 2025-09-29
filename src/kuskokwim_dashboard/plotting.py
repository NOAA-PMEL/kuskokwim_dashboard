import datetime as dt
import pandas as pd
from matplotlib import pyplot as plt 
from . import config

def timeseries_plots(df: pd.DataFrame, pdf: pd.DataFrame) -> None:
    """Generates timeseries plots for each ADFG region."""
    reg_df = {reg_id:df[df.RegionID.astype(str)==reg_id] for reg_id in config.ADFG_REGIONS}
    reg_pred_df = {reg_id:pdf[pdf.RegionID.astype(str)==reg_id] for reg_id in config.ADFG_REGIONS}

    for reg_id in config.ADFG_REGIONS:
        fig, ax = plt.subplots(nrows=3, ncols=1,figsize=(7,3), sharex=True)
        
        for year,groups in reg_df[reg_id].groupby('Year'):
            ax[0].plot(groups.Yearday,groups.SST,'k',alpha=.25)
            ax[0].plot(reg_pred_df[reg_id].Yearday,reg_pred_df[reg_id].SST,'k')
        
            ax[1].plot(groups.Yearday,groups.BOT,'r',alpha=.25)
            ax[1].plot(reg_pred_df[reg_id].Yearday,reg_pred_df[reg_id].BOT,'r')
        
        ice_climo = pd.DataFrame()
        for doy,groups in reg_df[reg_id].groupby('Yearday'):
            ice_climo = pd.concat([ice_climo,pd.DataFrame([[doy,groups.ICE.median()]])])
        
        ax[2].fill_between(ice_climo[0],ice_climo[1],color='b',alpha=.25)
        ax[2].plot(reg_pred_df[reg_id].Yearday,reg_pred_df[reg_id].ICE,'b')
        
        ax[0].spines[['bottom']].set_visible(False)
        ax[1].spines[['bottom','top']].set_visible(False)
        ax[2].spines[['top']].set_visible(False)
        
        fig.savefig(f'{config.IMAGE_DIR}/{reg_id}.image.png')