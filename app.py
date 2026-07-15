import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
import requests
import time
import datetime
import folium
from streamlit_folium import st_folium

# --- Page Configuration ---
st.set_page_config(page_title="ZESTY OS • Your World. Your AI.", page_icon="🧬", layout="wide", initial_sidebar_state="collapsed")

# --- Claude CSS Configuration - ZOEY OS HUD ---
ZOEY_OS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

html, body, .stApp {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
    background: #000000 !important;
}
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewContainer"] > .main,
section.main {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}
div.block-container {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
    padding: 0 !important;
}
#MainMenu, header, footer, div[data-testid="stDecoration"] { display: none !important; }

.stApp, .stApp * {
    font-family: 'JetBrains Mono', monospace !important;
}
.stApp p, .stApp span, .stApp div, .stApp label, .hud-data, .hud-title {
    font-size: 11px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #FFFFFF !important;
}

.hud-title {
    position: relative !important;
    display: inline-block !important;
    padding-right: 16px !important;
    color: #FF6D00 !important;
    border-bottom-color: rgba(255, 109, 0, 0.25) !important;
}
.hud-title::after {
    content: "";
    position: absolute;
    right: 0;
    top: 2px;
    width: 6px;
    height: 11px;
    background: #FF6D00;
    animation: zoey-blink 1.1s steps(1) infinite;
}
@keyframes zoey-blink { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }

div[data-testid="stAppViewContainer"] div[data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: 24% 52% 24% !important;
    gap: 1rem !important;
    padding: 1.5rem !important;
    height: 100% !important;
    max-height: 100vh !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
    width: auto !important;
    min-width: 0 !important;
    flex: unset !important;
    height: 100% !important;
    overflow: hidden !important;
}
div[data-testid="stColumn"] div[data-testid="stVerticalBlock"] {
    height: 100% !important;
}

