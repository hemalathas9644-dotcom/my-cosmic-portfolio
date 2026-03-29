import streamlit as st
import pandas as pd
import time
from PIL import Image
import pytesseract
import requests
import json
from gtts import gTTS
from io import BytesIO
from openai import OpenAI, APITimeoutError

# ✅ Initialize DeepSeek client with correct base_url and timeout
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",  # ✅ Fixed base_url
    api_key="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",
    timeout=60  # ✅ Set timeout in seconds
)

# Load Excel file
file_path = "health2_post.xlsx"
data = pd.read_excel(file_path)
image_urls = data['displayUrl']
captions = data['caption']

# UI title
st.title("📲 Real-Time Instagram Fake News Checker")

# Session index setup
if 'index' not in st.session_state:
    st.session_state.index = 0

idx = st.session_state.index
current_url = image_urls[idx]
current_caption = captions[idx]

# Load image from URL
response = requests.get(current_url)
if response.status_code != 200:
    st.error("❌ Failed to load image.")
    st.stop()

image = Image.open(BytesIO(response.content))
st.image(image, caption=current_caption, use_column_width=True)

# OCR processing
languages = 'eng+tam+tel'
extracted_text = pytesseract.image_to_string(image, lang=languages)
combined_text = f"{extracted_text.strip()} {current_caption.strip()}".strip()

# Optional: truncate text if too long
if len(combined_text) > 3000:
    combined_text = combined_text[:3000]

# DeepSeek prompt
messages = [
    {
        "role": "user",
        "content": f"""
Instruction:
You are an AI model that categorizes and verifies health and finance-related information.

Categorize into:
- Health
- Finance
- Other (skip analysis)

If Health or Finance:
- Verdict: ✅ True | ❌ False | ⚠️ Uncertain
- Reasoning
- Confidence Score (0–100%)
- Suggested Corrections (if applicable)

Input: {combined_text}
"""
    }
]

# ✅ API call with timeout handling
try:
    completion = client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=messages
    )
    response_text = completion.choices[0].message.content

except APITimeoutError:
    st.error("⏱️ API request timed out. Please try again.")
    st.stop()

except Exception as e:
    st.error(f"⚠️ API call failed: {e}")
    st.stop()

# Response parsing
def extract(key, text, fallback="N/A"):
    try:
        return text.split(f"{key}:")[1].split("\n")[0].strip().replace("*", "")
    except:
        return fallback

category = extract("Category", response_text)
verdict = extract("Verdict", response_text, "⚠️ Uncertain")
reasoning = extract("Reasoning", response_text, "No reasoning provided.")
confidence = extract("Confidence Score", response_text)

# Display Results
st.markdown(f"### 🏷️ **Category:** {category}")
st.markdown(f"### 🔍 **Verdict:** {verdict}")
st.markdown(f"### 📌 **Confidence Score:** {confidence}")
st.markdown(f"### 💡 **Reasoning:** {reasoning}")

# Audio Output
if not reasoning:
    reasoning = "No reason"
tts = gTTS(text=reasoning, lang="en")
tts.save("reasoning.mp3")
st.audio("reasoning.mp3", format="audio/mp3")

# Verdict Highlight
if "False" in verdict:
    st.error("🚨 **This post may contain misinformation!**")
elif "True" in verdict:
    st.success("✅ **This post appears to be credible.**")
else:
    st.warning("⚠️ **Verification uncertain. Please cross-check.**")

# Next post button
if st.button("➡️ Next Post"):
    st.session_state.index = (st.session_state.index + 1) % len(image_urls)
    st.rerun()
