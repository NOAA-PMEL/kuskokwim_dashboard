# arctic_ice_forecaster/plotting.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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


# Assuming adfg_regions, reg_df, and reg_pred_df are defined in your environment

def timeseries_plotly_plots(df: pd.DataFrame, pdf: pd.DataFrame) -> None:
    """Generates plotly timeseries plots for each ADFG region."""
    reg_df = {reg_id:df[df.RegionID.astype(str)==reg_id] for reg_id in config.ADFG_REGIONS}
    reg_pred_df = {reg_id:pdf[pdf.RegionID.astype(str)==reg_id] for reg_id in config.ADFG_REGIONS}

    for reg_id in config.ADFG_REGIONS:
        # Create subplots: 3 rows, 1 column, shared x-axis
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,  # Adjust closer to 0 to mimic tight layout
        )

        # --- Subplot 1: SST (Black) ---
        # Plot historical years (Light Black lines)
        # We iterate through the groups just like the original code
        for year, groups in reg_df[reg_id].groupby('Year'):
            fig.add_trace(
                go.Scatter(
                    x=groups.Yearday, 
                    y=groups.SST,
                    mode='lines',
                    line=dict(color='black', width=1),
                    opacity=0.25,
                    showlegend=False,
                    hoverinfo='skip'  # Optional: skip hover for background noise
                ),
                row=1, col=1
            )
        
        # Plot Prediction (Solid Black line)
        fig.add_trace(
            go.Scatter(
                x=reg_pred_df[reg_id].Yearday, 
                y=reg_pred_df[reg_id].SST,
                mode='lines',
                line=dict(color='black', width=1.5),
                name='SST Pred'
            ),
            row=1, col=1
        )

        # --- Subplot 2: BOT (Red) ---
        # Plot historical years
        for year, groups in reg_df[reg_id].groupby('Year'):
            fig.add_trace(
                go.Scatter(
                    x=groups.Yearday, 
                    y=groups.BOT,
                    mode='lines',
                    line=dict(color='red', width=1),
                    opacity=0.25,
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=2, col=1
            )
            
        # Plot Prediction
        fig.add_trace(
            go.Scatter(
                x=reg_pred_df[reg_id].Yearday, 
                y=reg_pred_df[reg_id].BOT,
                mode='lines',
                line=dict(color='red', width=1.5),
                name='BOT Pred'
            ),
            row=2, col=1
        )

        # --- Subplot 3: ICE (Blue) ---
        # Calculate Median ICE (Optimized pandas version of your loop)
        # This replaces the slow for-loop concat block
        ice_climo = reg_df[reg_id].groupby('Yearday')['ICE'].median().reset_index()
        ice_climo.columns = [0, 1] # Matching your original column index access

        # Fill Between (Blue Area)
        fig.add_trace(
            go.Scatter(
                x=ice_climo[0], 
                y=ice_climo[1],
                mode='lines', # Use lines with fill
                fill='tozeroy', # Fills from line down to 0
                line=dict(width=0), # Hide the top line boundary if desired
                fillcolor='rgba(0, 0, 255, 0.25)', # Blue with alpha 0.25
                showlegend=False,
                hoverinfo='skip'
            ),
            row=3, col=1
        )

        # Plot Prediction
        fig.add_trace(
            go.Scatter(
                x=reg_pred_df[reg_id].Yearday, 
                y=reg_pred_df[reg_id].ICE,
                mode='lines',
                line=dict(color='blue', width=1.5),
                name='ICE Pred'
            ),
            row=3, col=1
        )

        # --- Subplot 4: Statistics ---
        # Calculate Median ICE (Optimized pandas version of your loop)

        # Fill Between (Blue Area)
        for year, groups in reg_df[reg_id].groupby('Year'):
            fig.add_trace(
                go.Scatter(
                    x=groups.Yearday, 
                    y=groups.BOT *0,
                    mode='lines',
                    line=dict(color='black', width=1),
                    opacity=0.25,
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=2, col=1
            )
            
        # Plot Prediction
        fig.add_trace(
            go.Scatter(
                x=reg_pred_df[reg_id].Yearday, 
                y=reg_pred_df[reg_id].BOT *0,
                mode='lines',
                line=dict(color='black', width=1.5),
                name='Probability'
            ),
            row=4, col=1
        )

        # --- Layout & Spines ---
        fig.update_layout(
            height=300, # figsize=(7,3) ~ 700x300 pixels
            width=700,
            title_text=f"ADFG Statistical Region: {reg_id}",
            template="simple_white", # Clean background like matplotlib
            margin=dict(t=40, b=40, l=40, r=40),
            showlegend=False, # Set to True if you want the legend for the bold lines

            # --- TRANSPARENCY SETTINGS ---
            # paper_bgcolor='rgba(0,0,0,0)', # Makes the outer margin area transparent
            # plot_bgcolor='rgba(0,0,0,0)'   # Makes the inner plotting area transparent
        )

        # Mimic spine removal (Removing bottom borders for top plots)
        # In Plotly 'simple_white', axes have lines. We turn them off.
        fig.update_xaxes(showline=False, row=1, col=1) # ax[0] bottom hidden
        fig.update_xaxes(showline=False, row=2, col=1) # ax[1] bottom hidden
        fig.update_xaxes(showline=False,  row=3, col=1) # ax[2] bottom visible
        fig.update_xaxes(showline=True,  row=4, col=1) # ax[3] bottom visible

        # Export commands
        fig.write_html(f"{config.OUTPUT_DIR}/{reg_id}.plotly.html")