.hud-panel {
    background: rgba(10, 10, 12, 0.7) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 109, 0, 0.12) !important;
    border-radius: 6px !important;
    box-shadow: 0 0 24px rgba(255, 109, 0, 0.06) !important;
    padding: 12px !important;
    margin-bottom: 10px;
}
.hud-panel.sealed { border-color: rgba(255, 140, 66, 0.4) !important; }
.highlight-cyan, .highlight-amber, .highlight-magenta { color: #FF8C42 !important; }

.core-container {
    position: relative !important;
    background: #000000 !important;
    border-radius: 12px !important;
    height: 75% !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
}
.core-container::before {
    content: "";
    position: absolute;
    width: 420px;
    height: 420px;
    border-radius: 50%;
    background: conic-gradient(from 0deg,
        transparent 0%, rgba(255,109,0,0.35) 15%, transparent 35%,
        rgba(255,140,66,0.25) 55%, transparent 75%, rgba(255,109,0,0.35) 95%, transparent 100%);
    animation: zoey-vortex-spin 6s linear infinite;
    filter: blur(1px);
    z-index: 0;
}
.core-container::after {
    content: "";
    position: absolute;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    background: conic-gradient(from 180deg,
        transparent 0%, rgba(255,140,66,0.4) 20%, transparent 40%,
        rgba(255,109,0,0.3) 65%, transparent 90%);
    animation: zoey-vortex-spin 4s linear infinite reverse;
    z-index: 0;
}
.vortex-core, .vortex-fallback { position: relative !important; z-index: 2 !important; }
@keyframes zoey-vortex-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

div[data-testid="stChatInput"] {
    background: rgba(10, 10, 12, 0.75) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 109, 0, 0.35) !important;
    border-radius: 999px !important;
    box-shadow: 0 0 26px rgba(255, 109, 0, 0.18) !important;
    padding: 4px 14px !important;
    max-width: 480px !important;
    margin: 20px auto 0 auto !important;
}
div[data-testid="stChatInput"] textarea {
    color: #FFFFFF !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.08em !important;
}
.hud-data { line-height: 1.55 !important; }
.map-container { margin-top: 8px; border-radius: 4px; overflow: hidden; }
</style>
"""
st.markdown(ZOEY_OS_CSS, unsafe_allow_html=True)

# --- TIME-AWARE GREETING FUNCTION ---
def get_time_aware_greeting(name="COMMANDER SANJAY"):
    """Generate elite, minimalist greeting based on current system time."""
    current_hour = datetime.datetime.now().hour
    
    if 5 <= current_hour < 12:
        return f"CORE INITIALIZED. GOOD MORNING {name}."
    elif 12 <= current_hour < 17:
        return f"CORE INITIALIZED. GOOD AFTERNOON {name}."
    elif 17 <= current_hour < 22:
        return f"CORE INITIALIZED. GOOD EVENING {name}."
    else:
        return "SYSTEM REST MODE ACTIVE. GOOD EVENING."

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "provider" not in st.session_state:
    st.session_state.provider = "Google Gemini"
if "credentials" not in st.session_state:
    st.session_state.credentials = {
        "Google Gemini": "",
        "OpenAI ChatGPT": "",
        "Anthropic Claude": "",
        "Local/Ollama": "",
    }
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "elevenlabs_api_key" not in st.session_state:
    st.session_state.elevenlabs_api_key = ""
if "voice_id" not in st.session_state:
    st.session_state.voice_id = "pNInz6obpgmA5mW3s7rC"
if "guest_name" not in st.session_state:
    st.session_state.guest_name = ""
if "hospitality_mode" not in st.session_state:
    st.session_state.hospitality_mode = False
if "welcome_ready" not in st.session_state:
    st.session_state.welcome_ready = False
if "welcome_text" not in st.session_state:
    st.session_state.welcome_text = ""
if "system_log" not in st.session_state:
    st.session_state.system_log = []
if "audio_cache_key" not in st.session_state:
    st.session_state.audio_cache_key = None

# --- HIGH-DENSITY LIFESTYLE LOGS STATE ---
if "diet_log" not in st.session_state:
    st.session_state.diet_log = {"breakfast": "", "lunch": "", "dinner": "", "snacks": ""}
if "rest_cycles" not in st.session_state:
    st.session_state.rest_cycles = {"sleep_hours": 0.0, "rest_state": "ACTIVE"}

# --- SOCIAL MEDIA TELEMETRY STATE ---
if "social_telemetry" not in st.session_state:
    st.session_state.social_telemetry = {
        "instagram": {"status": "DISCONNECTED", "notifications": 0},
        "facebook": {"status": "DISCONNECTED", "notifications": 0},
        "x": {"status": "DISCONNECTED", "notifications": 0}
    }

# --- GEO-SPATIAL STATE ---
if "user_location" not in st.session_state:
    st.session_state.user_location = {"lat": 15.6644, "lon": 73.6141, "city": "Goa, India"}

# --- CRITICAL STATE LOCKS: Prevent 429 infinite loop ---
if "processing_gemini_request" not in st.session_state:
    st.session_state.processing_gemini_request = False
if "processing_elevenlabs_request" not in st.session_state:
    st.session_state.processing_elevenlabs_request = False
if "gemini_response" not in st.session_state:
    st.session_state.gemini_response = ""
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = b""
if "audio_mime_type" not in st.session_state:
    st.session_state.audio_mime_type = "audio/wav"
if "last_user_action_time" not in st.session_state:
    st.session_state.last_user_action_time = 0

# --- Helper Functions ---

def normalize_audio_input(audio_value) -> tuple[bytes, str]:
    """Normalizes various audio input formats from Streamlit's audio_input widget."""
    if audio_value is None:
        return b"", "audio/wav"
    if isinstance(audio_value, dict):
        data = audio_value.get("data")
        if isinstance(data, (bytes, bytearray)):
            fmt = audio_value.get("format") or audio_value.get("mime_type") or "audio/wav"
            return bytes(data), fmt
    if hasattr(audio_value, "data"):
        data = getattr(audio_value, "data", None)
        if isinstance(data, (bytes, bytearray)):
            fmt = getattr(audio_value, "format", None) or getattr(audio_value, "mime_type", None) or "audio/wav"
            return bytes(data), fmt
    if hasattr(audio_value, "get"):
        data = audio_value.get("data")
        if isinstance(data, (bytes, bytearray)):
            fmt = audio_value.get("format") or audio_value.get("mime_type") or "audio/wav"
            return bytes(data), fmt
    return b"", "audio/wav"

