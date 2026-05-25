import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# 1. Page Configuration
st.set_page_config(page_title="Steger Ultimate Kubb Invitational", layout="centered")

# 2. Connection Setup
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        data = conn.read(worksheet="Sheet1", ttl=0)
        if data is not None and not data.empty:
            df = data.dropna(how='all').astype(str)
            return df.apply(lambda x: x.str.strip())
    except:
        pass
    return pd.DataFrame()

def update_sheet(df):
    try:
        df_save = df.astype(str)
        conn.update(worksheet="Sheet1", data=df_save)
        st.cache_data.clear() 
        st.toast("✅ Update Synced")
    except Exception as e:
        st.error(f"Sync failed: {e}")

st.title("🏆 Steger Ultimate Kubb Invitational")

# --- PERSISTENCE LATCH ---
# This prevents the app from "forgetting" it's in a tournament during slow syncs
if "tournament_active" not in st.session_state:
    st.session_state.tournament_active = False

with st.spinner("Syncing Scoreboard..."):
    df = get_data()

# If the sheet has data, lock the session into active mode
if not df.empty and "Team A" in df.columns:
    st.session_state.tournament_active = True

# --- SETUP PHASE ---
if not st.session_state.tournament_active:
    st.header("Tournament Setup")
    team_input = st.text_area("Enter Team Names (one per line):", height=250)
    
    if st.button("🚀 Launch Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 4:
            st.error("Please enter at least 4 teams.")
        else:
            t_list = list(teams)
            if len(t_list) % 2 != 0: t_list.append("BYE")
            
            n = len(t_list)
            matches = []
            for r in range(3):
                for i in range(n // 2):
                    ta, tb = t_list[i], t_list[n - 1 - i]
                    if ta != "BYE" and tb != "BYE":
                        matches.append({
                            "Type": "Prelim",
                            "Game": str(len(matches) + 1),
                            "Team A": ta,
                            "Team B": tb,
                            "Winner": "None"
                        })
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            
            new_df = pd.DataFrame(matches).astype(str)
            update_sheet(new_df)
            st.session_state.tournament_active = True
            time.sleep(1) # Give Google time to write
            st.rerun()

# --- LIVE APP PHASE ---
else:
    # Backup: If the sync returned empty mid-tournament, wait and retry instead of showing Setup
    if df.empty:
        st.warning("🔄 Re-syncing with Court... one moment.")
        time.sleep(1)
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📅 Prelims", "📊 Leaderboard", "🥇 Bracket"])
    
    # 1. STANDINGS LOGIC (With SoS Tiebreaker)
    prelims = df[df['Type'] == 'Prelim']
    all_teams = pd.unique(prelims[['Team A', 'Team B']].values.ravel())
    all_teams = [t for t in all_teams if t not in ["BYE", "nan", "None", ""]]
    
    standings_list = []
    for t in all_teams:
        wins = len(prelims[prelims['Winner'] == t])
        played = len(prelims[((prelims['Team A'] == t) | (prelims['Team B'] == t)) & (prelims['Winner'] != "None")])
        opponents = prelims[prelims['Team A'] == t]['Team B'].tolist() + prelims[prelims['Team B'] == t]['Team A'].tolist()
        # SoS: Combined wins of every team you played
        sos = sum([len(prelims[prelims['Winner'] == opp]) for opp in opponents if opp != "BYE"])
        
        standings_list.append({
            "Team": t, 
            "Wins": wins, 
            "Losses": played - wins, 
            "SoS": sos,
            "GP": played
        })
    
    standings_df = pd.DataFrame(standings_list).sort_values(by=["Wins", "SoS", "Losses"], ascending=[False, False, True])

    # 2. PRELIMS TAB
    with tab1:
        st.write(f"### {len(prelims)} Scheduled Matches")
        for idx, row in prelims.iterrows():
            clean_num = row['Game'].split('.')[0]
            with st.container(border=True):
                st.write(f"#### Match {clean_num}")
                c1, c2 = st.columns(2)
                ta, tb = row['Team A'], row['Team B']
                winner = row['Winner']

                with c1:
                    is_a = (winner == ta)
                    if st.button(f"{'👑 ' if is_a else ''}{ta}", key=f"a_{idx}", use_container_width=True, type="primary" if is_a else "secondary"):
                        df.at[idx, 'Winner'] = ta
                        update_sheet(df); st.rerun()
                with c2:
                    is_b = (winner == tb)
                    if st.button(f"{'👑 ' if is_b else ''}{tb}", key=f"b_{idx}", use_container_width=True, type="primary" if is_b else "secondary"):
                        df.at[idx, 'Winner'] = tb
                        update_sheet(df); st.rerun()

    # 3. LEADERBOARD TAB
    with tab2:
        st.subheader("Leaderboard")
        st.caption("Tiebreaker: Strength of Schedule (Total wins of opponents played)")
        st.table(standings_df)

    # 4. BRACKET TAB
    with tab3:
        st.header("Top 8 Championship")
        p_remaining = (prelims['Winner'] == "None").sum()
        
        if p_remaining > 0:
            st.warning(f"Championship Bracket will unlock once the final {p_remaining} matches are completed.")
            st.info("Current Projected Seeds (1-8):")
            st.write(", ".join(standings_df.head(8)['Team'].tolist()))
        else:
            st.balloons()
            st.success("Preliminary Rounds Complete!")
            top_8 = standings_df.head(8)['Team'].tolist()
            
            st.write("### Quarterfinal Matchups")
            seeds = [(0,7), (3,4), (1,6), (2,5)]
            for i, (p1, p2) in enumerate(seeds):
                with st.container(border=True):
                    st.write(f"**Match {i+1}**")
                    st.write(f"{top_8[p1]} (Seed {p1+1}) vs {top_8[p2]} (Seed {p2+1})")
