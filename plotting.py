import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import matplotlib.gridspec as gridspec
import matplotlib.cm as cm
import seaborn as sns
import numpy as np
import pandas as pd
import streamlit as st
import fastf1 as ff1
from data_importing import drs_to_boolean

plt.style.use('dark_background')

#Supporting functions
def format_lap_time(seconds: float) -> str:
    # Ensure that seconds is a float
    if isinstance(seconds, pd.Timedelta):
        seconds = seconds.total_seconds()
    elif not isinstance(seconds, (int, float)):
        raise ValueError("Expected seconds to be a number or Timedelta")

    minutes = int(seconds // 60)
    seconds = seconds % 60
    milliseconds = int((seconds % 1) * 1000)
    return f"{minutes:01}:{int(seconds):02}.{milliseconds:03}"


def add_watermark(fig, watermark_text: str = "Formula Stats", alpha=0.3, fontsize=90, rotation=30):
    fig.text(
        0.5, 0.5,
        watermark_text,
        fontsize=fontsize,
        color='gray',
        alpha=alpha,
        ha='center',
        va='center',
        weight='bold',
        rotation=rotation,
        transform=fig.transFigure
    )
    return fig




# General Lap Time Distribution
def general_lap_time_dist(
        quick_laps: pd.DataFrame,
        team_order: pd.Index,
        team_colours: dict, session) -> plt.Figure:
    
    fig, ax = plt.subplots(figsize=(15, 10))

    sns.boxplot(
        data=quick_laps,
        x="Team",
        y="Lap Time (s)",
        hue="Team",
        order=team_order,
        palette=team_colours,
        whiskerprops=dict(color="white"),
        boxprops=dict(edgecolor="white"),
        medianprops=dict(color="grey"),
        capprops=dict(color="white"),
        flierprops=dict(marker='o', markerfacecolor='lightgrey', markersize=5, linestyle='none'),
        width=0.6,
        dodge=False
    )

    # Create custom tick labels (team name and average lap time)
    avg_lap_times = quick_laps.groupby('Team')['LapTime'].median()  # You could use a different aggregation here
    tick_labels = [f"{team} \n {format_lap_time(avg_lap_time)}" for team, avg_lap_time in zip(team_order, avg_lap_times)]

    # Set custom x-ticks with rotation and labels
    plt.xticks(
        ticks=np.arange(len(team_order)),  # Position of the ticks
        labels=tick_labels,  # The custom tick labels
        rotation=45,  # Rotate the labels for better visibility
    )

    # Set plot title
    plt.title(f"Team Lap Time Distribution | {session.event.year} - {session.event.EventName} - {session.name}")
    plt.grid(visible=False)
    ax.set(xlabel=None)

    return fig



def violin_dist_point_scorers(session) -> plt.Figure:
    point_finishers = session.drivers[:10]
    driver_laps = session.laps.pick_drivers(point_finishers).pick_quicklaps().reset_index()
    finishing_order = session.results['Abbreviation'][:10]
    
    
    fig, ax = plt.subplots(figsize=(15, 10))

    driver_laps["LapTime(s)"] = driver_laps["LapTime"].dt.total_seconds()

    sns.violinplot(data=driver_laps,
                    x="Driver",
                    y="LapTime(s)",
                    hue="Driver",
                    inner=None,
                    scale="width",
                    density_norm="area",
                    order=finishing_order,
                    dodge=False,
                    palette=ff1.plotting.get_driver_color_mapping(session=session),
                    ax=ax
                    )

    sns.swarmplot(data=driver_laps,
                x="Driver",
                y="LapTime(s)",
                order=finishing_order,
                hue="Compound",
                palette=ff1.plotting.get_compound_mapping(session=session),
                hue_order=["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"],
                dodge=False,
                linewidth=1,
                edgecolor='black',
                size=4,
                ax=ax
                )

    ax.set_xlabel("Driver")
    ax.set_ylabel("Lap Time (s)")
    plt.title(f"Point Scorers Lap Time Distribution | {session.event.year} - {session.event.EventName} - {session.name}")
    sns.despine(left=True, bottom=True)

    handles, labels = ax.get_legend_handles_labels()
    unique_labels = list(set(labels))

    compound_handles = [handles[i] for i, label in enumerate(labels) if label in ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]]
    legend2 = ax.legend(compound_handles, ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"], title='Tire Compound', loc='lower right', bbox_to_anchor=(1, 0))
    ax.add_artist(legend2)

    return fig



def fastest_lap_team_pace_comparison(df_pace_comparison: pd.DataFrame) -> plt.Figure:
    
    df_pace_comparison.sort_values("Percentage Diff Fast Lap", inplace=True)

    fig, ax = plt.subplots(figsize=(15, 6))

    ax.bar(df_pace_comparison['Team'], df_pace_comparison['Percentage Diff Fast Lap'], color=df_pace_comparison['Team Color'])

    ax.set_ylabel('Percentage Difference from Fastest Lap (%)')
    ax.set_xlabel('Team & Time (s)')
    ax.set_title('Fastest Lap Team Pace Comparison')

    # Rotate team names for better readability with formatted lap times
    tick_labels = [
        f"{team} \n {format_lap_time(avg_team_lap)}"
        for team, avg_team_lap in zip(df_pace_comparison['Team'], df_pace_comparison['Fastest Lap'])
    ]
    
    ax.set_xticks(np.arange(len(df_pace_comparison)))
    ax.set_xticklabels(tick_labels, rotation=45)

    ax.set_ylim(df_pace_comparison['Percentage Diff Fast Lap'].max()+1, 0)

    for index, value in enumerate(df_pace_comparison['Percentage Diff Fast Lap']):
        ax.text(index, value + 0.1, f"+{value:.2f}%", ha='center', va='top')

    return fig



def avg_lap_team_pace_comparison(df_pace_comparison: pd.DataFrame) -> plt.Figure:
    df_pace_comparison.sort_values('Percentage Diff Avg Lap', inplace=True)

    fig, ax = plt.subplots(figsize=(15, 6))

    ax.bar(df_pace_comparison['Team'], df_pace_comparison['Percentage Diff Avg Lap'], color=df_pace_comparison['Team Color'])

    ax.set_ylabel('Percentage Difference (%)')
    ax.set_xlabel('Team & Time (s)')
    ax.set_title('Avg Lap Team Pace Comparison')

    # Format x-ticks with team name and average lap time using format_lap_time
    tick_labels = [f"{team} \n {format_lap_time(avg_team_lap)}" for team, avg_team_lap in zip(df_pace_comparison['Team'], df_pace_comparison['Avg Lap'])]
    ax.set_xticks(np.arange(len(df_pace_comparison)))
    ax.set_xticklabels(tick_labels, rotation=45)

    ax.set_ylim(df_pace_comparison['Percentage Diff Avg Lap'].max() + 1, 0)

    for index, value in enumerate(df_pace_comparison['Percentage Diff Avg Lap']):
        ax.text(index, value + 0.1, f"+{value:.2f}%", ha='center', va='top')

    return fig

def plot_race_lap_times(session) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(15, 10))

    # Loop through each driver in the session
    for driver_number in session.drivers:
        driver_laps = session.laps.pick_driver(driver_number)

        lap_times_seconds = driver_laps['LapTime'].dt.total_seconds()
        lap_numbers = driver_laps['LapNumber']
        driver_abbr = driver_laps.iloc[0]['Driver']

        ax.plot(lap_numbers, lap_times_seconds, label=driver_abbr)

    ax.set_xlabel('Lap Number')
    ax.set_ylabel('Lap Time (s)')
    ax.set_xticks(range(1, int(max(session.laps["LapNumber"])+1)))
    ax.set_title(f'Lap Times - {session.event["EventName"]} {session.event.year}')
    ax.legend(title='Drivers', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle="--", color='darkgrey', linewidth=0.5)
    fig.tight_layout()

    return fig