def generate_gemini_response(prompt: str, audio_bytes: bytes = b"", mime_type: str = "audio/wav") -> str:
    """Generates a response from local Hermes 3 via Ollama with Jarvis protocols."""
    import urllib.request
    import json

    # पक्का करना कि यूजर ने कुछ इनपुट दिया है
    if not prompt and not audio_bytes:
        return ""

    # CRITICAL: Check state lock before proceeding
    if st.session_state.processing_gemini_request:
        return ""

    st.session_state.processing_gemini_request = True

    try:
        url = "http://localhost:11434/api/chat"
        
        # आपका डायनामिक सिस्टम इंस्ट्रक्शन (लाइफस्टाइल और जियोलोकेशन डेटा के साथ)
        system_instruction = build_system_instruction()
        
        # जार्विस का स्पेशल टोनी स्टार्क प्रोटोकॉल इसमें जोड़ना
        jarvis_protocol = (
            f"{system_instruction}\n\n"
            "CRITICAL PROTOCOLS:\n"
            "1. VOICE FIRST: Keep your response concise, punchy, and natural for speech.\n"
            "2. DYNAMIC UI GENERATION: If the user asks for historical records, memory data, or complex lists, "
            "you must include a clean HTML container wrap. Structure your internal logic to pass data safely."
        )

        payload = {
            "model": "hermes3",
            "messages": [
                {"role": "system", "content": jarvis_protocol},
                {"role": "user", "content": prompt if prompt else "Listen to this audio command."}
            ],
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }

        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"), 
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            full_text = res_data.get("message", {}).get("content", "")
            
            # बैकएंड को सिंक रखने के लिए zesty_state.json को अपडेट करना
            try:
                # चेक करना कि क्या हरमिस ने कोई खास स्ट्रक्चर भेजा है
                with open("zesty_state.json", "w") as f:
                    json.dump({
                        "trigger_3d_mesh": True if "<div" in full_text else False,
                        "voice_text": full_text,
                        "dynamic_html": full_text if "<div" in full_text else "",
                        "engine_state": "state-hermes"
                    }, f, indent=4)
            except Exception:
                pass
                
            st.session_state.system_log.append("MODEL SELECTED: hermes3 (Local)")
            return full_text

    except Exception as exc:
        st.session_state.system_log.append(f"Local Engine Error: {str(exc)}")
        return f"Sir, I encountered an issue connecting to the local Hermes engine: {str(exc)}"
        
    finally:
        st.session_state.processing_gemini_request = False

def build_system_instruction() -> str:
    """Build comprehensive system instruction with lifestyle and geospatial context."""
    diet_info = st.session_state.get("diet_log", {})
    rest_info = st.session_state.get("rest_cycles", {})
    location_info = st.session_state.get("user_location", {})
    
    instruction = """You are ZESTY OS, an elite AI assistant with JARVIS-style capabilities. 
Respond with precision and minimalism. Use uppercase for system outputs.

CURRENT CONTEXT:
"""
    
    # Add lifestyle context
    if diet_info:
        instruction += f"\nLIFESTYLE LOGS:\n"
        instruction += f"- Breakfast: {diet_info.get('breakfast', 'Not logged')}\n"
        instruction += f"- Lunch: {diet_info.get('lunch', 'Not logged')}\n"
        instruction += f"- Dinner: {diet_info.get('dinner', 'Not logged')}\n"
        instruction += f"- Sleep Hours: {rest_info.get('sleep_hours', 0)} hours\n"
        instruction += f"- Rest State: {rest_info.get('rest_state', 'ACTIVE')}\n"
    
    # Add geospatial context
    if location_info:
        instruction += f"\nGEOLOCATION:\n"
        instruction += f"- City: {location_info.get('city', 'Unknown')}\n"
        instruction += f"- Coordinates: {location_info.get('lat', 0)}°N, {location_info.get('lon', 0)}°E\n"
    
    return instruction

