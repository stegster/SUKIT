import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="SUKIT | Steger Ultimate Kubb Invitational", layout="wide", page_icon="🏆")

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

def reset_tournament():
    empty_df = pd.DataFrame(columns=["Type", "Game", "Team A", "Team B", "Winner"])
    update_sheet(empty_df)
    st.session_state.tournament_active = False
    st.rerun()

# --- 3. THEME-AWARE DYNAMIC CSS ---
st.markdown("""
    <style>
    .hero-text { text-align: center; margin-top: -10px; font-weight: 800; transition: color 0.4s ease; }
    .hero-subtext { text-align: center; font-size: 22px; margin-top: -20px; font-style: italic; }
    @media (prefers-color-scheme: light) { .hero-text { color: #4A2C2A; } .hero-subtext { color: #6D4C41; } }
    @media (prefers-color-scheme: dark) { .hero-text { color: #D7B594; } .hero-subtext { color: #E3C8A8; } }
    </style>
    """, unsafe_allow_html=True)

# --- 4. HEADER ---
col_l, col_mid, col_r = st.columns([1, 2, 1])
with col_mid:
    try:
        st.image("sukit_banner.png", use_container_width=True)
    except:
        st.info("ℹ️ Banner 'sukit_banner.png' not found.")

st.markdown("<h1 class='hero-text'>Steger Ultimate Kubb Invitational</h1>", unsafe_allow_html=True)
st.markdown("<p class='hero-subtext'>Precision. Strategy. Wood.</p>", unsafe_allow_html=True)
st.divider()

# --- 5. DATA FETCHING & VALIDATION ---
required_cols = ["Type", "Game", "Team A", "Team B", "Winner"]
df = get_data()
columns_present = all(col in df.columns for col in required_cols)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.header("🏆 SUKIT Admin")
    if st.button("🚨 Reset Tournament Data", use_container_width=True):
        reset_tournament()

