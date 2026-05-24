import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Steger Ultimate Kubb Invitational", layout="centered")

# 1. Connect
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # Pull data and force everything to be a 'string' (text) immediately
        df = conn.read(worksheet="Sheet1", ttl=0)
        df = df.dropna(how='all').astype(str)
        return df
    except Exception:
        return pd.DataFrame()

def update_sheet(df):
    try:
        # Final safety check: convert to string before saving
        df_save = df.astype(str)
        conn.update(worksheet="Sheet1", data=df_save)
        st.cache_data.clear()
        st.toast("✅ Match Saved!")
    except Exception as e:
        st.error(f"Sync failed: {e}")

st.title("🏆 Steger Ultimate Kubb Invitational")

# 2. Load Data
df = get_data()

# --- SETUP ---
if df.empty or "Team A" not in df.columns:
    st.header("Tournament Setup")
    team_input = st.text_area("Enter Team Names (one per line):")
    
    if st.button("🚀 Launch Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 4:
            st.error("Enter at least 4 teams.")
        else:
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
            
            # Create DataFrame and FORCE it to be objects (text)
            master_df = pd.DataFrame(matches).astype(str)
            update_sheet(master_df)
            st.rerun()

# --- LIVE APP ---
else:
    tab1, tab2, tab3 = st.tabs(["📅 Schedule", "📊 Standings", "🥇 Bracket"])

    with tab1:
        # We make a COPY of the data to ensure we don't hit "SettingWithCopy" warnings
        live_df = df.copy().astype(str)
        
        for idx, row in live_df.iterrows():
            ta = row['Team A']
            tb = row['Team B']
            winner = row['Winner']
            
            with st.container(border=True):
                st.write(f"### Match {row['Game']}")
                c1, c2 = st.columns(2)
                
                with c1:
                    is_a = (winner == ta)
                    if st.button(f"{'👑 ' if is_a else ''}{ta}", key=f"a_{idx}", use_container_width=True, type="primary" if is_a else "secondary"):
                        live_df.at[idx, 'Winner'] = str(ta)
                        update_sheet(live_df)
                        st.rerun()
                with c2:
                    is_b = (winner == tb)
                    if st.button(f"{'👑 ' if is_b else ''}{tb}", key=f"b_{idx}", use_container_width=True, type="primary" if is_b else "secondary"):
                        live_df.at[idx, 'Winner'] = str(tb)
                        update_sheet(live_df)
                        st.rerun()

    with tab2:
        st.header("Rankings")
        all_teams = pd.unique(live_df[['Team A', 'Team B']].values.ravel())
        standings = []
        for team in all_teams:
            if team == "BYE" or team == "nan": continue
            w = len(live_df[live_df['Winner'] == team])
            standings.append({"Team": team, "Wins": w})
        
        st.table(pd.DataFrame(standings).sort_values(by="Wins", ascending=False))

    with tab3:
        st.info("Top 8 will be displayed here after all 3 rounds are complete.")