def generate_elevenlabs_audio(text: str) -> bytes:
    """Generates audio from text using ElevenLabs API with 429 handling."""
    if not st.session_state.elevenlabs_api_key.strip():
        raise RuntimeError("No ElevenLabs API key available.")

    # CRITICAL: Check state lock before proceeding
    if st.session_state.processing_elevenlabs_request:
        return b""

    st.session_state.processing_elevenlabs_request = True
    
    try:
        voice_ids = [
            st.session_state.voice_id,
            "21m00Tcm4TlvDq8ikWAM",
            "ErXwobaYiN019PkySvjV",
        ]
        headers = {
            "xi-api-key": st.session_state.elevenlabs_api_key,
            "Content-Type": "application/json",
        }
        payload = {"text": text, "model_id": "eleven_multilingual_v2"}
        last_exception = None

        for voice_id in voice_ids:
            endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            try:
                response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                return response.content
            except Exception as exc:
                last_exception = exc
                error_message = str(exc).lower()
                if "429" in error_message or "resource exhausted" in error_message:
                    st.warning("ElevenLabs is cooling down. Please wait...")
                    return b""
                st.session_state.system_log.append(f"ElevenLabs voice {voice_id} failed: {exc}")
                continue

        raise RuntimeError(f"ElevenLabs audio generation failed for all voice IDs. Last error: {last_exception}")
    finally:
        st.session_state.processing_elevenlabs_request = False

# --- Authentication Flow ---
if not st.session_state.authenticated:
    st.markdown('<div class="hud-panel" style="max-width: 400px; margin: 5rem auto; padding: 2rem; position: relative;"><span class="hud-title" style="display: block; text-align: center; letter-spacing: 0.2em;">UNIVERSAL API GATEWAY</span></div>', unsafe_allow_html=True)
    with st.form(key="gateway_form"):
        provider = st.selectbox(
            "Select API Provider",
            ["Google Gemini", "OpenAI ChatGPT", "Anthropic Claude", "Local/Ollama"],
            index=["Google Gemini", "OpenAI ChatGPT", "Anthropic Claude", "Local/Ollama"].index(st.session_state.provider),
        )
        st.session_state.provider = provider
        provider_key = st.text_input(f"{provider} API Key", st.session_state.credentials.get(provider, ""))
        st.session_state.credentials[provider] = provider_key
        if provider == "Google Gemini":
            st.session_state.api_key = provider_key
        st.session_state.elevenlabs_api_key = st.text_input("ElevenLabs API Key", st.session_state.elevenlabs_api_key)
        st.session_state.voice_id = st.text_input("Voice ID", st.session_state.voice_id)
        access_pass = st.text_input("Access Passcode", type="password")
        initialized = st.form_submit_button("Initialize Core")
        if initialized:
            if (
                st.session_state.api_key.strip()
                and st.session_state.elevenlabs_api_key.strip()
                and st.session_state.voice_id.strip()
                and access_pass.strip()
            ):
                st.session_state.authenticated = True
                st.session_state.welcome_ready = True
                st.session_state.welcome_text = "Welcome to Zesty OS. Core online and ready for secure operation."
                st.session_state.system_log.append("SYSTEM: Core initialization complete. Gateway unlocked.")
            else:
                st.error("Initialization failed. Ensure all credentials and passcode are provided.")
    st.stop()

# --- MAIN HUD DASHBOARD - THREE COLUMN GRID ---
st.markdown('<div data-testid="stHorizontalBlock">', unsafe_allow_html=True)

# --- LEFT COLUMN: Commander Panel + Flavour DNA Lab + Lifestyle Logs ---
st.markdown('<div data-testid="stColumn"><div data-testid="stVerticalBlock">', unsafe_allow_html=True)

