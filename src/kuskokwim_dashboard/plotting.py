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


# --- HELPER FUNCTIONS ---
def to_date(yearday_series):
    """Maps Yearday (1-365) to a fixed leap year (2020)."""
    return pd.to_datetime(yearday_series - 1, unit='D', origin='2020-01-01')

def c_to_f(c_val):
    """Converts Celsius to Fahrenheit."""
    return (c_val * 9/5) + 32

def get_padded_range(series_list, padding=0.05):
    """Calculates min/max across multiple series with padding."""
    combined = pd.concat(series_list)
    y_min = combined.min()
    y_max = combined.max()
    
    if pd.isna(y_min) or pd.isna(y_max):
        return [0, 1]
        
    span = y_max - y_min
    if span == 0: span = 1
    
    return [y_min - (span * padding), y_max + (span * padding)]

def timeseries_plotly_plots(df: pd.DataFrame, pdf: pd.DataFrame) -> None:
    """Generates plotly timeseries plots for each ADFG region."""
    reg_df = {reg_id:df[df.RegionID.astype(str)==reg_id] for reg_id in config.ADFG_REGIONS}
    reg_pred_df = {reg_id:pdf[pdf.RegionID.astype(str)==reg_id] for reg_id in config.ADFG_REGIONS}

    for reg_id in config.ADFG_REGIONS:
        # 1. Setup Subplots with Dual Axis Specs
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            specs=[
                [{"secondary_y": True}],  # Row 1: SST
                [{"secondary_y": True}],  # Row 2: BOT
                [{"secondary_y": False}],  # Row 3: ICE (Single axis)
                [{"secondary_y": False}]  # Row 4: prediction stats
            ]
        )

        # --- ROW 1: SST (Black) ---
        # 1A. Historical (Celsius)
        for year, groups in reg_df[reg_id].groupby('Year'):
            fig.add_trace(
                go.Scatter(
                    x=to_date(groups.Yearday), 
                    y=groups.SST,
                    mode='lines',
                    line=dict(color='black', width=1),
                    opacity=0.25,
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=1, col=1, secondary_y=False
            )
        
        # 1B. Prediction (Celsius)
        fig.add_trace(
            go.Scatter(
                x=to_date(reg_pred_df[reg_id].Yearday),
                y=reg_pred_df[reg_id].SST,
                mode='lines',
                line=dict(color='black', width=1.5),
                name='SST Pred'
            ),
            row=1, col=1, secondary_y=False
        )

        # --- ROW 2: BOT (Red) ---
        # 2A. Historical (Celsius)
        for year, groups in reg_df[reg_id].groupby('Year'):
            fig.add_trace(
                go.Scatter(
                    x=to_date(groups.Yearday),
                    y=groups.BOT,
                    mode='lines',
                    line=dict(color='red', width=1),
                    opacity=0.25,
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=2, col=1, secondary_y=False
            )
            
        # 2B. Prediction (Celsius)
        fig.add_trace(
            go.Scatter(
                x=to_date(reg_pred_df[reg_id].Yearday),
                y=reg_pred_df[reg_id].BOT,
                mode='lines',
                line=dict(color='red', width=1.5),
                name='BOT Pred'
            ),
            row=2, col=1, secondary_y=False
        )

        # --- ROW 3: ICE (Blue) - Single Axis ---
        ice_climo = reg_df[reg_id].groupby('Yearday')['ICE'].median().reset_index()
        ice_climo.columns = [0, 1] 

        fig.add_trace(
            go.Scatter(
                x=to_date(ice_climo[0]),
                y=ice_climo[1],
                mode='lines', 
                fill='tozeroy', 
                line=dict(width=0), 
                fillcolor='rgba(0, 0, 255, 0.25)', 
                showlegend=False,
                hoverinfo='skip'
            ),
            row=3, col=1, secondary_y=False
        )

        fig.add_trace(
            go.Scatter(
                x=to_date(reg_pred_df[reg_id].Yearday),
                y=reg_pred_df[reg_id].ICE,
                mode='lines',
                line=dict(color='blue', width=1.5),
                name='ICE Pred'
            ),
            row=3, col=1, secondary_y=False
        )

        # --- ROW 4: Prediction analysis - Single Axis ---
        ice_climo = reg_df[reg_id].groupby('Yearday')['ICE'].median().reset_index()
        ice_climo.columns = [0, 1] 

        fig.add_trace(
            go.Scatter(
                x=to_date(ice_climo[0]),
                y=ice_climo[1] * 0,
                mode='lines', 
                fill='tozeroy', 
                line=dict(color='black', width=0.5), 
                showlegend=False,
                hoverinfo='skip'
            ),
            row=4, col=1, secondary_y=False
        )

        fig.add_trace(
            go.Scatter(
                x=to_date(reg_pred_df[reg_id].Yearday),
                y=reg_pred_df[reg_id].ICE *0,
                mode='lines',
                line=dict(color='black', width=1.5),
                name='Accuracy Est.'
            ),
            row=4, col=1, secondary_y=False
        )

        # --- RANGE CALCULATIONS & DUMMY TRACES ---
        # To force the secondary axis to show, we add an invisible trace 
        # with the calculated Fahrenheit range.
        
        # SST Ranges
        sst_c_range = get_padded_range([reg_df[reg_id].SST, reg_pred_df[reg_id].SST])
        sst_f_range = [c_to_f(x) for x in sst_c_range]
        
        # Add Invisible Dummy Trace for SST Fahrenheit
        fig.add_trace(
            go.Scatter(
                x=[to_date(pd.Series([1])), to_date(pd.Series([1]))], # Just arbitrary x points
                y=sst_f_range, # The Min/Max F values
                mode='markers',
                marker=dict(opacity=0), # Invisible
                showlegend=False,
                hoverinfo='skip'
            ),
            row=1, col=1, secondary_y=True
        )

        # BOT Ranges
        bot_c_range = get_padded_range([reg_df[reg_id].BOT, reg_pred_df[reg_id].BOT])
        bot_f_range = [c_to_f(x) for x in bot_c_range]

        # Add Invisible Dummy Trace for BOT Fahrenheit
        fig.add_trace(
            go.Scatter(
                x=[to_date(pd.Series([1])), to_date(pd.Series([1]))],
                y=bot_f_range,
                mode='markers',
                marker=dict(opacity=0), # Invisible
                showlegend=False,
                hoverinfo='skip'
            ),
            row=2, col=1, secondary_y=True
        )

        # --- LAYOUT UPDATES ---
        
        # Apply Ranges
        # Row 1
        fig.update_yaxes(title_text="SST<br>(°C)", range=sst_c_range, row=1, col=1, secondary_y=False)
        fig.update_yaxes(title_text="SST<br>(°F)", range=sst_f_range, row=1, col=1, secondary_y=True, showgrid=False)
        
        # Row 2
        fig.update_yaxes(title_text="BOT<br>(°C)", range=bot_c_range, row=2, col=1, secondary_y=False)
        fig.update_yaxes(title_text="BOT<br>(°F)", range=bot_f_range, row=2, col=1, secondary_y=True, showgrid=False)
        
        # Row 3
        fig.update_yaxes(title_text="ICE", row=3, col=1, secondary_y=False)

        # Row 4
        fig.update_yaxes(title_text="ACCURACY<br>EST.", row=4, col=1, secondary_y=False)

        fig.update_layout(
            height=600, 
            width=800,
            title_text=f"Region: {reg_id}",
            template="simple_white", 
            margin=dict(t=50, b=50, l=60, r=60), # Right margin space for 2nd axis
            showlegend=True, 
            legend=dict(
                x=1.25,            # Far right
                y=0.01,            # Far bottom
                xanchor="right",   # Anchor the right edge of the box to x
                yanchor="bottom",  # Anchor the bottom edge of the box to y
                bgcolor="rgba(255, 255, 255, 0.8)", # Semi-transparent white background
                bordercolor="Black",
                borderwidth=1
            ),
        )

        # X-Axis Month-Day Format
        fig.update_xaxes(tickformat="%b %d")
        
        # Spine Management
        fig.update_xaxes(showline=False, row=1, col=1) 
        fig.update_xaxes(showline=False, row=2, col=1) 
        fig.update_xaxes(showline=False, row=3, col=1) 
        fig.update_xaxes(showline=True,  row=4, col=1) 

        # fig.show()
        fig.write_html(f"{config.OUTPUT_DIR}/{reg_id}.plotly.html")
