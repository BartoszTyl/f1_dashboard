import streamlit as st
import pandas as pd
import fastf1 as ff1
from datetime import datetime
from data_importing import load_session, get_team_order, get_team_color, drs_to_boolean
import plotting as fsp
import time

from webscrape import get_f1_drivers

# Default wide mode
st.set_page_config(layout="wide")

st.header("🏎️ Formula Stats - Dashboard")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Graphics", "Schedule", "Drivers", "Records"])

# Get the current year
today = datetime.today().year

# Step 1: Choose year
year = st.sidebar.selectbox("Select Year", list(range(2018, today + 1))[::-1])

# Step 2: Get event schedule and choose event
event_schedule = ff1.get_event_schedule(year, include_testing=False)
race_names = event_schedule["EventName"].to_list()

event = st.sidebar.selectbox("Select Event", race_names)
event_time = event_schedule[event_schedule["EventName"] == event]["Session5DateUtc"].iloc[0]

if event_time > datetime.utcnow():
    st.header("Selected Event Didn't Happen Yet!")

    countdown_placeholder = st.empty()

    # This will update the countdown every second until the event time is reached
    while event_time > datetime.utcnow():
        now = datetime.utcnow()
        remaining = event_time - now

        days = remaining.days
        hours, rem = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        countdown_placeholder.text(f'Time left: {days}d {hours:02}h {minutes:02}m {seconds:02}s')
        time.sleep(1)

    # Once the event starts
    countdown_placeholder.text("Event Started!")
