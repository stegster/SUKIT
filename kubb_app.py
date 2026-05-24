import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Steger Ultimate Kubb Invitational", layout="centered")

# --- CONNECTION ---
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

st.title("🏆 Steger Ultimate Kubb Invitational")

# --- LOAD DATA (Fixes the NameError) ---
df = get_data()

# --- SETUP (The 18-match Scheduler) ---
if df.empty or "Team A" not in df.columns:
    st.header("Tournament Setup (1 Court)")
    team_input = st.text_area("Enter Team Names (one per line):")
    
    if st.button("🚀 Launch Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 4:
            st.error("Enter at least 4 teams.")
        else:
            t_list = list(teams)
            if len(t_list) % 2 != 0: t_list.append("BYE")
            
            n = len(t_list)
            all_matches = []
            
            # Generate 3 Rounds to ensure 12 teams = 18 games
            for r in range(3):
                for i in range(n // 2):
                    ta, tb = t_list[i], t_list[n - 1 - i]
                    if ta != "BYE" and tb != "BYE":
                        all_matches.append({
                            "Game": str(len(all_matches) + 1),
                            "Team A": str(ta),
                            "Team B": str(tb),
                            "Winner": "None"
                        })
                # Rotate for next round
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            
            update_sheet(pd.DataFrame(all_matches))
            st.rerun()

# --- LIVE APP ---
else:
    tab1, tab2, tab3 = st.tabs(["📅 Schedule", "📊 Standings", "🥇 Bracket"])
    live_df = df.copy().astype(str)

    with tab1:
        for idx, row in live_df.iterrows():
            with st.container(border=True):
                st.write(f"### Match {row['Game']}")
                c1, c2 = st.columns(2)
                with c1:
                    is_a = (row['Winner'] == row['Team A'])
                    if st.button(f"{'👑 ' if is_a else ''}{row['Team A']}", key=f"a_{idx}", use_container_width=True, type="primary" if is_a else "secondary"):
                        live_df.at[idx, 'Winner'] = row['Team A']
                        update_sheet(live_df)
                        st.rerun()
                with c2:
                    is_b = (row['Winner'] == row['Team B'])
                    if st.button(f"{'👑 ' if is_b else ''}{row['Team B']}", key=f"b_{idx}", use_container_width=True, type="primary" if is_b else "secondary"):
                        live_df.at[idx, 'Winner'] = row['Team B']
                        update_sheet(live_df)
                        st.rerun()

    with tab2:
        st.header("Rankings")
        teams_only = pd.unique(live_df[['Team A', 'Team B']].values.ravel())
        standings = [{"Team": t, "Wins": len(live_df[live_df['Winner'] == t])} for t in teams_only if t != "nan"]
        st.table(pd.DataFrame(standings).sort_values(by="Wins", ascending=False))

    with tab3:
        st.info("Top 8 Bracket unlocks after Match 18.")
