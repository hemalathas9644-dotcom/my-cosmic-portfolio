import pandas as pd
import requests
import pytesseract
from PIL import Image
from io import BytesIO

# Load the Excel file
file_path = "dataset_instagram-hashtag-scraper_2025-03-11_07-28-24-861.xlsx"
df = pd.read_excel(file_path)

# Ensure 'displayUrl' column exists
if 'displayUrl' not in df.columns:
    raise ValueError("Column 'displayUrl' not found in the dataset")

# Function to extract text from an image URL
def extract_text_from_image(image_url):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            text = pytesseract.image_to_string(img)
            return text.strip()
        else:
            return "Failed to fetch image"
    except Exception as e:
        return f"Error: {str(e)}"

# Apply function to the first few rows for testing
df['ExtractedText'] = df['displayUrl'].apply(extract_text_from_image)

# Save the extracted text to a new file
output_file = "extracted_text.xlsx"
df.to_excel(output_file, index=False)
# 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
print(f"Extracted text saved to {output_file}")
