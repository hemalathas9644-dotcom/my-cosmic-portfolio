import streamlit as st
import pandas as pd
import time
from PIL import Image
import pytesseract
import requests
from gtts import gTTS
from io import BytesIO
from openai import OpenAI

# ---------------- API Setup ----------------
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",  # Replace with your valid API key
)

# ---------------- Load Data ----------------
file_path = "health2_post.xlsx"
data = pd.read_excel(file_path)
image_urls = data['displayUrl']
captions = data['caption']

# ---------------- App Header ----------------
st.title("📲 Real-Time Instagram Fake News Checker (Auto Mode)")

# ---------------- State Setup ----------------
if 'index' not in st.session_state:
    st.session_state.index = 0
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = time.time()

refresh_interval = 10  # seconds

# ---------------- Time-Based Auto-Cycling ----------------
current_time = time.time()
if current_time - st.session_state.last_updated > refresh_interval:
    st.session_state.index = (st.session_state.index + 1) % len(image_urls)
    st.session_state.last_updated = current_time
    st.rerun()

# ---------------- Load Current Post ----------------
idx = st.session_state.index
current_url = image_urls[idx]
current_caption = captions[idx]

# ---------------- Display Image and Caption ----------------
response = requests.get(current_url)
if response.status_code == 200:
    image = Image.open(BytesIO(response.content))
    st.image(image, caption=current_caption, use_container_width=True)
else:
    st.error("❌ Failed to load image.")
    st.stop()

# ---------------- OCR + Caption Merge ----------------
extracted_text = pytesseract.image_to_string(image, lang="eng+tam+tel")
combined_text = f"{extracted_text.strip()} {current_caption.strip()}".strip()
if len(combined_text) > 3000:
    combined_text = combined_text[:3000]

# ---------------- DeepSeek AI Prompt ----------------
messages = [{
    "role": "user",
    "content": f"""
Instruction:
You are an AI model that categorizes and verifies health and finance-related information.

Categorize into:
- Health
- Finance
- Other (skip analysis)

If Health or Finance:
- Category: Health / Finance
- Verdict: ✅ True | ❌ False | ⚠️ Uncertain
- Reasoning
- Confidence Score (0–100%)

Input: {combined_text}
"""
}]

# ---------------- DeepSeek API Call ----------------
try:
    completion = client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=messages
    )
    response_text = completion.choices[0].message.content
except Exception as e:
    st.error(f"⚠️ API call failed: {e}")
    st.stop()

# ---------------- Parse AI Response ----------------
def extract(key, text, fallback="N/A"):
    try:
        return text.split(f"{key}:")[1].split("\n")[0].strip().replace("*", "")
    except:
        return fallback

category = extract("Category", response_text)
verdict = extract("Verdict", response_text)
reasoning = extract("Reasoning", response_text)
confidence = extract("Confidence Score", response_text)

# ---------------- Display Predictions ----------------
st.markdown(f"### 🏷️ **Category:** {category}")
st.markdown(f"### 🔍 **Verdict:** {verdict}")
st.markdown(f"### 📌 **Confidence Score:** {confidence}")
st.markdown(f"### 💡 **Reasoning:** {reasoning}")

# ---------------- Text-to-Speech ----------------
safe_reasoning = reasoning[:500] if reasoning else "No reasoning provided."
try:
    tts = gTTS(text=safe_reasoning, lang="en")
    tts.save("reasoning.mp3")
    st.audio("reasoning.mp3", format="audio/mp3")
except Exception as e:
    st.warning(f"🔇 Audio generation failed: {e}")

# ---------------- Highlight Verdict ----------------
if "False" in verdict:
    st.error("🚨 **This post may contain misinformation!**")
elif "True" in verdict:
    st.success("✅ **This post appears to be credible.**")
else:
    st.warning("⚠️ **Verification uncertain. Please cross-check.**")
