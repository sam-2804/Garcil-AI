import streamlit as st
import sqlite3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 1.Page & DB Configuration
st.set_page_config(page_title="Garcil-AI", page_icon="🗺️", layout="wide")

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

st.title("Garcil-AI: Adaptive Learning Architect")

# 2. Taxonomy Matrix (Deterministic Data)
ROLE_TAXONOMY = {
    "Data Scientist": {"Python", "SQL", "Pandas", "Machine Learning", "Statistics"},
    "AI Engineer": {"Python", "PyTorch", "Transformers", "Docker", "FastAPI"},
    "Cloud Architect": {"Python", "AWS", "Docker", "Kubernetes", "Terraform"}
}

# 3. User Input Form
with st.form("profile_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        background = st.text_input("Academic Background", "B.Tech Computer Science")
        target_role = st.selectbox("Target Role", list(ROLE_TAXONOMY.keys()))
    
    with col2:
        known_skills = st.multiselect(
            "Current Technical Skills", 
            ["Python", "SQL", "Java", "AWS", "Pandas", "Docker", "PyTorch", "React"],
            default=["Python"]
        )
        weekly_hours = st.slider("Weekly Time Commitment", 2, 20, 10)
    
    submitted = st.form_submit_button("Analyze Skill Gap", type="primary")

# 4. Deterministic Gap Engine (Feature Engineering)
if submitted:
    user_skills = set(known_skills)
    required_skills = ROLE_TAXONOMY[target_role]
    
    # Pure Python Set Math to find the gap
    missing_skills = required_skills - user_skills
    
    # Calculate Readiness Score
    total_req = len(required_skills)
    score = ((total_req - len(missing_skills)) / total_req) * 100
    
    st.subheader("📊 Deterministic Gap Analysis")
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