def plot_telemetry(session, driver_1: str, lap: int) -> plt.Figure:
    team_color = ff1.plotting.get_driver_color(driver_1, session)
    
    telemetry = session.laps.pick_drivers(driver_1).pick_laps(lap).get_telemetry().add_distance()
    telemetry["DRS bool"] = telemetry["DRS"].apply(drs_to_boolean)
    telemetry


    fig, ax = plt.subplots(6, figsize = [10,10], gridspec_kw={'height_ratios': [3, 2, 1, 1, 2, 1]}, constrained_layout=False)
    # Speed trace
    ax[0].plot(telemetry["Distance"], telemetry["Speed"], label=driver_1, color=team_color)
    ax[0].set_ylabel('Speed (km/h)', color='white')
    ax[0].legend(loc="lower right")
    ax[0].set_yticks([350, 300, 250, 200, 150, 100, 50, 0])
    ax[0].yaxis.grid(color='#3E4041', linestyle='--', linewidth=1)
    
    # Throttle Trace
    ax[1].plot(telemetry["Distance"], telemetry["Throttle"], label=driver_1, color=team_color)
    ax[1].set_ylabel('Throttle (%)', color='white')

    # Brake Trace
    ax[2].plot(telemetry["Distance"], telemetry["Brake"], label=driver_1, color=team_color)
    ax[2].set_ylabel('Brake', color='white')
    ax[2].set_yticks([0, 1])
    ax[2].set_yticklabels(['OFF', 'ON'])

    # Gear Trace
    ax[3].plot(telemetry["Distance"], telemetry["nGear"], label=driver_1, color=team_color)
    ax[3].set_ylabel('Gear', color='white')
    ax[3].set_yticks([2, 4, 6, 8])
    ax[3].set_ylim([1, 9])
    ax[3].yaxis.grid(color='#3E4041', linestyle='--', linewidth=1)

    # RPM Trace
    ax[4].plot(telemetry["Distance"], telemetry["RPM"], label=driver_1, color=team_color)
    ax[4].set_ylabel('RPM', color='white')

    # DRS Trace
    ax[5].plot(telemetry["Distance"], telemetry["DRS bool"], label=driver_1, color=team_color)
    ax[5].set_ylabel('DRS', color='white')
    ax[5].set_xlabel('Lap distance (meters)', color='white')
    ax[5].set_yticks([False, True])
    ax[5].set_yticklabels(['OFF', 'ON'])


    fig.suptitle(f"{session.event.year} {session.event.EventName} - {session.name}", fontsize=16, color='white', y=0.93)
    fig.text(0.5, 0.89, f"Lap telemetry | {driver_1} ({format_lap_time(session.laps.pick_driver(driver_1).pick_lap(lap)['LapTime'].iloc[0])})", ha='center', fontsize=10)


    
    return fig

