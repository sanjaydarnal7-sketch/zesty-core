#region 📦 SYSTEM IMPORTS & LOGGING SETUP
import os
import json
import time
import subprocess
import asyncio
import re
import sys
import logging
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
import requests
from edge_tts import Communicate

from chromadb import EmbeddingFunction, Documents, Embeddings
import chromadb

logging.getLogger("wsgi").setLevel(logging.ERROR)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

app = Flask(__name__, static_folder=".")
app.logger.disabled = True
#endregion


# =====================================================================
#region 🛸 1. UNIVERSAL COGNITIVE POOL
# =====================================================================

# Read API Keys securely from Environment Variables
API_VAULT = [

    os.getenv("GROQ_API_KEY"),

]

# Remove empty / None values automatically
API_VAULT = [key for key in API_VAULT if key]

CURRENT_KEY_INDEX = 0


def get_active_groq_client():

    if not API_VAULT:
        raise RuntimeError(
            "No Groq API key found. Please set GROQ_API_KEY environment variable."
        )

    global CURRENT_KEY_INDEX

    from groq import Groq

    key = API_VAULT[CURRENT_KEY_INDEX]

    return Groq(api_key=key)


def rotate_to_next_brain():

    global CURRENT_KEY_INDEX

    if len(API_VAULT) <= 1:
        return

    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(API_VAULT)

    print(
        f"\n[🔄 STARK CORE ROTATION]: "
        f"Shifting neural transmission to Brain Key Node {CURRENT_KEY_INDEX + 1}"
    )


DB_DIR = "zesty_knowledge_base"

chroma_client = chromadb.PersistentClient(path=DB_DIR)
#endregion
chroma_client = chromadb.PersistentClient(path=DB_DIR)
JOURNAL_FILE = "boss_personal_journal.json"
CONVERSATION_HISTORY = []

class ZestyCloudEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> any: # type: ignore
        try:
            url = "https://feature-extraction.hf.space/embed"
            res = requests.post(url, json={"inputs": input}, timeout=3.0)
            if res.status_code == 200: return res.json()
        except Exception: pass
        return [[0.0] * 384 for _ in input]

cloud_embedding = ZestyCloudEmbeddingFunction()
collection = chroma_client.get_or_create_collection(name="zesty_master_lexicon_v4", embedding_function=cloud_embedding)
#endregion

