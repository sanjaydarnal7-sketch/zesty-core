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
from ZestyBrain.runtime_manager import RuntimeManager
from ZestyBrain.services.weather_service import WeatherService
from ZestyBrain.services.research_service import ResearchService
from ZestyBrain.services.tts_service import TTSService


logging.getLogger('wsgi').setLevel(logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__, static_folder=".")
app.logger.disabled = True
#endregion

# =====================================================================
#region 🛸 1. UNIVERSAL COGNITIVE POOL (LOCAL RUNTIME)
# =====================================================================
runtime_manager = RuntimeManager()
if not runtime_manager.is_ready():
    raise RuntimeError("Ollama runtime unavailable")

DB_DIR = "zesty_knowledge_base"
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

        self.weather_service = WeatherService()
        self.research_service = ResearchService()
        self.tts_service = TTSService()

        self.cleanup_audio()

    def cleanup_audio(self):
        try:
            subprocess.run(["pkill", "afplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists("zesty_reply.mp3"): os.remove("zesty_reply.mp3")
        except Exception: pass

    def get_live_weather(self):
        return self.weather_service.get_weather()

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
        return self.research_service.search(query)

    def execute_os_command_or_research(self, text: str) -> tuple:
        cleaned = text.lower()
        if "chrome" in cleaned or "browser" in cleaned:
            if "open" in cleaned or "kholo" in cleaned:
                subprocess.Popen(["open", "-a", "Google Chrome"])
                return True, "Opening Google Chrome, Boss."
        
        research_triggers = [
            "search",
            "find",
            "lookup",
            "research",
            "detail",
            "info",
            "strategy",
            "who is",
            "what is",
            "बताओ",
            "ढूंढो",
            "जानकारी",
            "कौन है",
            "क्या है",
            "dna",
            "flavour",
        ]

        if any(trigger in cleaned for trigger in research_triggers):
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

            print("\n" + "=" * 70)
            print("🗂 CHROMA RAW RESULT")
            print("-" * 70)
            print(results)
            print("=" * 70 + "\n")

            if results and results.get("documents") and results["documents"][0]:
                return results["documents"][0][0]

        except Exception as e:
            print("[CHROMA ERROR]", e)

        return ""

    def speak_text_edge_seamless(self, text_to_speak: str, current_lang: str):
        self.tts_service.speak(text_to_speak, current_lang)
#endregion

# =====================================================================
#region 🧠 3. INTENT-AWARE COGNITIVE LAYER
# =====================================================================

    def call_llm(self, user_prompt: str, local_context: str, web_intel: str) -> tuple:

        system_prompt = (
            "At the end of every reply append exactly one tag in the form: [TARGET_PANEL: panel_name].\n"
            "Allowed panels: panelSocial, panelFlavour, panelFamily, "
            "panelCraftsmen, panelDriver, panelRecipe, panelHelp, "
            "panelSearch, CLOSE, chat."
        )

        # Legacy personality injection disabled.
        # Chroma knowledge will be re-integrated through ZestyBrain.

        if local_context:
            system_prompt += (
                "\n\n"
                "### RELEVANT MEMORY ###\n"
                f"{local_context}\n"
                "### END MEMORY ###\n"
            )

        if web_intel:
            system_prompt += (
                "\n\n"
                "### WEB INTELLIGENCE ###\n"
                f"{web_intel}\n"
                "### END WEB ###\n"
            )

        try:

            llm_start = time.perf_counter()

            raw_reply = runtime_manager.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=1000,
            ) or ""

            llm_end = time.perf_counter()

            print(f"[⏱ LLM TIME] {llm_end - llm_start:.2f} sec")

            print("\n" + "=" * 70)
            print("🧠 ZESTY RAW REPLY")
            print("-" * 70)
            print(raw_reply)
            print("=" * 70 + "\n")

            panel_target = "chat"

            panel_match = re.search(
                r'\[TARGET_PANEL:\s*([A-Za-z_]+)\]',
                raw_reply,
            )

            if panel_match:
                panel_target = panel_match.group(1)
                raw_reply = re.sub(
                    r'\[TARGET_PANEL:\s*[A-Za-z_]+\]',
                    '',
                    raw_reply,
                ).strip()

            return raw_reply, panel_target

        except Exception as e:

            print(f"[⚠️ RUNTIME ERROR]: {e}")

            return (
                "System array disruption. Local neural core is temporarily unavailable.",
                "chat",
            )



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

    print(f"[TARGET PANEL] {target_panel}")
    print(f"[FINAL REPLY] {reply_text}")
    
    zesty_os.speak_text_edge_seamless(reply_text, lang_hint)

    return jsonify({
        "voice_text": reply_text,
        "dynamic_html": f"<div class='hermes-dynamic-content'>{reply_text}</div>",
        "open_panel": target_panel
    })
#endregion

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)