# Time-Aware Greeting Display
greeting = get_time_aware_greeting()
st.markdown(f'<div class="hud-panel"><span class="hud-title">SYSTEM STATUS</span><div class="hud-data" style="text-align: center;">{greeting}</div></div>', unsafe_allow_html=True)

# Commander Panel
st.markdown('<div class="hud-panel"><span class="hud-title">COMMANDER</span><div class="hud-data">', unsafe_allow_html=True)
st.markdown(f"""
<div class="hud-data" style="display: grid; gap: 6px;">
    <div><span class="highlight-cyan">Operator:</span> Sanjay Darnal</div>
    <div><span class="highlight-cyan">Role:</span> Director of Operations</div>
    <div><span class="highlight-cyan">Corp:</span> Craftsmen & Co.</div>
    <div><span class="highlight-cyan">Fatigue:</span> <span class="highlight-magenta">Nominal</span></div>
    <div><span class="highlight-cyan">Hydration:</span> <span class="highlight-magenta">1.8L/3.0L</span></div>
</div>
""", unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)

# Flavour DNA Lab
st.markdown('<div class="hud-panel"><span class="hud-title">FLAVOUR DNA LAB</span><div class="hud-data">', unsafe_allow_html=True)
st.markdown(f"""
<div class="hud-data" style="display: grid; gap: 6px;">
    <div><span class="highlight-cyan">Sys-Mode:</span> <span class="highlight-magenta">GOD MODE CORE</span></div>
    <div><span class="highlight-cyan">Salinity:</span> 0.42 Hz</div>
    <div><span class="highlight-cyan">Umami:</span> 89.4%</div>
    <div><span class="highlight-cyan">Acidic:</span> 3.1 pH</div>
    <div><span class="highlight-cyan">Menu:</span> Geological Framework</div>
</div>
""", unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)

# HIGH-DENSITY LIFESTYLE LOGS
st.markdown('<div class="hud-panel"><span class="hud-title">LIFESTYLE MONITOR</span><div class="hud-data">', unsafe_allow_html=True)
st.markdown('<div style="display: grid; gap: 8px;">', unsafe_allow_html=True)

# Diet Monitor
st.markdown('<div><span class="highlight-cyan">DIET MONITOR:</span></div>', unsafe_allow_html=True)
col_b, col_l, col_d = st.columns(3)
with col_b:
    breakfast_input = st.text_input("Breakfast", st.session_state.diet_log.get("breakfast", ""), key="diet_b", label_visibility="collapsed")
with col_l:
    lunch_input = st.text_input("Lunch", st.session_state.diet_log.get("lunch", ""), key="diet_l", label_visibility="collapsed")
with col_d:
    dinner_input = st.text_input("Dinner", st.session_state.diet_log.get("dinner", ""), key="diet_d", label_visibility="collapsed")

st.session_state.diet_log["breakfast"] = breakfast_input
st.session_state.diet_log["lunch"] = lunch_input
st.session_state.diet_log["dinner"] = dinner_input

# Rest Cycles
st.markdown('<div><span class="highlight-cyan">REST CYCLES:</span></div>', unsafe_allow_html=True)
sleep_hours = st.number_input("Sleep (hrs)", value=float(st.session_state.rest_cycles.get("sleep_hours", 0.0)), min_value=0.0, max_value=24.0, step=0.5, key="sleep_hrs", label_visibility="collapsed")
rest_state = st.selectbox("Rest State", ["ACTIVE", "RESTING", "RECOVERY"], index=["ACTIVE", "RESTING", "RECOVERY"].index(st.session_state.rest_cycles.get("rest_state", "ACTIVE")), key="rest_state", label_visibility="collapsed")

st.session_state.rest_cycles["sleep_hours"] = sleep_hours
st.session_state.rest_cycles["rest_state"] = rest_state

st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)

# --- CENTER COLUMN: Vortex Core + ZESTY OS Title + Chat Input ---
st.markdown('<div data-testid="stColumn"><div data-testid="stVerticalBlock">', unsafe_allow_html=True)