else:

    # Step 3: Choose session (FP1, FP2, FP3, Q, R)
    event_info = event_schedule[event_schedule["EventName"] == event].iloc[0]
    session_columns = [f"Session{i}" for i in range(5, 0, -1)]
    available_sessions = [
        session for session in event_info[session_columns].values 
        if isinstance(session, str)
    ]

    session_type = st.sidebar.selectbox("Select Session", available_sessions)

    # Step 4: Load and process session data
    with st.spinner(f"Loading session data for {event} - {session_type}..."):
        session, schedule, quick_laps = load_session(year, event, session_type)
        
        # Convert LapTime to seconds for easier plotting
        quick_laps["LapTime"] = quick_laps["LapTime"].dt.total_seconds()
        
        # Get team order and team colors
        team_order = get_team_order(quick_laps)
        team_colors = get_team_color(session, team_order)

        teams = list(session.laps['Team'].unique())

        fastest_lap_times = {team: [] for team in session.laps['Team'].unique()}
        avg_lap_times = {team: [] for team in session.laps['Team'].unique()}

        for team in teams:
            fastest_lap_times[team] = session.laps.pick_teams(team)['LapTime'].min()
            avg_lap_times[team] = session.laps.pick_teams(team)['LapTime'].mean()

        df_fastest_lap_times = pd.DataFrame.from_dict(fastest_lap_times, orient='index', columns=['Fastest Lap']).reset_index()
        df_avg_lap_times = pd.DataFrame.from_dict(avg_lap_times, orient='index', columns=['Avg Lap']).reset_index()
        df_pace_comparison = pd.merge(df_fastest_lap_times, df_avg_lap_times, on="index")

        df_pace_comparison.columns = ["Team", "Fastest Lap", "Avg Lap"]
        df_pace_comparison["Percentage Diff Fast Lap"] = (((df_pace_comparison['Fastest Lap'] - df_pace_comparison['Fastest Lap'].min()) / df_pace_comparison['Fastest Lap'].min()) * 100).round(2)
        df_pace_comparison["Percentage Diff Avg Lap"] = (((df_pace_comparison['Avg Lap'] - df_pace_comparison['Avg Lap'].min()) / df_pace_comparison['Avg Lap'].min()) * 100).round(2)
        df_pace_comparison['Team Color'] = df_pace_comparison['Team'].apply(lambda team: ff1.plotting.get_team_color(team, session))

        drivers = [driver for driver in session.results['Abbreviation']]



    # Display content inside tabs
    with tab1:
        if event:  # Only show page chooser if event is selected
            page = st.selectbox("Select Graphics",
                                ["Lap Time Distributions",
                                "Pace Comparisons",
                                "Whole Race",
                                "Telemetry"
            ])
            
            if page == "Lap Time Distributions":
                st.subheader("Team Lap Time Distribution")
                st.text(
                    "Graphic represents a box plot of quick laps* grouped by teams. With the avg team lap listed.\n"
                    "\n"
                    "*quick lap - within 107% of the fastest lap in the session" 
                )
                st.pyplot(fsp.add_watermark(fsp.general_lap_time_dist(quick_laps, team_order, team_colors, session)))

                st.subheader("Point Scorers Lap Time Distribution")
                st.pyplot(fsp.add_watermark(fsp.violin_dist_point_scorers(session)))

            elif page == "Pace Comparisons":
                st.subheader("Fastest Lap Team Pace Comparison")
                st.pyplot(fsp.add_watermark(fsp.fastest_lap_team_pace_comparison(df_pace_comparison)))

                st.subheader("Avg Lap Team Pace Comparison")
                st.pyplot(fsp.add_watermark(fsp.avg_lap_team_pace_comparison(df_pace_comparison)))

            elif page == "Whole Race":
                st.subheader("Lap Times Over Entire Race")
                st.pyplot(fsp.add_watermark(fsp.plot_race_lap_times(session), fontsize=110))

            elif page == "Telemetry":
                st.subheader("Lap Telemetry Over Selected Lap")
                driver = st.selectbox("Select Driver:", drivers)
                lap_choice  = st.radio("Choose Lap Option:", ["Fastest Lap", "Specific Lap"])

                if lap_choice == "Specific Lap":
                    lap = st.selectbox("Select Lap:", range(1, int(max(session.laps["LapNumber"])+1)))
                else:
                    lap = session.laps.pick_drivers(driver).pick_fastest()["LapNumber"]
                st.pyplot(fsp.add_watermark(fsp.plot_telemetry(session, driver, lap)))

                st.subheader("Lap Telemetry Comparison")
                col1, col2 = st.columns(2)
                with col1:
                    driver1 = st.selectbox("Select Driver 1:", drivers)
                with col2:
                    driver2 = st.selectbox("Select Driver 2:", [d for d in drivers if d != driver1])
                lap_choice  = st.radio("Choose Lap:", ["Fastest Lap", "Specific Lap"])

                if lap_choice == "Specific Lap":
                    col1, col2 = st.columns(2)
                    with col1:
                        lap_driver_1 = st.selectbox("Select Lap for Driver 1:", range(1, int(max(session.laps["LapNumber"])+1)))
                    with col2:
                        lap_driver_2 = st.selectbox("Select Lap for Driver 2:", range(1, int(max(session.laps["LapNumber"])+1)))
                else:
                    lap_driver_1 = session.laps.pick_drivers(driver1).pick_fastest()["LapNumber"]
                    lap_driver_2 = session.laps.pick_drivers(driver2).pick_fastest()["LapNumber"]
                st.pyplot(fsp.add_watermark(fsp.plot_telemetry_comparison(session, driver1, driver2, lap_driver_1, lap_driver_2)))

    with tab2:
        df_schedule = event_schedule[["EventDate", "Location", "EventName", "EventFormat", "OfficialEventName"]].copy()
        df_schedule = df_schedule.rename(columns={"EventDate":"Event Date", "EventName":"Name", "EventFormat":"Format", "OfficialEventName":"Official Name"})
        df_schedule["Format"] = df_schedule["Format"].apply(lambda x: "Sprint" if x == "sprint_qualifying" else "Conventional")
        st.subheader(f"Event Schedule for the {today} season")
        st.dataframe(df_schedule, hide_index=True)
    
    
    with tab3:
        st.subheader("Formula 1 Driver Statistics")
        df_f1_drivers = get_f1_drivers()
        selected_drivers = st.radio("Select Drivers:", ["Current Drivers", "All Drivers"])
        if selected_drivers == "All Drivers":
            st.dataframe(df_f1_drivers, use_container_width=True, hide_index=True)
        else:
            all_drivers_data = []

            for name in ff1.plotting.list_driver_names(session):
                df_temp = df_f1_drivers[df_f1_drivers["Driver name"] == name]
                all_drivers_data.append(df_temp)

            df_current_drivers = pd.concat(all_drivers_data, ignore_index=True)
            st.dataframe(df_current_drivers, use_container_width=True, hide_index=True)

    with tab4:
        pass