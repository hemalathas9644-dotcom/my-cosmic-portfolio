import streamlit as st
import requests
import json
import pytesseract
from gtts import gTTS
from PIL import Image
from openai import OpenAI  # Import DeepSeek API client
from openai import APITimeoutError

# Set up DeepSeek API client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",  # Replace with actual API key
    timeout=60  # Set the timeout to 60 seconds
)

st.title("📱 Fake News Detector - Instagram Simulation")

# Upload an image (optional)
uploaded_image = st.file_uploader("📸 Upload a post image (optional)", type=["jpg", "png", "jpeg"])

# Extract text from the image (if uploaded)
extracted_text = ""
if uploaded_image:
    image = Image.open(uploaded_image)
    # Specify the languages (e.g., English and Tamil)
    languages = 'eng+tam+tel'
    extracted_text = pytesseract.image_to_string(image, lang=languages)  # Extract text using OCR
    st.text_area("📝 Extracted Text from Image:", extracted_text, height=100)

# Enter the post caption
user_input = st.text_area("📌 Enter post caption:", "Type or paste the post text here...")

# Combine extracted text & caption for analysis
combined_text = f"{extracted_text} {user_input}".strip()

# Optional: truncate text if too long
if len(combined_text) > 3000:
    combined_text = combined_text[:3000]

if st.button("Check News"):
    if combined_text:
        # Send request to DeepSeek API
        messages = [
            {
                "role": "user",
                "content": f"""
                Instruction:
You are an AI model that categorizes and verifies health and finance-related information. Follow these steps:

Categorize the Data into:
- Health: Related to medicine, diseases, treatments, nutrition, or public health.
- Finance: Related to stock markets, investments, economic policies, banking, or personal finance.
- Other: Any topic outside health or finance (skip analysis).

If Health or Finance, Verify Truthfulness Using:
- Trusted Sources (if provided): WHO, FDA, SEC, IMF, etc.
- General Knowledge: If no source is provided, verify using logical reasoning, common facts, and expert knowledge.

Language Handling:
- Identify the language of the extracted information.
- Provide the output in the **same language** as the input.

Input:
Extracted Information: {combined_text}

Output:
- **Category:** Health | Finance | Other  
- **If Other:** Respond in the same language:  
  - Example (Tamil): "இந்த தகவல் மருத்துவம் அல்லது நிதி தொடர்புடையது அல்ல. மதிப்பீட்டைத் தவிர்க்கிறது."  
  - Example (Hindi): "यह जानकारी स्वास्थ्य या वित्त से संबंधित नहीं है। विश्लेषण छोड़ रहा हूँ।"  
- **If Health or Finance:**  
  - **Verdict:** ✅ True | ❌ False | ⚠️ Uncertain  
  - **Reasoning:** Explanation based on available sources OR logical analysis in the same language.  
  - **Confidence Score:** (0-100%)  
  - **Suggested Corrections (if applicable)**  
                """
            }
        ]
        
        try:
            completion = client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=messages
            )
            response = completion.choices[0].message.content
        except APITimeoutError:
            st.error("⚠️ Request timed out. Please try again or check your internet/API key.")
            response = None
        
        if response:
            print("API Raw Response:", response)  # Debugging Step

            # Since response is a string, manually extract key parts
            category = "Unknown"
            verdict = "⚠️ Uncertain"
            reasoning = "No reasoning provided."
            confidence = "N/A"

            # Extract information from string response
            if "Category:" in response:
                try:
                    category = response.split("Category:")[1].split("\n")[0].strip().replace("*", "")
                except:
                    pass

            if "Verdict:" in response:
                try:
                    verdict = response.split("Verdict:")[1].split("\n")[0].replace("*", "").strip()
                except:
                    pass

            if "Reasoning:" in response:
                try:
                    reasoning = response.split("Reasoning:")[1].split("**Confidence Score:")[0].strip().replace("*", "")
                except:
                    pass

            if "Confidence Score:" in response:
                try:
                    confidence = response.split("Confidence Score:")[1].split("\n")[0].strip().replace("*", "")
                except:
                    pass

            # Display results
            st.markdown(f"### 🏷️ **Category:** {category}")
            st.markdown(f"### 🔍 **Verdict:** {verdict}")
            st.markdown(f"### 📌 **Confidence Score:** {confidence}")
            st.markdown(f"### 💡 **Reasoning:** {reasoning}")

            # Convert reasoning to speech using gTTS
            tts = gTTS(text=reasoning, lang="en")
            tts.save("reasoning.mp3")

            # Show Fake News Warning
            if "False" in verdict:
                st.error("🚨 **Warning: This post may contain misinformation!**")
            elif "True" in verdict:
                st.success("✅ **This post appears to be credible.**")
            else:
                st.warning("⚠️ **Verification uncertain. Cross-check with trusted sources.**")

            # Play audio button
            st.audio("reasoning.mp3", format="audio/mp3")
    else:
        st.warning("⚠️ Please enter text or upload an image.")
