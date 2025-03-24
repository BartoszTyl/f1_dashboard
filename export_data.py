from fastf1 import get_session
import fastf1
import time

fastf1.Cache.enable_cache('/Users/bartosz/Data Projects/f1_analysis/Data/Detailed_Positional_Data_(2018-current)')

years = [2025]
sessions = ['FP1', 'FP2', 'FP3', 'Q', 'R', 'S', 'SQ', 'SS']

for year in years:
    print(f"📅 Loading schedule for {year}...")
    retries = 3
    for attempt in range(retries):
        try:
            schedule = fastf1.get_event_schedule(year)
            break
        except ValueError as e:
            print(f"⚠️ Attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5)
            else:
                print(f"❌ Skipping year {year} due to repeated failures.")
                continue

    for _, event in schedule.iterrows():
        event_name = event['EventName']
        for session in sessions:
            try:
                sess = get_session(year, event_name, session)

                # ✅ Check if session already cached by testing laps data
                try:
                    sess.laps  # Access laps to trigger minimal load from cache
                    print(f"⏭️ Skipped {year} {event_name} {session} (already cached)")
                    continue
                except Exception:
                    # If laps not available, we proceed to load the session
                    pass

                sess.load()  # Downloads and caches data if not cached
                print(f"✅ Downloaded {year} {event_name} {session}")

            except Exception as e:
                print(f"⚠️ Skipped {year} {event_name} {session}: {e}")
