from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from google import genai
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import time
import json
import re
import os



# State variables for consistency across reloads or events

if "curriculum" not in st.session_state:
    st.session_state.curriculum = None
if "score" not in st.session_state:
    st.session_state.score = 0
if "missing_skills" not in st.session_state:
    st.session_state.missing_skills = []



# CONFIG 
load_dotenv()
st.set_page_config(page_title="Garcil-AI Dashboard", layout="wide")

# Initialize theme state
if "retro_mode" not in st.session_state:
    st.session_state.retro_mode = True

# Retro 8-bit CSS
retro_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap');

/* Base terminal text */

html, body, [class*="st-"] {
    font-family: 'VT323', monospace !important;
    font-size: 1.2rem !important; 
    -webkit-font-smoothing: none !important;
    text-rendering: pixelated !important;
}

/* Scale down the 8-bit font slightly more to prevent sidebar wrapping */

h1, h2, h3, p, label, .st-emotion-cache-10trnc2 {
    font-family: 'Press Start 2P', cursive !important;
    font-size: 0.7rem !important; /* Shrunk from 0.85rem to fit the sidebar */
    -webkit-font-smoothing: none !important;
    text-rendering: pixelated !important;
}

h1 { font-size: 1.2rem !important; margin-bottom: 0.5rem !important; }
h2, h3 { margin-bottom: 0.3rem !important; }

/* Fix the massive gaps between radio buttons */

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

#.block-container {
#    padding-top: 2rem !important; 
#}

h1, h2, h3 { 
    text-align: center !important; 
    margin-bottom: 0.5rem !important; 
    padding-bottom: 0px !important; 
}

/* Hide the accidental sidebar collapse icon text artifact */

[data-testid="stSidebarNav"] span, button[kind="header"] svg, .css-1rs6os {
    /* hides stray navigation text remnants */
}

/* Specifically targets the collapsed control icon text */

.st-emotion-cache-12xyydp, [data-testid="collapsedControl"] {
    display: none !important;
}

/* Center everything inside the sidebar */

[data-testid="stSidebar"] * {
    text-align: center !important;
}

/* Force the radio group options to center align their text */

[data-testid="stSidebar"] div[role="radiogroup"] label {
    justify-content: center !important;
}

/* General spacing tightener */

[data-testid="stVerticalBlock"] { 
    gap: 1.2rem !important; 
    border-radius: 0px !important;
    border: 2px solid #333 !important;
    padding: 1.5rem !important;
}

</style>
"""

if st.session_state.retro_mode:
    st.markdown(retro_css, unsafe_allow_html=True)

  

# DATABASE INITIALIZATION

conn = sqlite3.connect("garcil_state.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_email TEXT,
        target_role TEXT,
        readiness_score REAL,
        missing_skills TEXT,
        curriculum TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS quest_progress (
        player_email TEXT,
        week_num INTEGER,
        is_completed INTEGER DEFAULT 0,
        PRIMARY KEY (player_email, week_num)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_accounts (
        email TEXT PRIMARY KEY,
        name TEXT,
        password TEXT
    )
""")


conn.commit()

# Deterministic Data
ROLE_TAXONOMY = {
    "Data Scientist": {"Python", "SQL", "Pandas", "Machine Learning", "Statistics"},
    "AI Engineer": {"Python", "PyTorch", "Transformers", "Docker", "FastAPI"},
    "Cloud Architect": {"Python", "AWS", "Docker", "Kubernetes", "Terraform"}
} 

