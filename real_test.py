import streamlit as st
import pandas as pd
import time
from PIL import Image
import pytesseract
import requests
from gtts import gTTS
from io import BytesIO
from openai import OpenAI, APITimeoutError
from streamlit_autorefresh import st_autorefresh

# Initialize DeepSeek client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    timeout=60
)

file_path = "health2_post.xlsx"
data = pd.read_excel(file_path)
image_urls = data['displayUrl']
captions = data['caption']

st.title("📲 Real-Time Instagram Fake News Checker (Auto Mode)")

# Auto refresh every 10 seconds and return number of refreshes so far
count = st_autorefresh(interval=10 * 1000, limit=None, key="auto_refresh")

# Use modulo to cycle through posts
idx = count % len(image_urls)

current_url = image_urls[idx]
current_caption = captions[idx]

# Display image with caption
response = requests.get(current_url)
if response.status_code != 200:
    st.error("❌ Failed to load image.")
    st.stop()
image = Image.open(BytesIO(response.content))
st.image(image, caption=current_caption, use_container_width=True)

# OCR + caption
extracted_text = pytesseract.image_to_string(image, lang="eng+tam+tel")
combined_text = f"{extracted_text.strip()} {current_caption.strip()}".strip()
if len(combined_text) > 3000:
    combined_text = combined_text[:3000]

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
- Suggested Corrections (if applicable)

Input: {combined_text}
"""
}]

try:
    completion = client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=messages
    )
    response_text = completion.choices[0].message.content
except APITimeoutError:
    st.error("⏱️ API request timed out.")
    st.stop()
except Exception as e:
    st.error(f"⚠️ API call failed: {e}")
    st.stop()

def extract(key, text, fallback="N/A"):
    try:
        return text.split(f"{key}:")[1].split("\n")[0].strip().replace("*", "")
    except:
        return fallback

category = extract("Category", response_text)
verdict = extract("Verdict", response_text)
reasoning = extract("Reasoning", response_text)
confidence = extract("Confidence Score", response_text)

st.markdown(f"### 🏷️ **Category:** {category}")
st.markdown(f"### 🔍 **Verdict:** {verdict}")
st.markdown(f"### 📌 **Confidence Score:** {confidence}")
st.markdown(f"### 💡 **Reasoning:** {reasoning}")

tts = gTTS(text=reasoning or "No reasoning provided.", lang="en")
tts.save("reasoning.mp3")
st.audio("reasoning.mp3", format="audio/mp3")

if "False" in verdict:
    st.error("🚨 **This post may contain misinformation!**")
elif "True" in verdict:
    st.success("✅ **This post appears to be credible.**")
else:
    st.warning("⚠️ **Verification uncertain. Please cross-check.**")
