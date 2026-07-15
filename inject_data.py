#region 📦 SYSTEM IMPORTS
import os
import time
import requests
import chromadb
from chromadb.utils import embedding_functions
#endregion

# =====================================================================
#region 🛸 1. CONFIGURATION & DATABASE LAYER (Path & Collection Settings)
# =====================================================================
print("🛸 [ZESTY OS INTELLIGENCE]: LOADING VECTOR EMBEDDING ENGINE...")

# फ्री सेंटेंस-ट्रांसफॉर्मर मॉडल जो लोकल मैकबुक पर ही टेक्स्ट को न्यूमेरिकल वेक्टर्स में बदलता है
free_embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2") # type: ignore

# क्रोमा डेटाबेस का परमानेंट पाथ सेट करना
DB_DIR = "zesty_knowledge_base"
chroma_client = chromadb.PersistentClient(path=DB_DIR)

# मास्टर लेक्सिकॉन कलेक्शन बनाना या लोड करना
collection = chroma_client.get_or_create_collection(name="zesty_master_lexicon", embedding_function=free_embedding_model) # type: ignore
#endregion

# =====================================================================
#region 📡 2. GLOBAL DATA SYNC LAYER (Wikipedia API Integration)
# =====================================================================
def download_wikipedia_data(topic_title):
    """🌍 VERIFIED GLOBAL DATA SYNCER (Wikipedia API)"""
    print(f"📡 Downloading and verifying global data for: '{topic_title}'...")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic_title.replace(' ', '_')}"
    try:
        headers = {'User-Agent': 'ZestyOS/1.0 (sanjay@craftsmen.com)'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("extract", "")
    except Exception as e:
        print(f"❌ Verification Timeout for {topic_title}: {e}")
    return None
#endregion

# =====================================================================
#region 📋 3. INTEL TARGETS (Core Knowledge Topics Configuration)
# =====================================================================
# अगर भविष्य में नए टॉपिक्स जोड़ने या हटाने हों, तो सिर्फ इस लिस्ट को बदलें:
topics_to_download = [
    "Stock market", 
    "Technical analysis", 
    "Financial market", 
    "Trading strategy",
    "Hospitality industry", 
    "Mixology", 
    "Bartender", 
    "Restaurant management"
]
#endregion

# =====================================================================
#region 📥 4. VAULT INJECTION MECHANICS (Database Clean & Load)
# =====================================================================
downloaded_documents = []
downloaded_ids = []

# डेटाबेस को पूरी तरह साफ़ और ताज़ा करने के लिए एक बार पुराने नोड्स को डिलीट करने का लॉजिक
try:
    existing_count = collection.count()
    if existing_count > 0:
        print(f"🧹 Clearing {existing_count} legacy contaminated nodes from vault...")
        # री-इंजेक्शन से पहले क्लीन स्वीप ताकि पुराना कचरा पूरी तरह साफ़ हो जाए
        collection.delete(where={}) 
except Exception as e:
    pass

# डेटा डाउनलोड और एरे बिल्डिंग
for index, topic in enumerate(topics_to_download):
    text_content = download_wikipedia_data(topic)
    if text_content:
        downloaded_documents.append(text_content)
        # टाइमस्टैम्प के साथ एक यूनिक आईडी जनरेट करना
        downloaded_ids.append(f"master_node_{int(time.time())}_{index}")
    time.sleep(0.5) # सर्वर पर लोड न पड़े इसलिए छोटा सा पॉज

# 💾 क्रोमा डेटाबेस की तिजोरी में डेटा को इंजेक्ट करना
if downloaded_documents:
    collection.add(documents=downloaded_documents, ids=downloaded_ids)
    print("\n🏆 [GRAND SUCCESS]: CORE DATA BASELINES SECURED LOCALLY IN CHROMA VAULT!")
    print(f"📊 Total Active Verified Intelligence Nodes Loaded: {collection.count()}")
else:
    print("\n⚠️ Injection array empty. Please check internet connectivity.")
#endregion