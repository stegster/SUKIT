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
        # Convert all to string to prevent decimal .0 issues and TypeErrors
        df_save = df.astype(str)
        conn.update(worksheet="Sheet1", data=df_save)
        st.cache_data.clear() 
        st.toast("✅ Sync Successful")
    except Exception as e:
        st.error(f"Sync failed: {e}")

st.title("🏆 Steger Ultimate Kubb Invitational")

# Load data first to prevent NameErrors
df = get_data()

# --- SETUP PHASE ---
if df.empty or "Team A" not in df.columns:
    st.header("Tournament Setup")
    team_input = st.text_area("Enter Team Names (one per line):", height=250)
    
    if st.button("🚀 Launch Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        
        if len(teams) < 4:
            st.error("Please enter at least 4 teams.")
        else:
            t_list = list(teams)
            if len(t_list) % 2 != 0:
                t_list.append("BYE")
            
            n = len(t_list)
            matches = []
            
            # Generate 3 rounds of rotation
            for r in range(3):
                for i in range(n // 2):
                    ta = t_list[i]
                    tb = t_list[n - 1 - i]
                    
                    if ta != "BYE" and tb != "BYE":
                        matches.append({
                            "Game": len(matches) + 1,
                            "Team A": ta,
                            "Team B": tb,
                            "Winner": "None"
                        })
                
                # Standard Circle Rotation
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            
            new_df = pd.DataFrame(matches).astype(str)
            update_sheet(new_df)
            st.rerun()

# --- LIVE APP PHASE ---
else:
    tab1, tab2, tab3 = st.tabs(["📅 Schedule", "📊 Standings", "🥇 Bracket"])
    
    live_df = df.copy()

    with tab1:
        st.write(f"### {len(live_df)} Matches Scheduled")
        
        for idx, row in live_df.iterrows():
            # Force clean integer display for Match numbers
            clean_num = str(row['Game']).split('.')[0]
            
            with st.container(border=True):
                st.write(f"#### Match {clean_num}")
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
        st.header("Rankings")
        raw_teams = pd.unique(live_df[['Team A', 'Team B']].values.ravel())
        teams_only = [t for t in raw_teams if t not in ["BYE", "nan", "None", ""]]
        
        standings_data = []
        for t in teams_only:
            wins = len(live_df[live_df['Winner'] == t])
            played = len(live_df[((live_df['Team A'] == t) | (live_df['Team B'] == t)) & (live_df['Winner'] != "None")])
            losses = played - wins
            
            standings_data