# AUTHENTICATION GATE 

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.player_name = None
    st.session_state.player_email = None

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>SYSTEM ACCESS RESTRICTED</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            # Create a clean tabbed interface for Login vs Registration
            tab1, tab2 = st.tabs(["LOGIN", "NEW PLAYER REGISTRATION"])
            
            with tab1:
                st.markdown("### ENTER CREDENTIALS")
                login_email = st.text_input("Player ID (Email)", key="login_email")
                login_pass = st.text_input("Password", type="password", key="login_pass")
                
                if st.button("AUTHORIZE LOGIN", type="primary", use_container_width=True):
                    # Check database for exact match
                    cursor.execute("SELECT name, password FROM user_accounts WHERE email = ?", (login_email,))
                    record = cursor.fetchone()
                    
                    if record and record[1] == login_pass:
                        st.session_state.logged_in = True
                        st.session_state.player_name = record[0]
                        st.session_state.player_email = login_email
                        st.rerun()
                    else:
                        st.error("ACCESS DENIED: Invalid Player ID or Password")
                        
            with tab2:
                st.markdown("### CREATE NEW PROFILE")
                reg_name = st.text_input("Player Name", key="reg_name")
                reg_email = st.text_input("Player ID (Email)", key="reg_email")
                reg_pass = st.text_input("Password", type="password", key="reg_pass")
                
                if st.button("REGISTER PROFILE", type="primary", use_container_width=True):
                    if reg_name and reg_email and reg_pass:
                        try:    
                            # Insert new user into database
                            cursor.execute(
                                "INSERT INTO user_accounts (email, name, password) VALUES (?, ?, ?)", 
                                (reg_email, reg_name, reg_pass)
                            )
                            conn.commit()
                            st.success("PROFILE CREATED! Switch to the LOGIN tab to enter.")
                        except sqlite3.IntegrityError:
                            # Triggers if the email (PRIMARY KEY) already exists
                            st.error("ERROR: Player ID (Email) already exists in the system.")
                    else:
                        st.warning("Please fill in all fields to register.")
    
    st.stop()
    
def get_quest_status(week_num):
    cursor.execute("SELECT is_completed FROM quest_progress WHERE week_num = ?", (week_num,))
    result = cursor.fetchone()
    return bool(result[0]) if result else False

def update_quest_status(week_num, is_completed):
    cursor.execute("""
        INSERT INTO quest_progress (week_num, is_completed) 
        VALUES (?, ?) 
        ON CONFLICT(week_num) DO UPDATE SET is_completed = excluded.is_completed
    """, (week_num, int(is_completed)))
    conn.commit()
    
def get_quest_status(week_num):
    email = st.session_state.player_email
    cursor.execute("SELECT is_completed FROM quest_progress WHERE player_email = ? AND week_num = ?", (email, week_num))
    result = cursor.fetchone()
    return bool(result[0]) if result else False

def update_quest_status(week_num, is_completed):
    email = st.session_state.player_email
    cursor.execute("""
        INSERT INTO quest_progress (player_email, week_num, is_completed) 
        VALUES (?, ?, ?) 
        ON CONFLICT(player_email, week_num) DO UPDATE SET is_completed = excluded.is_completed
    """, (email, week_num, int(is_completed)))
    conn.commit()

# SIDEBAR NAVIGATION
with st.sidebar:
    
    st.markdown("### PLAYER MENU")
    st.markdown("---")
    current_page = st.radio("SELECT LEVEL:", [
        "1. Character Creation", 
        "2. Quest Log (Roadmap)", 
        "3. Player Stats (Dashboard)"
    ])
    st.markdown("---")
    
    # toggle for theme switching
    st.toggle("8-bit Arcade Mode", key="retro_mode")
    
    st.markdown("---")
    st.caption("SYSTEM STATUS: ONLINE")
    st.caption(f"LOGGED IN AS: {st.session_state.player_name.upper()}")


#  RAG & AI BACKEND ARCHITECTURE

def retrieve_resources(missing_skills):
    
    try:
        with open("resources.json", "r") as file:
            all_resources = json.load(file)
        filtered_resources = []
        
        for res in all_resources:
            if res["skill"] in missing_skills:
                filtered_resources.append(res)
        return filtered_resources
        
    except FileNotFoundError:
        return []

