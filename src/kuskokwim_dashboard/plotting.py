# arctic_ice_forecaster/plotting.py
import calendar
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import xarray as xr
import matplotlib as mpl
from matplotlib import pyplot as plt 
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from . import config, data_processing

def matplotlib_region_map(sst_data: pd.DataFrame, minmax: list = [-1, 9], cmap: str = 'RdYlBu_r', label: str = '', filename: str = 'default.png', layer: str = 'sfc') -> None:
    """Generates region map of sst/btmp with cartopy and saves to images directory."""

    regions_df = data_processing.load_region_metadata()

    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.Miller())

    # Set Map Extent
    ax.set_extent([-168, -158, 55, 60.5], crs=ccrs.PlateCarree())
    title = f"{label}"

    # Plot SST Data
    mesh = sst_data.plot.pcolormesh(
        ax=ax, transform=ccrs.PlateCarree(),
        cmap=cmap, vmin=minmax[0], vmax=minmax[1], add_colorbar=False
    )

    xdf = xr.load_dataset(config.GEBCO_BATHY)

    if layer != 'sfc':
        bathymesh = xdf.where(xdf.elevation < -27).elevation.plot.pcolormesh(
            ax=ax, transform=ccrs.PlateCarree(), add_colorbar=False, cmap=mpl.colors.ListedColormap(['white','darkgrey'])
        )
    
    #  Add Features (Coastline and Bathymetry Contours)
    ax.add_feature(cfeature.GSHHSFeature(scale='high', levels=[1], facecolor='lightgray'))

    # Add Colorbar
    cbar = plt.colorbar(mesh, orientation='horizontal', pad=0.05, shrink=0.7)
    cbar.set_label('Temperature (°C)', fontsize=14)

    plt.title(title, fontsize=14 + 2)

    if layer != 'sfc':
        fig.text(
            0.5,
            0.5,
            'bottom temperatures currently \n unavailable for depths >15 fathoms',
            ha='center',
            va='bottom',
            fontsize=14,
            color='black'
        )

    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {config.IMAGE_DIR}/{filename}")
    
def timeseries_plots(df: pd.DataFrame, pdf: pd.DataFrame) -> None:
    """Generates timeseries plots for each ADFG region."""

    grid_df = pd.read_csv(config.REGIONID_FILE)
    grid_df = grid_df[grid_df['active'] == 'y']
    ADFG_REGIONS = []
    for _, row in grid_df.iterrows():
        ADFG_REGIONS.append(row.regID.split('_')[1])

    reg_df = {reg_id:df[df.RegionID.astype(str)==reg_id] for reg_id in ADFG_REGIONS}
    reg_pred_df = {reg_id:pdf[pdf.RegionID.astype(str)==reg_id] for reg_id in ADFG_REGIONS}

    for reg_id in ADFG_REGIONS:
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
        # ax[2].plot(reg_pred_df[reg_id].Yearday,reg_pred_df[reg_id].ICE,'b')
        
        ax[0].spines[['bottom']].set_visible(False)
        ax[1].spines[['bottom','top']].set_visible(False)
        ax[2].spines[['top']].set_visible(False)
        
        fig.savefig(f'{config.IMAGE_DIR}/{reg_id}.image.png')


# --- HELPER FUNCTIONS ---
def to_date(yearday_series):
    """Maps Yearday (1-365/366) to current year.

    Uses the local current year so plots are shown in the active year context.
    If current year is not leap and yearday==366, it clamps to 365.
    """
    current_year = datetime.datetime.now().year
    yearday = pd.Series(yearday_series).astype(int)

    if not calendar.isleap(current_year):
        yearday = yearday.clip(upper=365)

    return pd.to_datetime(yearday - 1, unit='D', origin=f'{current_year}-01-01')

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
    if span == 0: 
        span = 1
    
    return [y_min - (span * padding), y_max + (span * padding)]

