import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Kubb Tournament Manager", layout="wide")

# --- APP STATE MANAGEMENT ---
if 'teams' not in st.session_state:
    st.session_state.teams = []
if 'matches' not in st.session_state:
    st.session_state.matches = None
if 'bracket' not in st.session_state:
    st.session_state.bracket = None

st.title("🏆 Kubb Tournament Manager")

# --- STEP 1: TEAM ENTRY ---
with st.sidebar:
    st.header("1. Setup")
    team_input = st.text_area("Enter Team Names (one per line):", height=200)
    if st.button("Generate Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 8 or len(teams) % 2 != 0:
            st.error("Please enter an even number of teams (at least 8).")
        else:
            st.session_state.teams = teams
            # Create Randomized Schedule (3 games each)
            all_matches = []
            pool = teams * 3
            random.shuffle(pool)
            
            # Simple pairing logic
            temp_pool = list(pool)
            while len(temp_pool) > 1:
                t1 = temp_pool.pop(0)
                for i, t2 in enumerate(temp_pool):
                    if t2 != t1:
                        all_matches.append({"Team A": t1, "Team B": t2, "Winner": None})
                        temp_pool.pop(i)
                        break
            
            # Assign rounds and courts (2 courts)
            scheduled_matches = []
            for i, m in enumerate(all_matches):
                round_num = (i // 2) + 1
                court_num = (i % 2) + 1
                m['Round'] = round_num
                m['Court'] = court_num
                scheduled_matches.append(m)
            
            st.session_state.matches = pd.DataFrame(scheduled_matches)
            st.success(f"Generated {len(teams)} teams and {len(all_matches)} matches!")

# --- APP TABS ---
tab1, tab2, tab3 = st.tabs(["📅 Schedule & Scoring", "📊 Standings", "🥇 Top 8 Bracket"])

with tab1:
    if st.session_state.matches is not None:
        st.header("Match Schedule")
        df = st.session_state.matches
        for idx, row in df.iterrows():
            col1, col2, col3, col4 = st.columns([1, 2, 1, 2])
            with col1: st.write(f"**R{row['Round']} - C{row['Court']}**")
            with col2: 
                if st.button(f"Winner: {row['Team A']}", key=f"a_{idx}"):
                    st.session_state.matches.at[idx, 'Winner'] = row['Team A']
            with col3: st.write("vs")
            with col4:
                if st.button(f"Winner: {row['Team B']}", key=f"b_{idx}"):
                    st.session_state.matches.at[idx, 'Winner'] = row['Team B']
            
            if row['Winner']:
                st.info(f"Result: {row['Winner']} won")
            st.divider()
    else:
        st.info("Enter teams in the sidebar to start.")

with tab2:
    if st.session_state.matches is not None:
        st.header("Current Standings")
        results = []
        for team in st.session_state.teams:
            wins = len(st.session_state.matches[st.session_state.matches['Winner'] == team])
            losses = len(st.session_state.matches[((st.session_state.matches['Team A'] == team) | (st.session_state.matches['Team B'] == team)) & (st.session_state.matches['Winner'].notnull()) & (st.session_state.matches['Winner'] != team)])
            results.append({"Team": team, "W": wins, "L": losses})
        
        standings_df = pd.DataFrame(results).sort_values(by="W", ascending=False)
        st.table(standings_df)

with tab3:
    if st.session_state.matches is not None:
        if st.session_state.matches['Winner'].isnull().any():
            st.warning("Finish all preliminary matches to unlock the bracket.")
        else:
            st.header("Top 8 Single Elimination")
            # Get Top 8
            top_8 = pd.DataFrame(results).sort_values(by="W", ascending=False).head(8)['Team'].tolist()
            
            st.write("### Quarterfinals")
            # 1 vs 8, 4 vs 5, 2 vs 7, 3 vs 6
            qf = [(top_8[0], top_8[7]), (top_8[3], top_8[4]), (top_8[1], top_8[6]), (top_8[2], top_8[5])]
            for i, (ta, tb) in enumerate(qf):
                st.write(f"Match {i+1}: **{ta}** vs **{tb}**")