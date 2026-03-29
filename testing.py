import streamlit as st
import pandas as pd
import time
from PIL import Image

# Load the Excel file
file_path = "health_new_post.xlsx"
data = pd.read_excel(file_path)
image_paths = data['displayUrl']  # Column with image paths
captions = data['caption']  # Column with captions

# Title of the App
st.title("Fake News Prediction App")

# Simulate real-time updates
if 'index' not in st.session_state:
    st.session_state.index = 0  # Start with the first row

# Display current image and caption
current_image_path = image_paths[st.session_state.index]
current_caption = captions[st.session_state.index]
import requests
from io import BytesIO

response = requests.get(current_image_path)
if response.status_code == 200:
    img = Image.open(BytesIO(response.content))
    st.image(img, caption="Caption from your Excel sheet", use_column_width=True)
else:
    st.error("Failed to load image from URL.")

# Example prediction output (replace with your model)
st.write(f"Prediction: Fake / Not Fake for '{current_caption}'")

# Wait for 30 seconds and update the content

time.sleep(15)
st.session_state.index += 1
if st.session_state.index >= len(image_paths):
    st.session_state.index = 0  # Restart when reaching the end
st.rerun()
