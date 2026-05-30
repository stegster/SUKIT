import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(
    page_title="SUKIT | Steger Ultimate Kubb Invitational", 
    layout="wide", 
    page_icon="🏆"
)

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
    .hero-text {
        text-align: center;
        margin-top: -10px;
        font-weight: 800;
        transition: color 0.4s ease;
    }
    
    .hero-subtext {
        text-align: center;
        font-size: 22px;
        margin-top: -20px;
        font-style: italic;
    }

    /* LIGHT MODE: Dark Wood / Burnt Charcoal */
    @media (prefers-color-scheme: light) {
        .hero-text { color: #78592B; }
        .hero-subtext { color: #6D4C41; }
    }
    
    /* DARK MODE: Light Wood / Natural Tan */
    @media (prefers-color-scheme: dark) {
        .hero-text { color: #D7B594; }
        .hero-subtext { color: #E3C8A8; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. HEADER SECTION ---
col_l, col_mid, col_r = st.columns([1, 2, 1])
with col_mid:
    try:
        st.image("sukit_banner.png", use_container_width=True)
    except:
        st.info("ℹ️ Banner 'sukit_banner.png' not found.")

st.markdown("<h1 class='hero-text'>Steger Ultimate Kubb Invitational</h1>", unsafe_allow_html=True)
st.markdown("<p class='hero-subtext'>Precision. Strategy. Wood.</p>", unsafe_allow_html=True)
st.divider()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🏆 SUKIT Admin")
    if st.button("🚨 Reset Tournament Data", use_container_width=True):
        reset_tournament()

# --- 6. DATA FETCHING ---
if "tournament_active" not in st.session_state:
    st.session_state.tournament_active = False

df = get_data()

if not df.empty and "Team A" in df.columns:
    st.session_state.tournament_active = True

# --- 7. SETUP PHASE ---
if not st.session_state.tournament_active:
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
            update_sheet(pd.DataFrame(matches))
            st.session_state.tournament_active = True
            st.rerun()

# --- 8. LIVE APP PHASE ---
else:
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

    # STANDINGS CALCULATION
    all_teams = pd.unique(prelims[['Team A', 'Team B']].values.ravel())
    all_teams = [t for t in all_teams if t not in ["BYE", "nan", "None", ""]]
    standings_list = []
    for t in all_teams:
        wins = len(prelims[prelims['Winner'] == t])
        played = len(prelims[((prelims['Team A'] == t) | (prelims['Team B'] == t)) & (prelims['Winner'] != "None")])
        opponents = prelims[prelims['Team A'] == t]['Team B'].tolist() + prelims[prelims['Team B'] == t]['Team A'].tolist()
        sos = sum([len(prelims[prelims['Winner'] == opp]) for opp in opponents if opp != "BYE"])
        standings_list.append({"Team": t, "Wins": wins, "Losses": played-wins, "SoS": sos, "GP": played})
    
    standings_df = pd.DataFrame(standings_list).sort_values(by=["Wins", "SoS", "Losses"], ascending=[False, False, True])
    standings_df.reset_index(drop=True, inplace=True)
    standings_df.index += 1

    with tab2:
        st.subheader("Leaderboard")
        st.table(standings_df)

    with tab3:
        p_rem = (prelims['Winner'] == "None").sum()
        if p_rem > 0:
            st.warning(f"Complete {p_rem} more matches to lock the bracket.")
        else:
            # --- BALLOONS CELEBRATION ---
            st.balloons() 
            st.success("🏆 Preliminary Rounds Complete! The King Has Fallen.")
            
            top_8 = standings_df.head(8)['Team'].tolist()
            seeds = [(0,7), (3,4), (1,6), (2,5)]
            
            st.subheader("Championship Bracket")
            for i, (p1, p2) in enumerate(seeds):
                with st.container(border=True):
                    st.write(f"**Quarterfinal Match {i+1}**")
                    st.markdown(f"### {top_8[p1]} (Seed 1) vs {top_8[p2]} (Seed 8)")