# =====================================================================
#region 🎛️ 2. SYSTEM CORE MECHANICS (UPGRADED STARK RESEARCH ENGINE)
# =====================================================================
class ZestyCommercialOS:
    def __init__(self):
        self.boss_mode_active = False
        if not os.path.exists(JOURNAL_FILE):
            with open(JOURNAL_FILE, "w") as f: json.dump([], f)
        self.cleanup_audio()

    def cleanup_audio(self):
        try:
            subprocess.run(["pkill", "afplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists("zesty_reply.mp3"): os.remove("zesty_reply.mp3")
        except Exception: pass

    def get_live_weather(self):
        try:
            res = requests.get("https://wttr.in/Goa?format=%C+%t", timeout=2.0)
            if res.status_code == 200: return res.text.strip()
        except Exception: pass
        return "Clear Sky +29°C"

    def clean_phonetics_layer(self, text: str) -> str:
        text = re.sub(r'^(hi\s+)?justi[a-z]*\s+|^जैस्री\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'sukht[a-z]*|sukhd[a-z]*|palak\s+sukhta[a-z]*', 'Prahlad Sukhtankar', text, flags=re.IGNORECASE)
        return text.strip()

    def save_to_lexicon(self, data_text: str) -> str:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            doc_id = f"artifact_{int(time.time())}"
            collection.add(documents=[data_text], ids=[doc_id], metadatas=[{"timestamp": timestamp, "type": "user_experiment"}])
            return f"Understood, Sanjay Boss. मैंने इस डेटा को कोर लेक्सिकॉन मेमोरी में लॉक कर दिया है।"
        except Exception as e: return f"Memory storage node error: {str(e)}"

    def deep_internet_research(self, query: str) -> str:
        print(f"\n[🚀 DEEP SEARCH]: Scanning intelligence for -> {query}")
        try:
            # अपग्रेड: DuckDuckGo लाइट मोड पर शिफ्ट ताकि HTML कभी फेल न हो और डेटा तुरंत आए
            url = f"https://lite.duckduckgo.com/lite/"
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            res = requests.post(url, data={"q": query}, headers=headers, timeout=5.0)
            if res.status_code == 200:
                # स्लीक रेगेक्स पैटर्न जो डिस्क्रिप्शन ब्लॉक्स को आसानी से निकालता है
                snippets = re.findall(r'<td class="result-snippet">(.*?)</td>', res.text, re.DOTALL)
                cleaned = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:4]]
                if cleaned:
                    return "\n".join([f"• {s}" for s in cleaned])
        except Exception as e:
            print(f"[⚠️ SEARCH TELEMETRY]: Scraping node timed out. Reverting to base model knowledge.")
        return ""

    def execute_os_command_or_research(self, text: str) -> tuple:
        cleaned = text.lower()
        if "chrome" in cleaned or "browser" in cleaned:
            if "open" in cleaned or "kholo" in cleaned:
                subprocess.Popen(["open", "-a", "Google Chrome"])
                return True, "Opening Google Chrome, Boss."
        
        # रिसर्च ट्रिगर्स का दायरा बढ़ाया
        research_triggers = ["detail", "info", "search", "strategy", "बताओ", "ढूंढो", "dna", "flavour", "jankari", "who is", "bare mein"]
        if any(trigger in cleaned for trigger in research_triggers) or len(cleaned.split()) > 3:
            return False, self.deep_internet_research(text)
        return False, ""

    def build_dynamic_mood_greeting(self, user_input: str) -> str:
        weather = self.get_live_weather()
        current_hour = datetime.now().hour
        time_context = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"
        return f"{time_context}, Sanjay Boss! कॉकपिट पूरी तरह ऑप्टिमल स्टेट में है। Goa का मौसम अभी {weather} है। Ready to rule."

    def query_local_chroma_database(self, user_text: str) -> str:
        try:
            results = collection.query(query_texts=[user_text], n_results=1)
            if results and results['documents'] and results['documents'][0]: return results['documents'][0][0]
        except Exception: pass
        return ""

    def speak_text_edge_seamless(self, text_to_speak: str, current_lang: str):
        output_audio = "zesty_reply.mp3"
        voice = "en-IN-NeerjaNeural" if current_lang == "english" else "hi-IN-SwaraNeural"
        
        subprocess.run(["pkill", "afplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(output_audio):
            try: os.remove(output_audio)
            except Exception: pass

        async def amain():
            communicate = Communicate(text_to_speak, voice, rate="+8%", pitch="+10Hz")
            await communicate.save(output_audio)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(amain())
            loop.close()
            subprocess.Popen(["afplay", output_audio], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Audio Playback Error: {e}")
#endregion

# =====================================================================
#region 🧠 3. INTENT-AWARE COGNITIVE LAYER
# =====================================================================
    def call_llm(self, user_prompt: str, local_context: str, web_intel: str) -> tuple:
        global CONVERSATION_HISTORY
        system_prompt = (
            "You are ZESTY OS, an advanced operational intelligence network built for Sanjay Boss (Sanjay Darnal).\n"
            "CRITICAL RULES:\n"
            "1. You are strictly a FEMALE AI entity. Always use strict female verbs ('karti hoon', 'samjhati hoon').\n"
            "2. At the very end of your response, you MUST append: [TARGET_PANEL: panel_name]\n"
            "Choose 'panel_name' from: panelSocial, panelFlavour, panelFamily, panelCraftsmen, panelDriver, panelRecipe, panelHelp, panelSearch, CLOSE, chat.\n"
            "Tone: Polished, authoritative female Hinglish matching Sanjay Boss's energy."
        )
        
        if local_context: system_prompt += f"\n[CONTEXT]: {local_context}"
        if web_intel: system_prompt += f"\n[WEB INTEL]: {web_intel}"

        messages = [{"role": "system", "content": str(system_prompt)}]
        for hist in CONVERSATION_HISTORY[-4:]: messages.append(hist)
        messages.append({"role": "user", "content": str(user_prompt)})

        attempts = 0
        while attempts < len(API_VAULT):
            try:
                client = get_active_groq_client()
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages, # type: ignore
                    temperature=0.1,
                    max_tokens=1000
                )
                raw_reply = completion.choices[0].message.content or ""
                
                panel_target = "chat"
                panel_match = re.search(r'\[TARGET_PANEL:\s*([A-Za-z_]+)\]', raw_reply)
                if panel_match:
                    panel_target = panel_match.group(1)
                    raw_reply = re.sub(r'\[TARGET_PANEL:\s*[A-Za-z_]+\]', '', raw_reply).strip()

                CONVERSATION_HISTORY.append({"role": "user", "content": user_prompt})
                CONVERSATION_HISTORY.append({"role": "assistant", "content": raw_reply})
                if len(CONVERSATION_HISTORY) > 8: CONVERSATION_HISTORY.pop(0)
                
                return raw_reply, panel_target
            except Exception:
                rotate_to_next_brain()
                attempts += 1
        return "System array disruption. All core neural nodes are temporarily exhausted.", "chat"

zesty_os = ZestyCommercialOS()
#endregion

# =====================================================================
#region 🌐 4. NETWORK ROUTES & ENDPOINTS
# =====================================================================
@app.route("/")
def index():
    try:
        return send_from_directory("templates", "index.html")
    except Exception as e:
        return f"Zesty OS Cockpit Error: {str(e)}"

@app.route("/ask_hermes", methods=["POST"])
def ask_hermes_endpoint():
    print(f"\n[DEBUG BACKEND]: /ask_hermes endpoint hit - Connection VERIFIED from frontend")
    data = request.json or {}
    print(f"[DEBUG BACKEND]: Request data received -> {data}")
    
    raw_input = str(data.get("user_input", ""))
    cleaned_input = zesty_os.clean_phonetics_layer(raw_input)
    lower_input = cleaned_input.lower()

    if any(kw in lower_input for kw in ["stop", "ruko", "cancel"]):
        subprocess.run(["pkill", "afplay"])
        return jsonify({"voice_text": "Stopped", "dynamic_html": "Playback stopped.", "open_panel": "CLOSE"})

    lang_hint = "english" if re.match(r'^[A-Za-z0-9\s.,!?\'"\-]+$', cleaned_input) else "hinglish"

    if any(kw in lower_input for kw in ["daddy", "home", "duty", "जैस्री"]) and not zesty_os.boss_mode_active:
        zesty_os.boss_mode_active = True
        greeting = zesty_os.build_dynamic_mood_greeting(raw_input)
        zesty_os.speak_text_edge_seamless(greeting, lang_hint)
        return jsonify({"voice_text": greeting, "dynamic_html": greeting, "open_panel": "chat"})

    is_os_cmd, output_intel = zesty_os.execute_os_command_or_research(cleaned_input)
    if is_os_cmd:
        zesty_os.speak_text_edge_seamless(output_intel, "english")
        return jsonify({"voice_text": output_intel, "dynamic_html": output_intel, "open_panel": "chat"})

    local_context = zesty_os.query_local_chroma_database(cleaned_input)
    reply_text, target_panel = zesty_os.call_llm(cleaned_input, local_context, output_intel)
    
    zesty_os.speak_text_edge_seamless(reply_text, lang_hint)

    return jsonify({
        "voice_text": reply_text,
        "dynamic_html": f"<div class='hermes-dynamic-content'>{reply_text}</div>",
        "open_panel": target_panel
    })
#endregion

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)