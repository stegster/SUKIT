import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Steger Ultimate Kubb Invitational", layout="centered")

conn = st.connection(
    "gsheets", 
    type=GSheetsConnection, 
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)

def get_data():
    raw_data = conn.read(worksheet="Sheet1", ttl=0)
    # Filter out completely empty rows that Google Sheets sometimes adds
    return raw_data.dropna(how='all')

def update_sheet(df):
    try:
        # Convert everything to string to prevent TypeErrors
        df_to_save = df.astype(str)
        conn.update(worksheet="Sheet1", data=df_to_save)
        st.cache_data.clear()
        st.toast("✅ Sync Successful")
    except Exception as e:
        st.error(f"Sync Error: {e}")

st.title("🏆 Steger Ultimate Kubb Invitational")

try:
    df = get_data()
except Exception:
    df = pd.DataFrame()

# --- SETUP ---
if df.empty or "Team A" not in df.columns:
    st.header("Tournament Setup (1 Court)")
    team_input = st.text_area("Enter Team Names (one per line):")
    
    if st.button("🚀 Launch Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 4:
            st.error("Enter at least 4 teams.")
        else:
            # Circle Rotation logic
            t_list = list(teams)
            if len(t_list) % 2 != 0: t_list.append("BYE")
            n = len(t_list)
            matches = []
            for r in range(3):
                for i in range(n // 2):
                    matches.append({
                        "Game": str(len(matches) + 1),
                        "Team A": str(t_list[i]),
                        "Team B": str(t_list[n - 1 - i]),
                        "Winner": "None"
                    })
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            
            update_sheet(pd.DataFrame(matches))
            st.rerun()

# --- LIVE APP ---
else:
    tab1, tab2, tab3 = st.tabs(["📅 Schedule", "📊 Standings", "🥇 Bracket"])

    with tab1:
        for idx, row in df.iterrows():
            # Use .get() or str conversion to avoid TypeErrors on missing data
            ta = str(row.get('Team A', 'Unknown'))
            tb = str(row.get('Team B', 'Unknown'))
            winner = str(row.get('Winner', 'None'))
            game_num = str(row.get('Game', idx))

            with st.container(border=True):
                st.write(f"### Match {game_num}")
                c1, c2 = st.columns(2)
                
                with c1:
                    is_a = (winner == ta)
                    if st.button(f"{'👑 ' if is_a else ''}{ta}", key=f"a_{idx}", use_container_width=True, type="primary" if is_a else "secondary"):
                        df.at[idx, 'Winner'] = ta
                        update_sheet(df)
                        st.rerun()
                with c2:
                    is_b = (winner == tb)
                    if st.button(f"{'👑 ' if is_b else ''}{tb}", key=f"b_{idx}", use_container_width=True, type="primary" if is_b else "secondary"):
                        df.at[idx, 'Winner'] = tb
                        update_sheet(df)
                        st.rerun()

    with tab2:
        st.header("Rankings")
        # Ensure we are only looking at valid team rows
        valid_df = df[df['Team A'].notnull()]
        all_teams = pd.unique(valid_df[['Team A', 'Team B']].values.ravel())
        standings = []
        for team in all_teams:
            if team == "BYE": continue
            w = len(valid_df[valid_df['Winner'] == team])
            standings.append({"Team": team, "Wins": w})
        
        st.table(pd.DataFrame(standings).sort_values(by="Wins", ascending=False))

    with tab3:
        st.info("Top 8 will be displayed here after Prelims.")