def timeseries_plotly_plots(reg_df: pd.DataFrame, act_df: pd.DataFrame, pred_df: pd.DataFrame, size: str='large', offseason: bool=False) -> None:
    """Generates plotly timeseries plots for each ADFG region.

    If size='small', generates compact plots.
    If size='large', generates detailed plots with secondary axes and legends.
    
    """

    if size == 'small':
        width, height = 400, 400
        pname = 'plotly.html'
    elif size == 'medium':
        width, height = 400, 600
        pname = 'plotly.medium.html'
    else:
        width, height = 400, 800
        pname = 'plotly.large.html'

    today = datetime.datetime.now()

    grid_df = pd.read_csv(config.REGIONID_FILE)
    grid_df = grid_df[grid_df['active'] == 'y']
    for _, row in grid_df.iterrows():
        reg_id = row.regID.split('_')[1]
        climo_df = reg_df.groupby('RegionID').get_group(int(reg_id))
        actual_df = act_df.groupby('RegionID').get_group(int(reg_id))
        try:
            predicted_df = pred_df.groupby('RegionID').get_group(int(reg_id))
            prediction = True
        except KeyError:
            print(f"Predicted data for region {reg_id} empty.")
            prediction = False
            predicted_df = climo_df[climo_df['Year']==2020]
            predicted_df.loc[:,'SST'] = -1.8
            predicted_df.loc[:,'BOT'] = -1.8
        # 1. Setup Subplots with Dual Axis Specs

        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            specs=[
                [{"secondary_y": True}],  # Row 1: SST
                [{"secondary_y": True}],  # Row 2: BOT
                [{"secondary_y": False}],  # Row 3: ICE (Single axis)
                # [{"secondary_y": False}]  # Row 4: prediction stats
            ]
        )

        # --- ROW 1: SST (Black) ---
        # 1A. Historical (Celsius)
        for year, groups in climo_df.groupby('Year'):
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
        
        if prediction:
            fig.add_trace(
                go.Scatter(
                    x=to_date(predicted_df['Yearday']),
                    y=predicted_df['SST'],
                    mode='lines',
                    line=dict(color='black', width=1.5, dash='dash'),
                    name='SST Pred'
                ),
                row=1, col=1, secondary_y=False
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=to_date(predicted_df.Yearday), 
                    y=predicted_df.SST,
                    mode='lines',
                    line=dict(color='black', width=1.5, dash='dash'),
                    name='SST Pred <br>(Ice Present)'
                ),
                row=1, col=1, secondary_y=False
            )

        fig.add_trace(
            go.Scatter(
                x=to_date(actual_df['Yearday']),
                y=actual_df['SST'],
                mode='lines',
                line=dict(color='black', width=1.5),
                name='SST JPL Obs'
            ),
            row=1, col=1, secondary_y=False
        )

        # 1C. Actual (Celsius)
        # fig.add_trace(
        #     go.Scatter(
        #         x=to_date(actual_df['Yearday']),
        #         y=actual_df['SST'],
        #         mode='lines',
        #         line=dict(color='green', width=1.5),
        #         name='SST Act',
        #         showlegend=False,
        #     ),
        #     row=1, col=1, secondary_y=False
        # )    
        
        # --- ROW 2: BOT (Red) ---
        # 2A. Historical (Celsius)
        for year, groups in climo_df.groupby('Year'):
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
        if prediction:
            fig.add_trace(
                go.Scatter(
                    x=to_date(predicted_df['Yearday']),
                    y=predicted_df['BOT'],
                    mode='lines',
                    line=dict(color='red', width=1.5, dash='dash'),
                name='BOT Pred'
                ),
                row=2, col=1, secondary_y=False
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=to_date(predicted_df.Yearday), 
                    y=predicted_df.BOT,
                    mode='lines',
                    line=dict(color='red', width=1.5, dash='dash'),
                    name='BOT Pred <br>(Ice Present)'
                ),
                row=2, col=1, secondary_y=False
            )
        # --- ROW 3: ICE (Blue) - Single Axis ---
        ice_climo = climo_df.groupby('Yearday')['ICE'].median().reset_index()
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


        # for year, groups in climo_df.groupby('Year'):
        #     if year == today.timetuple().tm_year:
        #         fig.add_trace(
        #             go.Scatter(
        #                 x=to_date(groups.Yearday),
        #                 y=groups.ICE,
        #                 mode='lines',
        #                 line=dict(color='blue', width=1.5),
        #                 showlegend=False,
        #                 hoverinfo='skip'
        #             ),
        #             row=3, col=1, secondary_y=False
        #         )
                
        # --- ROW 4: Prediction analysis - Single Axis ---
        # ice_climo = reg_df[reg_id].groupby('Yearday')['ICE'].median().reset_index()
        # ice_climo.columns = [0, 1] 

        # fig.add_trace(
        #     go.Scatter(
        #         x=to_date(ice_climo[0]),
        #         y=ice_climo[1] * 0,
        #         mode='lines', 
        #         fill='tozeroy', 
        #         line=dict(color='black', width=0.5), 
        #         showlegend=False,
        #         hoverinfo='skip'
        #     ),
        #     row=4, col=1, secondary_y=False
        # )

        # fig.add_trace(
        #     go.Scatter(
        #         x=to_date(actual_df['Yearday']),
        #         y=(actual_df['SST']*0),
        #         mode='lines',
        #         line=dict(color='black', width=1.5),
        #         name='Accuracy Est.'
        #     ),
        #     row=4, col=1, secondary_y=False
        # )

        # --- RANGE CALCULATIONS & DUMMY TRACES ---
        # To force the secondary axis to show, we add an invisible trace 
        # with the calculated Fahrenheit range.
        
        # SST Ranges
        sst_c_range = get_padded_range([climo_df.SST, climo_df.SST])
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
        bot_c_range = get_padded_range([climo_df.BOT, climo_df.BOT])
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

        # -- Add Vlines --
        today_date = to_date(pd.Series([today.timetuple().tm_yday])).iloc[0]
        fig.add_vline(x=today_date, line_width=3, line_dash="dash", line_color="grey")


        # --- LAYOUT UPDATES ---
        
        # Apply Ranges
        # Row 1
        fig.update_yaxes(title_text="SST<br>(°C)", range=sst_c_range, row=1, col=1, secondary_y=False)
        fig.update_yaxes(title_text="SST<br>(°F)", range=sst_f_range, row=1, col=1, secondary_y=True, showgrid=False)
        
        # Row 2
        fig.update_yaxes(title_text="Bottom<br>(°C)", range=bot_c_range, row=2, col=1, secondary_y=False)
        fig.update_yaxes(title_text="Bottom<br>(°F)", range=bot_f_range, row=2, col=1, secondary_y=True, showgrid=False)
        
        # Row 3
        fig.update_yaxes(title_text="Ice", row=3, col=1, secondary_y=False)

        # Row 4
        # fig.update_yaxes(title_text="Error<br>(°C).", row=4, col=1, secondary_y=False)

        fig.update_layout(
            height=height, 
            width=width,
            title_text=f"Region: {reg_id}",
            template="simple_white", 
            margin=dict(t=50, b=50, l=60, r=60), # Right margin space for 2nd axis
            showlegend=True, 
            legend=dict(
                x=1.75,            # Far right
                y=0.01,            # Far bottom
                xanchor="right",   # Anchor the right edge of the box to x
                yanchor="bottom",  # Anchor the bottom edge of the box to y
                bgcolor="rgba(255, 255, 255, 0.8)", # Semi-transparent white background
                bordercolor="Black",
                borderwidth=1
            ),
        )
           

    
        # X-Axis Month-Day Format
        if offseason:
            fig.update_xaxes(range=[f"{today.strftime('%Y')}-01-01", 
                                    f"{today.strftime('%Y')}-12-31"])            
            fig.update_xaxes(tickformat="%b %d")
        else:
            fig.update_xaxes(range=[f"{today.strftime('%Y')}-03-01", 
                                    f"{today.strftime('%Y')}-07-01"])            
            fig.update_xaxes(tickformat="%b %d")
        
        # Spine Management
        fig.update_xaxes(showline=False, row=1, col=1) 
        fig.update_xaxes(showline=False, row=2, col=1) 
        fig.update_xaxes(showline=True, row=3, col=1) 
        # fig.update_xaxes(showline=True,  row=4, col=1) 
        fig.show()

        # fig.show()
        fig.write_html(f"{config.OUTPUT_DIR}/{reg_id}.{pname}")
