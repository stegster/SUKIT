import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

st.set_page_config(page_title="Steger Ultimate Kubb Invitational", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        data = conn.read(worksheet="Sheet1", ttl=0)
        if data is not None and not data.empty:
            return data.dropna(how='all').astype(str).apply(lambda x: x.str.strip())
    except:
        pass
    return pd.DataFrame()

def update_sheet(df):
    try:
        conn.update(worksheet="Sheet1", data=df.astype(str))
        st.cache_data.clear()
        st.toast("✅ Match Recorded")
    except Exception as e:
        st.error(f"Sync failed: {e}")

st.title("🏆 Steger Ultimate Kubb Invitational")

if "tournament_active" not in st.session_state:
    st.session_state.tournament_active = False

with st.spinner("Syncing..."):
    df = get_data()

if not df.empty:
    st.session_state.tournament_active = True

# --- SETUP ---
if not st.session_state.tournament_active:
    st.header("Tournament Setup")
    team_input = st.text_area("Enter Team Names (one per line):")
    if st.button("🚀 Launch Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 4:
            st.error("Need at least 4 teams.")
        else:
            t_list = list(teams)
            if len(t_list) % 2 != 0: t_list.append("BYE")
            n, matches = len(t_list), []
            for r in range(3):
                for i in range(n // 2):
                    ta, tb = t_list[i], t_list[n - 1 - i]
                    if ta != "BYE" and tb != "BYE":
                        matches.append({"Type": "Prelim", "Game": len(matches) + 1, "Team A": ta, "Team B": tb, "Winner": "None"})
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            update_sheet(pd.DataFrame(matches))
            st.rerun()

# --- LIVE APP ---
else:
    tab1, tab2, tab3 = st.tabs(["📅 Prelims", "📊 Standings", "🥇 Playoffs"])
    
    # 1. STANDINGS LOGIC (With Tiebreakers)
    prelims = df[df['Type'] == 'Prelim']
    teams = pd.unique(prelims[['Team A', 'Team B']].values.ravel())
    teams = [t for t in teams if t not in ["BYE", "nan", "None", ""]]
    
    standings_list = []
    for t in teams:
        wins = len(prelims[prelims['Winner'] == t])
        played = len(prelims[((prelims['Team A'] == t) | (prelims['Team B'] == t)) & (prelims['Winner'] != "None")])
        # Strength of Schedule: Sum of wins of all opponents played
        opponents = prelims[prelims['Team A'] == t]['Team B'].tolist() + prelims[prelims['Team B'] == t]['Team A'].tolist()
        sos = sum([len(prelims[prelims['Winner'] == opp]) for opp in opponents])
        standings_list.append({"Team": t, "Wins": wins, "Losses": played - wins, "SoS": sos})
    
    standings_df = pd.DataFrame(standings_list).sort_values(by=["Wins", "SoS", "Losses"], ascending=[False, False, True])

    # 2. PRELIM TAB
    with tab1:
        for idx, row in prelims.iterrows():
            with st.container(border=True):
                st.write(f"Match {row['Game']}")
                c1, c2 = st.columns(2)
                for i, col in enumerate([c1, c2]):
                    t_name = row['Team A'] if i == 0 else row['Team B']
                    is_w = row['Winner'] == t_name
                    if col.button(f"{'👑 ' if is_w else ''}{t_name}", key=f"p_{idx}_{i}", use_container_width=True, type="primary" if is_w else "secondary"):
                        df.at[idx, 'Winner'] = t_name
                        update_sheet(df); st.rerun()

    # 3. STANDINGS TAB
    with tab2:
        st.subheader("Leaderboard")
        st.caption("Tiebreaker: Strength of Schedule (Opponent Wins)")
        st.table(standings_df)

    # 4. PLAYOFF TAB (The Bracket Machine)
    with tab3:
        prelims_done = (prelims['Winner'] == "None").sum() == 0
        if not prelims_done:
            st.warning(f"Finish Prelims to start Playoffs ({ (prelims['Winner'] == 'None').sum() } left)")
        else:
            top_8 = standings_df.head(8)['Team'].tolist()
            
            # Helper to manage playoff games in the dataframe
            def get_or_create_playoff(label, ta, tb):
                exists = df[df['Type'] == label]
                if not exists.empty: return exists.iloc[0]
                # If not exists, add to master DF
                new_row = {"Type": label, "Game": label, "Team A": ta, "Team B": tb, "Winner": "None"}
                return new_row

            st.subheader("Quarterfinals")
            qf_matches = [("QF1", 0, 7), ("QF2", 3, 4), ("QF3", 1, 6), ("QF4", 2, 5)]
            qf_winners = []
            
            cols = st.columns(4)
            for i, (label, p1, p2) in enumerate(qf_matches):
                match = df[df['Type'] == label]
                if match.empty:
                    # Add QF games to Sheet if they don't exist
                    new_qf = pd.DataFrame([{"Type": label, "Game": label, "Team A": top_8[p1], "Team B": top_8[p2], "Winner": "None"}])
                    df = pd.concat([df, new_qf], ignore_index=True)
                    update_sheet(df); st.rerun()
                
                row = match.iloc[0]
                with cols[i]:
                    st.caption(label)
                    for t_key in ['Team A', 'Team B']:
                        t_name = row[t_key]
                        if st.button(t_name, key=f"btn_{label}_{t_key}", type="primary" if row['Winner'] == t_name else "secondary", use_container_width=True):
                            df.loc[df['Type'] == label, 'Winner'] = t_name
                            update_sheet(df); st.rerun()
                    if row['Winner'] != "None": qf_winners.append(row['Winner'])

            if len(qf_winners) == 4:
                st.divider()
                st.subheader("Semifinals")
                sf_matches = [("SF1", qf_winners[0], qf_winners[1]), ("SF2", qf_winners[2], qf_winners[3])]
                sf_winners = []
                scols = st.columns(2)
                for i, (label, ta, tb) in enumerate(sf_matches):
                    match = df[df['Type'] == label]
                    if match.empty:
                        df = pd.concat([df, pd.DataFrame([{"Type": label, "Game": label, "Team A": ta, "Team B": tb, "Winner": "None"}])], ignore_index=True)
                        update_sheet(df); st.rerun()
                    
                    row = match.iloc[0]
                    with scols[i]:
                        for t_key in ['Team A', 'Team B']:
                            t_name = row[t_key]
                            if st.button(t_name, key=f"btn_{label}_{t_key}", type="primary" if row['Winner'] == t_name else "secondary", use_container_width=True):
                                df.loc[df['Type'] == label, 'Winner'] = t_name
                                update_sheet(df); st.rerun()
                        if row['Winner'] != "None": sf_winners.append(row['Winner'])

                if len(sf_winners) == 2:
                    st.divider()
                    st.subheader("🏆 Grand Final")
                    label = "FINAL"
                    match = df[df['Type'] == label]
                    if match.empty:
                        df = pd.concat([df, pd.DataFrame([{"Type": label, "Game": label, "Team A": sf_winners[0], "Team B": sf_winners[1], "Winner": "None"}])], ignore_index=True)
                        update_sheet(df); st.rerun()
                    
                    row = match.iloc[0]
                    c1, c2 = st.columns(2)
                    for i, t_key in enumerate(['Team A', 'Team B']):
                        t_name = row[t_key]
                        if [c1, c2][i].button(t_name, key=f"btn_{label}_{t_key}", type="primary" if row['Winner'] == t_name else "secondary", use_container_width=True):
                            df.loc[df['Type'] == label, 'Winner'] = t_name
                            update_sheet(df); st.rerun()
                    
                    if row['Winner'] != "None":
                        st.balloons()
                        st.header(f"🥇 CHAMPION: {row['Winner']} 🥇")
