import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="Steger Ultimate Kubb Invitational", layout="wide")

# 2. Connect to the "Shared Brain" (Google Sheets)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # Pulls the current state of the tournament
    return conn.read(ttl=0)

def update_sheet(df):
    # Pushes the new results back to the shared sheet
    conn.update(worksheet="Sheet1", data=df)
    st.cache_data.clear()

st.title("🏆 Steger Ultimate Kubb Invitational")

# 3. Load existing data or create empty
try:
    df = get_data()
except Exception:
    df = pd.DataFrame()

# --- TAB 0: SETUP (Only shows if no teams exist yet) ---
if df.empty or "Team A" not in df.columns:
    st.header("Tournament Setup")
    team_input = st.text_area("Enter Team Names (one per line):", height=200)
    
    if st.button("🚀 Launch Tournament for Everyone"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 4 or len(teams) % 2 != 0:
            st.error("Please enter an even number of teams.")
        else:
            # --- CIRCLE ROTATION SCHEDULER ---
            n = len(teams)
            t_list = list(teams)
            all_rounds = []
            for r in range(n - 1):
                round_m = []
                for i in range(n // 2):
                    round_m.append((t_list[i], t_list[n - 1 - i]))
                all_rounds.append(round_m)
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]

            # Build the master dataframe
            init_data = []
            for r_idx, m_list in enumerate(all_rounds[:3]):
                for m_idx, (ta, tb) in enumerate(m_list):
                    time_slot = (r_idx * (n // 2) + m_idx) // 2 + 1
                    court_num = (m_idx % 2) + 1
                    init_data.append({
                        "Time Slot": int(time_slot),
                        "Court": int(court_num),
                        "Team A": ta,
                        "Team B": tb,
                        "Winner": "None"
                    })
            
            master_df = pd.DataFrame(init_data)
            update_sheet(master_df)
            st.rerun()

# --- THE MAIN APP (Shows once setup is done) ---
else:
    tab1, tab2, tab3 = st.tabs(["📅 Live Schedule", "📊 Standings", "🥇 Top 8 Bracket"])

    with tab1:
        st.info("Tap a team name to record a win. All players see updates live.")
        # Filter out empty rows if Google Sheets adds them
        display_df = df.dropna(subset=["Team A"])
        
        for slot, slot_df in display_df.groupby("Time Slot"):
            st.subheader(f"Round {int(slot)}")
            cols = st.columns(2)
            for i, (idx, row) in enumerate(slot_df.iterrows()):
                with cols[i]:
                    st.write(f"**Court {int(row['Court'])}**")
                    
                    # Team A Button
                    label_a = f"🏆 {row['Team A']}" if row['Winner'] == row['Team A'] else row['Team A']
                    if st.button(label_a, key=f"a_{idx}"):
                        df.at[idx, 'Winner'] = row['Team A']
                        update_sheet(df)
                        st.rerun()
                    
                    st.write("vs")
                    
                    # Team B Button
                    label_b = f"🏆 {row['Team B']}" if row['Winner'] == row['Team B'] else row['Team B']
                    if st.button(label_b, key=f"b_{idx}"):
                        df.at[idx, 'Winner'] = row['Team B']
                        update_sheet(df)
                        st.rerun()
            st.divider()

    with tab2:
        st.header("Current Rankings")
        # Extract all team names
        all_teams = pd.unique(display_df[['Team A', 'Team B']].values.ravel())
        standings = []
        for team in all_teams:
            wins = len(display_df[display_df['Winner'] == team])
            losses = len(display_df[((display_df['Team A'] == team) | (display_df['Team B'] == team)) & 
                                   (display_df['Winner'] != "None") & (display_df['Winner'] != team)])
            standings.append({"Team": team, "Wins": wins, "Losses": losses})
        
        standings_df = pd.DataFrame(standings).sort_values(by=["Wins", "Losses"], ascending=[False, True])
        st.table(standings_df)

    with tab3:
        finished = (display_df['Winner'] == "None").sum() == 0
        if not finished:
            st.warning("The Bracket will unlock once all Preliminary rounds are complete.")
        else:
            st.header("Top 8 Championship")
            top_8 = pd.DataFrame(standings).sort_values(by="Wins", ascending=False).head(8)['Team'].tolist()
            
            seeds = [(0,7), (3,4), (1,6), (2,5)]
            for i, (p1, p2) in enumerate(seeds):
                st.info(f"Match {i+1}: **{top_8[p1]}** vs **{top_8[p2]}**")
