import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Steger Ultimate Kubb Invitational", layout="centered")

# 2. Connect to Google Sheets with full permissions
conn = st.connection(
    "gsheets", 
    type=GSheetsConnection, 
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)

def get_data():
    return conn.read(worksheet="Sheet1", ttl=0)

def update_sheet(df):
    try:
        # Clean data and sync
        df_to_save = df.dropna(subset=["Team A"]).astype(str)
        conn.update(worksheet="Sheet1", data=df_to_save)
        st.cache_data.clear()
        st.toast("✅ Result Saved!")
    except Exception as e:
        st.error(f"Sync Error: {e}")

st.title("🏆 Steger Ultimate Kubb Invitational")

# 3. Load Data
try:
    df = get_data()
except:
    df = pd.DataFrame()

# --- SETUP (Only shows if sheet is empty) ---
if df.empty or "Team A" not in df.columns:
    st.header("Tournament Setup (1 Court)")
    team_input = st.text_area("Enter Team Names (one per line):", height=200)
    
    if st.button("🚀 Launch Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 4 or len(teams) % 2 != 0:
            st.error("Please enter an even number of teams.")
        else:
            # Circle Rotation for 3 Games
            n = len(teams)
            t_list = list(teams)
            matches = []
            for r in range(3): # Only 3 Rounds
                for i in range(n // 2):
                    matches.append({
                        "Game": len(matches) + 1,
                        "Team A": t_list[i],
                        "Team B": t_list[n - 1 - i],
                        "Winner": "None"
                    })
                # Rotate
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            
            master_df = pd.DataFrame(matches)
            update_sheet(master_df)
            st.rerun()

# --- LIVE APP ---
else:
    tab1, tab2, tab3 = st.tabs(["📅 Schedule", "📊 Standings", "🥇 Bracket"])

    with tab1:
        st.info("Tap the winner of each match.")
        for idx, row in df.iterrows():
            with st.container(border=True):
                st.write(f"### Match {row['Game']}")
                
                # Winner selection buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    is_winner_a = row['Winner'] == row['Team A']
                    btn_type_a = "primary" if is_winner_a else "secondary"
                    if st.button(f"{'👑 ' if is_winner_a else ''}{row['Team A']}", key=f"a_{idx}", type=btn_type_a, use_container_width=True):
                        df.at[idx, 'Winner'] = row['Team A']
                        update_sheet(df)
                        st.rerun()
                
                with col2:
                    is_winner_b = row['Winner'] == row['Team B']
                    btn_type_b = "primary" if is_winner_b else "secondary"
                    if st.button(f"{'👑 ' if is_winner_b else ''}{row['Team B']}", key=f"b_{idx}", type=btn_type_b, use_container_width=True):
                        df.at[idx, 'Winner'] = row['Team B']
                        update_sheet(df)
                        st.rerun()

    with tab2:
        st.header("Rankings")
        all_teams = pd.unique(df[['Team A', 'Team B']].values.ravel())
        standings = []
        for team in all_teams:
            wins = len(df[df['Winner'] == team])
            losses = len(df[( (df['Team A'] == team) | (df['Team B'] == team) ) & (df['Winner'] != "None") & (df['Winner'] != team)])
            standings.append({"Team": team, "W": wins, "L": losses})
        
        st.table(pd.DataFrame(standings).sort_values(by=["W", "L"], ascending=[False, True]))

    with tab3:
        if (df['Winner'] == "None").any():
            st.warning("Complete all preliminary matches to view the Top 8.")
        else:
            st.header("Top 8 Bracket")
            top_8 = pd.DataFrame(standings).sort_values(by="W", ascending=False).head(8)['Team'].tolist()
            seeds = [(0,7), (3,4), (1,6), (2,5)]
            for i, (p1, p2) in enumerate(seeds):
                st.success(f"Match {i+1}: **{top_8[p1]}** (1) vs **{top_8[p2]}** (8)")
