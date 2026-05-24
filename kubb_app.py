import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Steger Ultimate Kubb Invitational", layout="centered")

# 2. Connection Setup
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        data = conn.read(worksheet="Sheet1", ttl=0)
        return data.dropna(how='all').astype(str)
    except:
        return pd.DataFrame()

def update_sheet(df):
    try:
        df_save = df.astype(str)
        conn.update(worksheet="Sheet1", data=df_save)
        st.cache_data.clear()
        st.toast("✅ Match Updated!")
    except Exception as e:
        st.error(f"Sync failed: {e}")

# --- TITLE ---
st.title("🏆 Steger Ultimate Kubb Invitational")

# 3. Load Data immediately
df = get_data()

# --- SETUP (Shows if Google Sheet is empty) ---
if df.empty or "Team A" not in df.columns:
    st.header("Tournament Setup (1 Court)")
    st.info("Generating 3 rounds of play (18 matches total for 12 teams).")
    team_input = st.text_area("Enter Team Names (one per line):", height=250)
    
    if st.button("🚀 Launch Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 4:
            st.error("Please enter at least 4 teams.")
        else:
            t_list = list(teams)
            # Ensure we have an even number for the rotation math
            if len(t_list) % 2 != 0: 
                t_list.append("BYE")
            
            n = len(t_list)
            all_matches = []
            match_num = 1
            
            # Loop 3 times to ensure 3 games per team
            for r in range(3):
                for i in range(n // 2):
                    ta, tb = t_list[i], t_list[n - 1 - i]
                    # Skip matches involving a BYE so they don't take up court time
                    if ta != "BYE" and tb != "BYE":
                        all_matches.append({
                            "Game": match_num,
                            "Team A": str(ta),
                            "Team B": str(tb),
                            "Winner": "None"
                        })
                        match_num += 1
                # Rotation: keep index 0 fixed, rotate others
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            
            master_df = pd.DataFrame(all_matches)
            update_sheet(master_df)
            st.rerun()

# --- THE MAIN APP ---
else:
    tab1, tab2, tab3 = st.tabs(["📅 Schedule", "📊 Standings", "🥇 Bracket"])
    
    # Force clean data types
    live_df = df.copy()

    with tab1:
        st.write("### Single Court Match List")
        for idx, row in live_df.iterrows():
            with st.container(border=True):
                # Fix: Strip decimal .0 from Match Numbers
                raw_game = str(row['Game']).split('.')[0]
                st.write(f"#### Match {raw_game}")
                
                c1, c2 = st.columns(2)
                ta, tb = str(row['Team A']), str(row['Team B'])
                winner = str(row['Winner'])

                with c1:
                    is_a = (winner == ta)
                    if st.button(f"{'👑 ' if is_a else ''}{ta}", key=f"a_{idx}", use_container_width=True, type="primary" if is_a else "secondary"):
                        live_df.at[idx, 'Winner'] = ta
                        update_sheet(live_df)
                        st.rerun()
                
                with c2:
                    is_b = (winner == tb)
                    if st.button(f"{'👑 ' if is_b else ''}{tb}", key=f"b_{idx}", use_container_width=True, type="primary" if is_b else "secondary"):
                        live_df.at[idx, 'Winner'] = tb
                        update_sheet(live_df)
                        st.rerun()

    with tab2:
        st.header("Current Rankings")
        # Get all team names, excluding BYE and system strings
        raw_teams = pd.unique(live_df[['Team A', 'Team B']].values.ravel())
        teams_only = [t for t in raw_teams if t not in ["BYE", "nan", "None", ""]]
        
        standings_data = []
        for team in teams_only:
            wins = len(live_df[live_df['Winner'] == team])
            standings_data.append({"Team": team, "Wins": wins})
        
        if standings_data:
            standings_df = pd.DataFrame(standings_data).sort_values(by="Wins", ascending=False)
            st.table(standings_df)

    with tab3:
        st.header("Top 8 Championship")
        remaining = len(live_df[live_df['Winner'] == "None"])
        
        if remaining > 0:
            st.warning(f"Championship Bracket will unlock once the final {remaining} matches are completed.")
        else:
            st.balloons()
            standings_df = pd.DataFrame(standings_data).sort_values(by="Wins", ascending=False)
            top_8 = standings_df.head(8)['Team'].tolist()
            
            seeds = [(0,7), (3,4), (1,6), (2,5)]
            for i, (p1, p2) in enumerate(seeds):
                st.success(f"**Match {i+1}:** {top_8[p1]} (1) vs {top_8[p2]} (8)")
