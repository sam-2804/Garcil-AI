import streamlit as st
import sqlite3
import json
import os
from dotenv import load_dotenv

# ==========================================
# 1. CONFIG & CSS INJECTION
# ==========================================
load_dotenv()
st.set_page_config(page_title="Garcil-AI Dashboard", layout="wide")
# Retro 8-bit CSS
# Retro 8-bit CSS
retro_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap');

/* 1. Base terminal text */
html, body, [class*="st-"] {
    font-family: 'VT323', monospace !important;
    font-size: 1.2rem !important; 
    -webkit-font-smoothing: none !important;
    text-rendering: pixelated !important;
}

/* 2. Scale down the 8-bit font slightly more to prevent sidebar wrapping */
h1, h2, h3, p, label, .st-emotion-cache-10trnc2 {
    font-family: 'Press Start 2P', cursive !important;
    font-size: 0.7rem !important; /* Shrunk from 0.85rem to fit the sidebar */
    -webkit-font-smoothing: none !important;
    text-rendering: pixelated !important;
}

h1 { font-size: 1.2rem !important; margin-bottom: 0.5rem !important; }
h2, h3 { margin-bottom: 0.3rem !important; }

/* 3. Fix the massive gaps between radio buttons */
.stRadio > div[role="radiogroup"] {
    gap: 0.5rem !important; /* Pulls the radio options tightly together */
}

/* 4. Keep buttons blocky and proportional */
div[data-testid="stButton"] button {
    font-family: 'Press Start 2P', cursive !important;
    font-size: 0.8rem !important;
    border-radius: 0px !important;
    border: 2px solid #000 !important;
    box-shadow: 3px 3px 0px #000 !important;
    padding: 0.4rem 0.8rem !important;
    -webkit-font-smoothing: none !important;
}

/* 5. Tidy the layout boxes */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 0px !important;
    border: 2px solid #333 !important;
    padding: 1rem !important; 
}
/* Pull the entire main content block up to reduce top whitespace */
.block-container {
    padding-top: 1rem !important; 
}

/* 6. General spacing tightener */
[data-testid="stVerticalBlock"] { 
    gap: 1.2rem !important; 
    border-radius: 0px !important;
    border: 2px solid #333 !important;
    padding: 1.5rem !important;
}
</style>
"""
st.markdown(retro_css, unsafe_allow_html=True)
st.markdown(retro_css, unsafe_allow_html=True)

# ==========================================
# 2. DATABASE CONFIGURATION
# ==========================================
conn = sqlite3.connect("garcil_state.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_role TEXT,
        readiness_score REAL,
        missing_skills TEXT
    )
""")
conn.commit()

# Deterministic Data
ROLE_TAXONOMY = {
    "Data Scientist": {"Python", "SQL", "Pandas", "Machine Learning", "Statistics"},
    "AI Engineer": {"Python", "PyTorch", "Transformers", "Docker", "FastAPI"},
    "Cloud Architect": {"Python", "AWS", "Docker", "Kubernetes", "Terraform"}
}

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("### PLAYER MENU")
    st.markdown("---")
    current_page = st.radio("SELECT LEVEL:", [
        "1. Character Creation", 
        "2. Quest Log (Roadmap)", 
        "3. Player Stats (Dashboard)"
    ])
    st.markdown("---")
    st.caption("SYSTEM STATUS: ONLINE")

# ==========================================
# 4. PAGE LOGIC
# ==========================================
if current_page == "1. Character Creation":
    st.markdown("<h1>INITIATE PROFILE SETUP</h1>", unsafe_allow_html=True)
    
    # UI Layout: Mission Objective Box
    with st.container(border=True):
        st.markdown("### MISSION OBJECTIVE")
        col1, col2 = st.columns(2)
        with col1:
            background = st.text_input("Academic Background", "B.Tech Computer Science")
        with col2:
            target_role = st.selectbox("Target Class (Role)", list(ROLE_TAXONOMY.keys()))
            
    # UI Layout: Skill Inventory Box
    with st.container(border=True):
        st.markdown("### SKILL INVENTORY")
        known_skills = st.multiselect(
            "Equipped Skills", 
            ["Python", "SQL", "Java", "AWS", "Pandas", "Docker", "PyTorch", "React"],
            default=["Python"]
        )
        weekly_hours = st.slider("Grinding Hours (Per Week)", 2, 20, 10)
        
    # Execution Logic
    if st.button("GENERATE ROADMAP", type="primary"):
        # Pure Python Set Math to find the gap
        user_skills = set(known_skills)
        required_skills = ROLE_TAXONOMY[target_role]
        missing_skills = required_skills - user_skills
        
        # Calculate Readiness Score
        total_req = len(required_skills)
        score = ((total_req - len(missing_skills)) / total_req) * 100
        
        # UI Output
        st.markdown("---")
        st.markdown("### 📊 DETERMINISTIC GAP ANALYSIS")
        st.metric("Career Readiness Score", f"{int(score)}%")
        
        if missing_skills:
            st.warning(f"Missing Competencies Detected: {', '.join(missing_skills)}")
        else:
            st.success("You have all the baseline skills required!")
            
        # Save state to SQLite
        cursor.execute(
            "INSERT INTO users (target_role, readiness_score, missing_skills) VALUES (?, ?, ?)",
            (target_role, score, json.dumps(list(missing_skills)))
        )
        conn.commit()

elif current_page == "2. Quest Log (Roadmap)":
    st.markdown("<h1>ACTIVE QUESTS</h1>", unsafe_allow_html=True)
    st.info("Backend AI integration pending. Please return to Character Creation.")

elif current_page == "3. Player Stats (Dashboard)":
    st.markdown("<h1>ANALYTICS DASHBOARD</h1>", unsafe_allow_html=True)
    st.info("Metrics integration pending. Please return to Character Creation.")