def clean_json_response(raw_text):
    
    cleaned = re.sub(r"```json\n|\n```|```", "", raw_text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None

def generate_curriculum(target_role, missing_skills, resources, weekly_hours):
    
    
    prompt = f"""
        You are an expert technical curriculum architect.
        Target Role: {target_role}
        Skills to Learn: {list(missing_skills)}
        Time Commitment: {weekly_hours} hours per week
        Verified Resources Available: {json.dumps(resources)}

        Task:
        Sequence the 'Skills to Learn' logically. Do not invent course links; ONLY use the URLs provided in the verified resources.
        Format the response strictly as a JSON object with a 'modules' array containing 'week', 'focus_skill', 'resource_title', 'url', 'estimated_hours', and 'rationale'.
    """
        
    # Primary API (Google GenAI)
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        parsed_json = clean_json_response(response.text)
        if parsed_json: 
            return parsed_json
    except Exception as e:
        print(f"Gemini API warning: {str(e)}. Attempting fallback...")

    # Fallback API(Hugging Face Zephyr)
    try:
        hf_client = InferenceClient(token=os.getenv("HF_TOKEN"))
        response = hf_client.chat_completion(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "user", 
                    "content": prompt + "\n\nCRITICAL: Output ONLY valid JSON. No markdown formatting, no intro text, no outro text."
                }
            ],
            max_tokens=800,
            temperature=0.2
        )
        
        raw_output = response.choices[0].message.content
        parsed_json = clean_json_response(raw_output)
        if parsed_json: 
            return parsed_json
            
    except Exception as fallback_error:
        print(f"Fallback API failed: {str(fallback_error)}")
        
    return None
    
st.markdown(
    """
    <div style="border-bottom: 2px dashed #444; padding-bottom: 0.5rem; margin-bottom: 1rem;text-align: center;">
        <span style="font-family: 'Press Start 2P', cursive; font-size: 1rem; color: #ff3333;">GARCIL-AI</span>
        <span style="font-family: 'VT323', monospace; font-size: 1.2rem; color: #888; margin-left: 1rem;">v0.4</span>
    </div>
    """,
    unsafe_allow_html=True
)

# PAGE LOGIC

