import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Steger Ultimate Kubb Invitational", layout="centered")

# 2. Connection Setup (Uses Scopes from your Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # Pull data from Sheet1
        data = conn.read(worksheet="Sheet1", ttl=0)
        # Drop empty rows and force everything to strings to prevent TypeErrors
        return data.dropna(how='all').astype(str)
    except:
        # If sheet is brand new/empty, return an empty dataframe
        return pd.DataFrame()

def update_sheet(df):
    try:
        # Ensure every cell is a string before it hits the cloud
        df_save = df.astype(str)
        conn.update(worksheet="Sheet1", data=df_save)
        # Clear local cache so everyone sees the update immediately
        st.cache_data.clear()
        st.toast("✅ Match Updated!")
    except Exception as e:
        st.error(f"Sync failed: {e}")

# --- TITLE ---
st.title("🏆 Steger Ultimate Kubb Invitational")

# 3. Load Data immediately to prevent NameErrors
df = get_data()

# --- TAB 0: SETUP (Shows if Google Sheet is empty) ---
if df.empty or "Team A" not in df.columns:
    st.header("Tournament Setup (1 Court)")
    st.info("Enter teams to generate a 3-round rotation (18 games for 12 teams).")
    team_input = st.text_area("Enter Team Names (one per line):", height=250)
    
    if st.button("🚀 Launch Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 4:
            st.error("Please enter at least 4 teams.")
        else:
            t_list = list(teams)
            # Add a 'BYE' if there is an odd number of teams
            if len(t_list) % 2 != 0: 
                t_list.append("BYE")
            
            n = len(t_list)
            all_matches = []
            
            # Generate exactly 3 Rounds of play
            for r in range(3):
                for i in range(n // 2):
                    ta, tb = t_list[i], t_list[n - 1 - i]
                    # Only record the match if it's not against the BYE
                    if ta != "BYE" and tb != "BYE":
                        all_matches.append({
                            "Game": len(all_matches) + 1,
                            "Team A": str(ta),
                            "Team B": str(tb),
                            "Winner": "None"
                        })
                # Perform Circle Rotation: keep index 0, rotate others
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            
            # Convert to DataFrame and push to Google
            master_df = pd.DataFrame(all_matches)
            update_sheet(master_df)
            st.rerun()

# --- THE MAIN APP (Shows once setup is complete) ---
else:
    tab1, tab2, tab3 = st.tabs(["📅 Schedule", "📊 Standings", "🥇 Bracket"])
    
    # Work with a clean copy of the data
    live_df = df.copy().astype(str)

    with tab1:
        st.write("### Single Court Match List")
        for idx, row in live_df.iterrows():
            with st.container(border=True):
                # Clean up the Match Number (removes the .0 decimal)
                game_id = str(row['Game']).split('.')[0]
                st.write(f"#### Match {game_id}")
                
                c1, c2 = st.columns(2)
                ta, tb = row['Team A'], row['Team B']
                winner = row['Winner']

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
                        update_