# ZESTY OS Title
st.markdown('<div class="core-container"><div class="vortex-core">', unsafe_allow_html=True)
st.markdown('<div class="hud-title" style="text-align: center; margin-bottom: 20px;">ZESTY OS</div>', unsafe_allow_html=True)

# Vortex Core Canvas
st.markdown('<div class="vortex-fallback" style="position: relative; z-index: 2;">', unsafe_allow_html=True)

# Three.js Particle Vortex HTML
particle_vortex_html = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body style="margin: 0; padding: 0; background: #000000; overflow: hidden;">
    <canvas id="vortexCanvas" style="display: block;"></canvas>
    <script>
        const canvas = document.getElementById('vortexCanvas');
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true });
        renderer.setSize(420, 420);
        
        // Particle system for vortex
        const particlesCount = 800;
        const particles = new Float32Array(particlesCount * 3);
        const colors = new Float32Array(particlesCount * 3);
        
        for (let i = 0; i < particlesCount; i++) {
            const i3 = i * 3;
            const radius = 4 + Math.random() * 2;
            const angle = (i / particlesCount) * Math.PI * 2;
            const height = Math.sin(angle * 3) * 2;
            
            particles[i3] = Math.cos(angle) * radius;
            particles[i3 + 1] = height;
            particles[i3 + 2] = Math.sin(angle) * radius;
            
            // Blend #FF6D00 and #FF8C42
            const mix = Math.random();
            colors[i3] = 1.0;
            colors[i3 + 1] = 0.42 + mix * 0.15;
            colors[i3 + 2] = 0.0 + mix * 0.32;
        }
        
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(particles, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        
        const material = new THREE.PointsMaterial({
            size: 0.08,
            vertexColors: true,
            transparent: true,
            opacity: 0.9,
            blending: THREE.AdditiveBlending
        });
        
        const points = new THREE.Points(geometry, material);
        scene.add(points);
        
        camera.position.z = 10;
        
        // Smooth rotation with pulsing
        let time = 0;
        function animate() {
            requestAnimationFrame(animate);
            time += 0.01;
            
            points.rotation.x = time * 0.2;
            points.rotation.y = time * 0.3;
            points.rotation.z = time * 0.1;
            
            // Gentle pulsing
            material.opacity = 0.7 + Math.sin(time * 2) * 0.2;
            
            renderer.render(scene, camera);
        }
        animate();
    </script>
</body>
</html>
"""

components.html(particle_vortex_html, height=420, width=420)
st.markdown('</div></div>', unsafe_allow_html=True)

# Chat Input - positioned below vortex
st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
user_command = st.chat_input("Enter command or message", key="core_command")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)

# --- RIGHT COLUMN: Telemetry & Sovereign Shield + Social Syndication ---
st.markdown('<div data-testid="stColumn"><div data-testid="stVerticalBlock">', unsafe_allow_html=True)

# Sovereign Shield
st.markdown('<div class="hud-panel sealed"><span class="hud-title">SHIELD</span><div class="hud-data">', unsafe_allow_html=True)
st.markdown(f"""
<div class="hud-data" style="display: grid; gap: 6px;">
    <div><span class="highlight-cyan">Status:</span> <span class="highlight-magenta">Shielded</span></div>
    <div><span class="highlight-cyan">Mode:</span> Hospitality</div>
</div>
""", unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)

# Telemetry
st.markdown('<div class="hud-panel"><span class="hud-title">TELEMETRY</span><div class="hud-data">', unsafe_allow_html=True)
st.markdown(f"""
<div class="hud-data" style="display: grid; gap: 6px;">
    <div><span class="highlight-cyan">Location:</span> Goa, India</div>
    <div><span class="highlight-cyan">Lat:</span> 15.6644 N</div>
    <div><span class="highlight-cyan">Long:</span> 73.6141 E</div>
    <div><span class="highlight-cyan">Weather:</span> Light Drizzle</div>
    <div><span class="highlight-cyan">Temp:</span> 26°C</div>
</div>
""", unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)

# SOCIAL MEDIA TELEMETRY HUB
st.markdown('<div class="hud-panel"><span class="hud-title">SOCIAL SYNDICATION</span><div class="hud-data">', unsafe_allow_html=True)
st.markdown('<div style="display: grid; gap: 8px;">', unsafe_allow_html=True)

# Instagram
ig_status = st.session_state.social_telemetry.get("instagram", {}).get("status", "DISCONNECTED")
ig_notif = st.session_state.social_telemetry.get("instagram", {}).get("notifications", 0)
st.markdown(f'<div><span class="highlight-cyan">IG:</span> [{ig_status}] Connection Stable. [{ig_notif}] Pending Alerts.</div>', unsafe_allow_html=True)

# Facebook
fb_status = st.session_state.social_telemetry.get("facebook", {}).get("status", "DISCONNECTED")
fb_notif = st.session_state.social_telemetry.get("facebook", {}).get("notifications", 0)
st.markdown(f'<div><span class="highlight-cyan">FB:</span> [{fb_status}] Connection Stable. [{fb_notif}] Pending Alerts.</div>', unsafe_allow_html=True)

# X (Twitter)
x_status = st.session_state.social_telemetry.get("x", {}).get("status", "DISCONNECTED")
x_notif = st.session_state.social_telemetry.get("x", {}).get("notifications", 0)
st.markdown(f'<div><span class="highlight-cyan">X:</span> [{x_status}] Connection Stable. [{x_notif}] Pending Alerts.</div>', unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)

# GEO-SPATIAL MAP MATRIX
st.markdown('<div class="hud-panel"><span class="hud-title">MAP MATRIX</span><div class="hud-data">', unsafe_allow_html=True)

# Create folium map centered on Goa
m = folium.Map(
    location=[15.6644, 73.6141],
    zoom_start=12,
    tiles="CartoDB dark",
    width=320,
    attr="Map data",
    height=200
)
folium.Marker([15.6644, 73.6141], popup="Goa, India", icon=folium.Icon(color="orange", icon="map-marker-alt")).add_to(m)

st_folium(m, width=320, height=200, key="map_display")

st.markdown('<div><span class="highlight-cyan">Coordinates:</span> 15.6644°N, 73.6141°E</div>', unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)

# --- End Grid Container ---
st.markdown('</div>', unsafe_allow_html=True)

# --- FLOATING SYSTEM LOG ---
if st.session_state.system_log:
    st.markdown('<div style="position: fixed; bottom: 100px; left: 50%; transform: translateX(-50%); width: 400px; max-height: 100px; overflow-y: auto; background: rgba(10, 10, 12, 0.7); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255, 109, 0, 0.12); border-radius: 12px; padding: 0.75rem; pointer-events: none; z-index: 1000;">', unsafe_allow_html=True)
    for log in st.session_state.system_log[-3:]:
        st.markdown(f'<div style="font-size: 11px; color: #888888; letter-spacing: 0.05em; margin: 2px 0;">{log}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- CHAT LOGIC WITH STATE GUARDS ---
# CRITICAL: Only process when user_command exists AND no other processing is happening
if user_command and not st.session_state.processing_gemini_request and not st.session_state.processing_elevenlabs_request:
    st.session_state.system_log.append(f"USER: {user_command}")
    
    # Process with Gemini - wrapped in try-except for 429 handling
    try:
        with st.spinner("Processing..."):
            response = generate_gemini_response(user_command)
            if response:
                st.session_state.system_log.append(f"ZESTY: {response[:100]}...")
                
                # Generate audio response - only if not already processing
                if not st.session_state.processing_elevenlabs_request:
                    audio_bytes = generate_elevenlabs_audio(response)
                    if audio_bytes:
                        st.session_state.audio_bytes = audio_bytes
                        st.session_state.audio_mime_type = "audio/wav"
    except Exception as e:
        error_msg = str(e)
        st.session_state.system_log.append(f"ERROR: {error_msg[:50]}")
        if "429" in error_msg.lower() or "resource exhausted" in error_msg.lower():
            st.warning("Zesty is cooling down. Re-initializing core in a few seconds...")