if current_page == "1. Character Creation":
    st.markdown("<h1>INITIATE PROFILE SETUP</h1>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("### MISSION OBJECTIVE")
        col1, col2 = st.columns(2)
        with col1:
            background = st.text_input("Academic Background", "B.Tech Computer Science")
        with col2:
            target_role = st.selectbox("Target Class (Role)", list(ROLE_TAXONOMY.keys()))
            
    with st.container(border=True):
        st.markdown("### SKILL INVENTORY")
        known_skills = st.multiselect(
            "Equipped Skills", 
            ["Python", "SQL", "Java", "AWS", "Pandas", "Docker", "PyTorch", "React"],
            default=["Python"]
        )
        weekly_hours = st.slider("Grinding Hours (Per Week)", 2, 20, 10)
        
    if st.button("GENERATE ROADMAP", type="primary"):
        user_skills = set(known_skills)
        required_skills = ROLE_TAXONOMY[target_role]
        missing_skills = required_skills - user_skills
        
        total_req = len(required_skills)
        score = ((total_req - len(missing_skills)) / total_req) * 100
        
        st.session_state.score = score
        st.session_state.missing_skills = list(missing_skills)
        
        
        
        if missing_skills:
            with st.spinner("Compiling personalized curriculum via AI Engine..."):
                matched_resources = retrieve_resources(missing_skills)
                curriculum_json = generate_curriculum(target_role, missing_skills, matched_resources, weekly_hours)
                
                if curriculum_json:
                    st.session_state.curriculum = curriculum_json
                    
                    cursor.execute(
                        "INSERT INTO users (player_email, target_role, readiness_score, missing_skills,curriculum) VALUES (?, ?, ?, ?)",
                        (st.session_state.player_email, target_role, score, json.dumps(list(missing_skills)), json.dumps(curriculum_json))
                    )
                    conn.commit()
                    
                    st.success("SUCCESS! Curriculum loaded. Go to 'Quest Log (Roadmap)' to view your path.")
                else:
                    st.error("AI Generation failed. Please check your API keys.")
        else:
            cursor.execute(
                "INSERT INTO users (player_email, target_role, readiness_score, missing_skills, curriculum) VALUES (?, ?, ?, ?)",
                (st.session_state.player_email, target_role, score, "[]", "{}")
            )
            conn.commit()
            st.success("You have all baseline skills required for this role!")


elif current_page == "2. Quest Log (Roadmap)":
    st.markdown("<h1>ACTIVE QUESTS</h1>", unsafe_allow_html=True)
    
    if not st.session_state.curriculum:
        cursor.execute("SELECT curriculum, missing_skills FROM users ORDER BY id DESC LIMIT 1")
        saved_data = cursor.fetchone()
        if saved_data and saved_data[0]:
            st.session_state.curriculum = json.loads(saved_data[0])
            st.session_state.missing_skills = json.loads(saved_data[1])
    
    if st.session_state.curriculum:
        col_main, col_side = st.columns([2, 1])
        
        with col_main:
            for module in st.session_state.curriculum.get("modules", []):
                week_num = module.get("week")
                
                # Load saved state from database
                saved_status = get_quest_status(week_num)
                
                with st.container(border=True):
                    st.markdown(f"### WEEK {week_num}: {module.get('focus_skill')}")
                    st.write(f"**OBJECTIVE:** {module.get('rationale')}")
                    st.write(f"**TIME REQ:** {module.get('estimated_hours')} Hours")
                    st.markdown(f"[START MODULE: {module.get('resource_title')}]({module.get('url')})")
                    
                    # Interactive checkbox connected to database callback
                    is_checked = st.checkbox(
                        "Mark as Complete", 
                        value=saved_status, 
                        key=f"chk_{week_num}"
                    )
                    
                    # Save state if changed
                    if is_checked != saved_status:
                        update_quest_status(week_num, is_checked)
                        st.rerun()
                    
        with col_side:
            with st.container(border=True):
                st.markdown("### MISSING SKILLS")
                for skill in st.session_state.missing_skills:
                    st.markdown(f"- {skill}")
    else:
        st.warning("No active quests found. Complete 'Character Creation' first to generate your AI roadmap.")

elif current_page == "3. Player Stats (Dashboard)":
    st.markdown("<h1>ANALYTICS DASHBOARD</h1>", unsafe_allow_html=True)
    
    # 1. Fetch the latest user profile data from SQLite
    cursor.execute("SELECT target_role, readiness_score, missing_skills FROM users ORDER BY id DESC LIMIT 1")
    user_data = cursor.fetchone()
    
    # 2. Fetch the total number of completed quests
    cursor.execute("SELECT COUNT(*) FROM quest_progress WHERE is_completed = 1")
    completed_quests = cursor.fetchone()[0]
    
    if user_data:
        target_role = user_data[0]
        readiness_score = int(user_data[1])
        missing_skills = json.loads(user_data[2])
        
        # Calculate dynamic gamified metrics
        xp_earned = completed_quests * 50  # 50 XP per completed week
        
        # Determine total weeks from active curriculum or default to length of missing skills
        total_weeks = len(st.session_state.curriculum.get("modules", [])) if st.session_state.curriculum else len(missing_skills)
        weeks_remaining = max(0, total_weeks - completed_quests)
        
        # Top Row: Dynamic KPIs
        m1, m2, m3 = st.columns(3)
        with m1:
            with st.container(border=True):
                st.metric("READINESS SCORE", f"{readiness_score}%")
        with m2:
            with st.container(border=True):
                st.metric("WEEKS TO COMPLETION", str(weeks_remaining))
        with m3:
            with st.container(border=True):
                st.metric("XP EARNED", str(xp_earned), f"{completed_quests} Quests Done")
                
        st.markdown("---")
        
        # Bottom Row: Real Data Visualizations
        c1, c2 = st.columns(2)
        
        with c1:
            with st.container(border=True):
                st.markdown("### PROGRESS TRAJECTORY")
                # Generate a real cumulative line chart based on quests finished
                if completed_quests > 0:
                    # Creates a list of XP growth: e.g., [0, 50, 100]
                    progress_data = [0] + [50 * i for i in range(1, completed_quests + 1)]
                    chart_data = pd.DataFrame(progress_data, columns=['Actual XP'])
                else:
                    chart_data = pd.DataFrame([0], columns=['Actual XP'])
                st.line_chart(chart_data)
                
        with c2:
            with st.container(border=True):
                st.markdown("### SKILL INVENTORY")
                # Build a dynamic bar chart comparing known (100%) vs missing (0%) skills
                req_skills = ROLE_TAXONOMY.get(target_role, set())
                skill_status = {}
                for skill in req_skills:
                    skill_status[skill] = 0 if skill in missing_skills else 100
                    
                bar_data = pd.DataFrame.from_dict(skill_status, orient='index', columns=['Mastery %'])
                st.bar_chart(bar_data)
                
    else:
        st.warning("No player data found. Please complete 'Character Creation' to initialize your stats.")