# --- 7. APP LOGIC ---
if df.empty or not columns_present:
    # --- SETUP PHASE ---
    st.subheader("🔥 Start a New Session")
    team_input = st.text_area("Enter Team Names (one per line):", height=200)
    
    if st.button("Generate Schedule", type="primary"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) >= 4:
            t_list = list(teams)
            if len(t_list) % 2 != 0: t_list.append("BYE")
            n = len(t_list)
            matches = []
            for r in range(3):
                for i in range(n // 2):
                    ta, tb = t_list[i], t_list[n - 1 - i]
                    if ta != "BYE" and tb != "BYE":
                        matches.append({"Type": "Prelim", "Game": str(len(matches) + 1), "Team A": ta, "Team B": tb, "Winner": "None"})
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            update_sheet(pd.DataFrame(matches, columns=required_cols))
            st.rerun()
else:
    # --- LIVE APP PHASE ---
    tab1, tab2, tab3 = st.tabs(["📅 Match Schedule", "📊 Leaderboard", "🥇 Top 8 Bracket"])
    
    prelims = df[df['Type'] == 'Prelim']
    
    with tab1:
        st.write("### Preliminary Rounds")
        for idx, row in prelims.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 2])
                c1.markdown(f"**Match {row['Game'].split('.')[0]}**")
                ta, tb, w = row['Team A'], row['Team B'], row['Winner']
                if c2.button(f"{'👑 ' if w == ta else ''}{ta}", key=f"a_{idx}", use_container_width=True, type="primary" if w == ta else "secondary"):
                    df.at[idx, 'Winner'] = ta
                    update_sheet(df); st.rerun()
                if c3.button(f"{'👑 ' if w == tb else ''}{tb}", key=f"b_{idx}", use_container_width=True, type="primary" if w == tb else "secondary"):
                    df.at[idx, 'Winner'] = tb
                    update_sheet(df); st.rerun()

    with tab2:
        all_teams = pd.unique(prelims[['Team A', 'Team B']].values.ravel())
        all_teams = [t for t in all_teams if t not in ["BYE", "nan", "None", ""]]
        standings = []
        for t in all_teams:
            wins = len(prelims[prelims['Winner'] == t])
            losses = len(prelims[((prelims['Team A'] == t) | (prelims['Team B'] == t)) & (prelims['Winner'] != "None") & (prelims['Winner'] != t)])
            opps = prelims[prelims['Team A'] == t]['Team B'].tolist() + prelims[prelims['Team B'] == t]['Team A'].tolist()
            sos = sum([len(prelims[prelims['Winner'] == o]) for o in opps if o != "BYE"])
            standings.append({"Team": t, "Wins": wins, "Losses": losses, "SoS": sos})
        
        standings_df = pd.DataFrame(standings).sort_values(by=["Wins", "SoS", "Losses"], ascending=[False, False, True])
        standings_df.index = range(1, len(standings_df) + 1)
        st.table(standings_df)

    with tab3:
        p_rem = (prelims['Winner'] == "None").sum()
        if p_rem > 0:
            st.warning(f"Complete {p_rem} more matches to lock the bracket.")
        else:
            bracket_df = df[df['Type'].isin(['QF', 'SF', 'Final'])]
            if bracket_df.empty:
                if st.button("🏁 Initialize Official Bracket"):
                    top_8 = standings_df.head(8)['Team'].tolist()
                    seeds = [(0,7,"QF1"), (3,4,"QF2"), (1,6,"QF3"), (2,5,"QF4")]
                    new_m = []
                    for p1, p2, lbl in seeds:
                        new_m.append({"Type": "QF", "Game": lbl, "Team A": top_8[p1], "Team B": top_8[p2], "Winner": "None"})
                    new_m.append({"Type": "SF", "Game": "SF1", "Team A": "TBD", "Team B": "TBD", "Winner": "None"})
                    new_m.append({"Type": "SF", "Game": "SF2", "Team A": "TBD", "Team B": "TBD", "Winner": "None"})
                    new_m.append({"Type": "Final", "Game": "Final", "Team A": "TBD", "Team B": "TBD", "Winner": "None"})
                    update_sheet(pd.concat([df, pd.DataFrame(new_m)], ignore_index=True))
                    st.rerun()
            else:
                # --- SYNC LOGIC (With Safety Checks) ---
                changed = False
                qf_w = df[df['Type'] == 'QF']['Winner'].tolist()
                sf_w = df[df['Type'] == 'SF']['Winner'].tolist()
                
                # Check for SF existence and update from QF winners
                if len(qf_w) >= 4:
                    if qf_w[0] != "None" and qf_w[1] != "None":
                        if 'SF1' in df['Game'].values:
                            if df.loc[df['Game']=='SF1', 'Team A'].values[0] != qf_w[0]: df.loc[df['Game']=='SF1', 'Team A'] = qf_w[0]; changed = True
                            if df.loc[df['Game']=='SF1', 'Team B'].values[0] != qf_w[1]: df.loc[df['Game']=='SF1', 'Team B'] = qf_w[1]; changed = True
                    if qf_w[2] != "None" and qf_w[3] != "None":
                        if 'SF2' in df['Game'].values:
                            if df.loc[df['Game']=='SF2', 'Team A'].values[0] != qf_w[2]: df.loc[df['Game']=='SF2', 'Team A'] = qf_w[2]; changed = True
                            if df.loc[df['Game']=='SF2', 'Team B'].values[0] != qf_w[3]: df.loc[df['Game']=='SF2', 'Team B'] = qf_w[3]; changed = True

                # Check for Final existence and update from SF winners
                if len(sf_w) >= 2 and all(w != "None" for w in sf_w):
                    if 'Final' in df['Game'].values:
                        if df.loc[df['Game']=='Final', 'Team A'].values[0] != sf_w[0]: df.loc[df['Game']=='Final', 'Team A'] = sf_w[0]; changed = True
                        if df.loc[df['Game']=='Final', 'Team B'].values[0] != sf_w[1]: df.loc[df['Game']=='Final', 'Team B'] = sf_w[1]; changed = True
                
                if changed: update_sheet(df); st.rerun()

                # Display synced bracket
                for r_type in ['QF', 'SF', 'Final']:
                    st.write(f"### {r_type}")
                    r_matches = df[df['Type'] == r_type]
                    cols = st.columns(len(r_matches))
                    for i, (idx, row) in enumerate(r_matches.iterrows()):
                        with cols[i]:
                            ta, tb, w = row['Team A'], row['Team B'], row['Winner']
                            if ta == "TBD": st.info("Waiting...")
                            else:
                                if st.button(f"{ta}", key=f"b_a_{idx}", use_container_width=True, type="primary" if w==ta else "secondary"):
                                    df.at[idx, 'Winner'] = ta; update_sheet(df); st.rerun()
                                st.write("vs")
                                if st.button(f"{tb}", key=f"b_b_{idx}", use_container_width=True, type="primary" if w==tb else "secondary"):
                                    df.at[idx, 'Winner'] = tb; update_sheet(df); st.rerun()
                
                # Ultimate Champion Check
                final_results = df[df['Type'] == 'Final']
                if not final_results.empty:
                    champ = final_results['Winner'].values[0]
                    if champ != "None":
                        st.balloons()
                        st.success(f"CHAMPION: {champ}")
