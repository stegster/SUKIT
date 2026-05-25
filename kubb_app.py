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
        st.toast("✅ Update Synced")
    except Exception as e:
        st.error(f"Sync failed: {e}")

st.title("🏆 Steger Ultimate Kubb Invitational")

with st.spinner("Loading Tournament Data..."):
    df = get_data()

# --- SETUP ---
if df.empty or "Team A" not in df.columns:
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
            # Generate 3 rounds of play
            for r in range(3):
                for i in range(n // 2):
                    ta, tb = t_list[i], t_list[n - 1 - i]
                    if ta != "BYE" and tb != "BYE":
                        matches.append({"Type": "Prelim", "Game": str(len(matches) + 1), "Team A": ta, "Team B": tb, "Winner": "None"})
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            update_sheet(pd.DataFrame(matches))
            st.rerun()

# --- LIVE APP ---
else:
    tab1, tab2, tab3 = st.tabs(["📅 Prelims", "📊 Leaderboard", "🥇 Bracket"])
    
    # 1. LIVE STANDINGS CALCULATION (SoS Tiebreaker Retained)
    prelims = df[df['Type'] == 'Prelim']
    all_teams = pd.unique(prelims[['Team A', 'Team B']].values.ravel())
    all_teams = [t for t in all_teams if t not in ["BYE", "nan", "None", ""]]
    
    standings_list = []
    for t in all_teams:
        wins = len(prelims[prelims['Winner'] == t])
        played = len(prelims[((prelims['Team A'] == t) | (prelims['Team B'] == t)) & (prelims['Winner'] != "None")])
        # Find all opponents played
        opponents = prelims[prelims['Team A'] == t]['Team B'].tolist() + prelims[prelims['Team B'] == t]['Team A'].tolist()
        # Strength of Schedule: Sum of wins of all opponents
        sos = sum([len(prelims[prelims['Winner'] == opp]) for opp in opponents if opp != "BYE"])
        standings_list.append({"Team": t, "Wins": wins, "Losses": played - wins, "SoS": sos})
    
    # Sort by Wins, then SoS, then fewer Losses
    standings_df = pd.DataFrame(standings_list).sort_values(by=["Wins", "SoS", "Losses"], ascending=[False, False, True])

    # 2. PRELIMS TAB
    with tab1:
        st.write(f"### {len(prelims)} Prelim Matches")
        for idx, row in prelims.iterrows():
            with st.container(border=True):
                st.write(f"Match {row['Game']}")
                c1, c2 = st.columns(2)
                for i, team_key in enumerate(['Team A', 'Team B']):
                    name = row[team_key]
                    is_winner = row['Winner'] == name
                    if [c1, c2][i].button(f"{'👑 ' if is_winner else ''}{name}", key=f"p_{idx}_{i}", use_container_width=True, type="primary" if is_winner else "secondary"):
                        df.at[idx, 'Winner'] = name
                        update_sheet(df); st.rerun()

    # 3. LEADERBOARD TAB
    with tab2:
        st.subheader("Tournament Standings")
        st.caption("Tiebreaker 1: Strength of Schedule (Total wins of opponents played)")
        st.table(standings_df)

    # 4. BRACKET TAB (The Original Style)
    with tab3:
        st.header("Top 8 Championship")
        remaining = (prelims['Winner'] == "None").sum()
        
        if remaining > 0:
            st.warning(f"Championship Bracket will unlock once the final {remaining} matches are completed.")
            st.info("Current Projected Top 8:")
            st.write(", ".join(standings_df.head(8)['Team'].tolist()))
        else:
            st.balloons()
            st.success("Preliminary Rounds Complete!")
            # Get the top 8 teams based on the leaderboard
            top_8 = standings_df.head(8)['Team'].tolist()
            
            # Standard 1-8, 4-5, 2-7, 3-6 seeding
            st.write("### Quarterfinal Matchups")
            seeds = [(0,7), (3,4), (1,6), (2,5)]
            for i, (p1, p2) in enumerate(seeds):
                with st.container(border=True):
                    st.write(f"**Match {i+1}**")
                    st.write(f"{top_8[p1]} (Seed {p1+1}) vs {top_8[p2]} (Seed {p2+1})")