def plot_telemetry_comparison(session, driver_1: str, driver_2: str, lap_driver_1: int, lap_driver_2: int) -> plt.Figure:

    team_color_driver_1 = ff1.plotting.get_driver_color(driver_1, session)
    team_color_driver_2 = ff1.plotting.get_driver_color(driver_2, session)
    
    telemetry_driver_1 = session.laps.pick_drivers(driver_1).pick_laps(lap_driver_1).get_telemetry().add_distance()
    telemetry_driver_1["DRS bool"] = telemetry_driver_1["DRS"].apply(drs_to_boolean)

    telemetry_driver_2 = session.laps.pick_drivers(driver_2).pick_laps(lap_driver_2).get_telemetry().add_distance()
    telemetry_driver_2["DRS bool"] = telemetry_driver_2["DRS"].apply(drs_to_boolean)
    


    fig, ax = plt.subplots(6, figsize = [10,10], gridspec_kw={'height_ratios': [3, 2, 1, 1, 2, 1]}, constrained_layout=False)
    # Speed trace
    ax[0].plot(telemetry_driver_1["Distance"], telemetry_driver_1["Speed"], label=driver_1, color=team_color_driver_1)
    ax[0].plot(telemetry_driver_2["Distance"], telemetry_driver_2["Speed"], label=driver_2, color=team_color_driver_2, linestyle='--')
    ax[0].set_ylabel('Speed (km/h)', color='white')
    ax[0].legend(loc="lower right")
    ax[0].set_yticks([350, 300, 250, 200, 150, 100, 50, 0])
    ax[0].yaxis.grid(color='#3E4041', linestyle='--', linewidth=1)
    
    # Throttle Trace
    ax[1].plot(telemetry_driver_1["Distance"], telemetry_driver_1["Throttle"], label=driver_1, color=team_color_driver_1)
    ax[1].plot(telemetry_driver_2["Distance"], telemetry_driver_2["Throttle"], label=driver_2, color=team_color_driver_2, linestyle='--')
    ax[1].set_ylabel('Throttle (%)', color='white')

    # Brake Trace
    ax[2].plot(telemetry_driver_1["Distance"], telemetry_driver_1["Brake"], label=driver_1, color=team_color_driver_1)
    ax[2].plot(telemetry_driver_2["Distance"], telemetry_driver_2["Brake"], label=driver_2, color=team_color_driver_2, linestyle='--')
    ax[2].set_ylabel('Brake', color='white')
    ax[2].set_yticks([0, 1])
    ax[2].set_yticklabels(['OFF', 'ON'])

    # Gear Trace
    ax[3].plot(telemetry_driver_1["Distance"], telemetry_driver_1["nGear"], label=driver_1, color=team_color_driver_1)
    ax[3].plot(telemetry_driver_2["Distance"], telemetry_driver_2["nGear"], label=driver_2, color=team_color_driver_2, linestyle='--')
    ax[3].set_ylabel('Gear', color='white')
    ax[3].set_yticks([2, 4, 6, 8])
    ax[3].set_ylim([1, 9])
    ax[3].yaxis.grid(color='#3E4041', linestyle='--', linewidth=1)

    # RPM Trace
    ax[4].plot(telemetry_driver_1["Distance"], telemetry_driver_1["RPM"], label=driver_1, color=team_color_driver_1)
    ax[4].plot(telemetry_driver_2["Distance"], telemetry_driver_2["RPM"], label=driver_2, color=team_color_driver_2, linestyle='--')
    ax[4].set_ylabel('RPM', color='white')

    # DRS Trace
    ax[5].plot(telemetry_driver_1["Distance"], telemetry_driver_1["DRS bool"], label=driver_1, color=team_color_driver_1)
    ax[5].plot(telemetry_driver_2["Distance"], telemetry_driver_2["DRS bool"], label=driver_2, color=team_color_driver_2, linestyle='--')
    ax[5].set_ylabel('DRS', color='white')
    ax[5].set_xlabel('Lap distance (meters)', color='white')
    ax[5].set_yticks([False, True])
    ax[5].set_yticklabels(['OFF', 'ON'])


    fig.suptitle(f"{session.event.year} {session.event.EventName} - {session.name}", fontsize=16, color='white', y=0.93)
    fig.text(0.5, 0.89, f"Lap telemetry | {driver_1} ({format_lap_time(session.laps.pick_driver(driver_1).pick_lap(lap_driver_1)['LapTime'].iloc[0])}) vs {driver_2} ({format_lap_time(session.laps.pick_driver(driver_1).pick_lap(lap_driver_2)['LapTime'].iloc[0])})", ha='center', fontsize=10)

    
    return fig