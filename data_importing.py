import fastf1 as ff1
from fastf1 import plotting
from fastf1 import utils
import pandas as pd
from typing import Tuple, Dict, List
from fastf1.core import Session

ff1.Cache.enable_cache('/Users/bartosz/Data Projects/f1_analysis/Data/Detailed_Positional_Data_(2018-current)')

def load_session(year: int, event: str, session_type:str) -> Tuple[Session, pd.DataFrame, pd.DataFrame]:
    schedule = ff1.get_event_schedule(year, include_testing=False)
    session = ff1.get_session(year, event, session_type)
    session.load()
    
    quick_laps = session.laps.pick_quicklaps()
    quick_laps["Lap Time (s)"] = quick_laps["LapTime"].dt.total_seconds()
    
    return session, schedule, quick_laps

def get_team_order(quick_laps: pd.DataFrame, fastest_first: bool = True) -> pd.Index:
    return (
    quick_laps[["LapTime", "Team"]]
    .groupby("Team")
    .median()["LapTime"]
    .sort_values(ascending=fastest_first)
    .index
    )

def get_team_color(session: Session, team_order: pd.Index) -> Dict[str, str]:
    return {team: plotting.get_team_color(team, session=session)
                for team in team_order}

def drs_to_boolean(drs_value): #Convert DRS value to boolean
    if drs_value in [10, 12, 14]:
        return True  # DRS is enabled
    else:
        return False  # Every other value is treated as though the DRS is disabled