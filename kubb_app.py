import streamlit as st
import pandas as pd

# Updated Page Title
st.set_page_config(page_title="Steger Ultimate Kubb Invitational", layout="wide")

# --- APP STATE MANAGEMENT ---
if 'teams' not in st.session_state:
    st.session_state.teams = []
if 'matches' not in st.session_state:
    st.session_state.matches = None

# Updated Main Header
st.title("🏆 Steger Ultimate Kubb Invitational Tournament")

# --- STEP 1: TEAM ENTRY ---
with st.sidebar:
    st.header("1. Setup")
    team_input = st.text_area("Enter Team Names (one per line):", height=200)
    if st.button("Generate Balanced Schedule"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 4 or len(teams) % 2 != 0:
            st.error("Please enter an even number of teams (at least 4).")
        else:
            st.session_state.teams = teams
            
            # --- CIRCLE ROTATION SCHEDULER ---
            n = len(teams)
            t_list = list(teams)
            all_possible_rounds = []
            
            for r in range(n - 1):
                round_matches = []
                for i in range(n // 2):
                    t1 = t_list[i]
                    t2 = t_list[n - 1 - i]
                    round_matches.append((t1, t2))
                all_possible_rounds.append(round_matches)
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]

            selected_rounds = all_possible_rounds[:3]
            
            scheduled_data = []
            for r_idx, round_matches in enumerate(selected_rounds):
                for m_idx, (ta, tb) in enumerate(round_matches):
                    time_slot = (r_idx * (n // 2) + m_idx) // 2 + 1
                    court_num = (m_idx % 2) + 1
                    scheduled_data.append({
                        "Time Slot": time_slot,
                        "Court": court_num,
                        "Team A": ta,
                        "Team B": tb,
                        "Winner": None
                    })
            
            st.session_state.matches = pd.DataFrame(scheduled_data)
            st.success(f"Generated balanced schedule for {len(teams)} teams!")

# --- APP TABS ---
tab1, tab2, tab3 = st.tabs(["📅 Schedule & Scoring", "📊 Standings", "🥇 Top 8 Bracket"])

with tab1:
    if st.session_state.matches is not None:
        st.header("Match Schedule")
        df = st.session_state.matches
        for slot, slot_df in df.groupby("Time Slot"):
            st.subheader(f"Round {slot}")
            cols = st.columns(2)
            for i, (idx, row) in enumerate(slot_df.iterrows()):
                with cols[i]:
                    st.write(f"**Court {row['Court']}**")
                    label_a = f"🏆 {row['Team A']}" if row['Winner'] == row['Team A'] else row['Team A']
                    label_b = f"🏆 {row['Team B']}" if row['Winner'] == row['Team B'] else row['Team B']
                    
                    if st.button(f"{label_a}", key=f"a_{idx}"):
                        st.session_state.matches.at[idx, 'Winner'] = row['Team A']
                        st.rerun()
                    st.write("vs")
                    if st.button(f"{label_b}", key=f"b_{idx}"):
                        st.session_state.matches.at[idx, 'Winner'] = row['Team B']
                        st.rerun()
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
        
        standings_df = pd.DataFrame(results).sort_values(by=["W", "L"], ascending=[False, True])
        st.table(standings_df)

with tab3:
    if st.session_state.matches is not None:
        finished = st.session_state.matches['Winner'].notnull().all()
        if not finished:
            st.warning("Finish all preliminary matches to unlock the bracket.")
        else:
            st.header("Top 8 Single Elimination")
            standings = pd.DataFrame(results).sort_values(by="W", ascending=False).head(8)
            top_8 = standings['Team'].tolist()
            
            col1, col2 = st.columns(2)
            qf = [(0,7), (3,4), (1,6), (2,5)]
            for i, (p1, p2) in enumerate(qf):
                with col1 if i < 2 else col2:
                    st.write(f"**Match {i+1}**")
                    st.info(f"{top_8[p1]} vs {top_8[p2]}")
