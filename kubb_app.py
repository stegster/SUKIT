import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Steger Ultimate Kubb Invitational", layout="wide")

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(ttl=0) # ttl=0 means it pulls fresh data every time

def save_data(df):
    conn.update(data=df)
    st.cache_data.clear()

# --- APP LAYOUT ---
st.title("🏆 Steger Ultimate Kubb Invitational")

# Check if we have data
try:
    df = load_data()
except:
    df = pd.DataFrame(columns=["Time Slot", "Court", "Team A", "Team B", "Winner"])

# --- SETUP (Only visible if sheet is empty) ---
if df.empty:
    st.header("1. Initial Setup")
    team_input = st.text_area("Enter Team Names (one per line):")
    if st.button("Generate & Sync Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        # (The same scheduling logic from before goes here...)
        # We generate 'new_df' and then:
        # save_data(new_df)
        st.rerun()

# --- LIVE APP ---
else:
    tab1, tab2, tab3 = st.tabs(["📅 Live Schedule", "📊 Standings", "🥇 Bracket"])

    with tab1:
        st.info("Results update for everyone in real-time.")
        for idx, row in df.iterrows():
            cols = st.columns([1, 4])
            with cols[0]: st.write(f"R{row['Time Slot']} C{row['Court']}")
            with cols[1]:
                if st.button(f"{row['Team A']} vs {row['Team B']}", key=f"btn_{idx}"):
                    # Toggle logic or pop-up to select winner
                    pass
