import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import pytesseract
from openai import OpenAI  # Ensure the openai package is installed and configured

# -------------------------------
# 1. Setup DeepSeek API client
# -------------------------------
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",  # Use your DeepSeek/DeepRouter API endpoint
    api_key="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"            # Replace with your actual API key
)

# -------------------------------
# 2. Read the Excel dataset
# -------------------------------
excel_file = "health_related_post.xlsx"
df = pd.read_excel(excel_file)

# -------------------------------
# 3. Define helper function to extract text from image using pytesseract
# -------------------------------
def extract_text_from_image(url):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            text = pytesseract.image_to_string(image)
            return text.strip()
        else:
            print(f"Failed to fetch image from {url} - status code: {response.status_code}")
            return ""
    except Exception as e:
        print(f"Error processing image from {url}: {e}")
        return ""

# -------------------------------
# 4. Define function to process each row with DeepSeek prompt
# -------------------------------
def process_row(caption, image_text):
    # Combine the caption and the text extracted from the image.
    combined_input = f"Caption: {caption}\nImage Text: {image_text}"
    
    # Build the prompt based on your provided example.
    prompt = f"""
Instruction:
You are an AI model that categorizes and verifies health and finance-related information. Follow these steps:

Categorize the Data into:

Health: Related to medicine, diseases, treatments, nutrition, or public health.
Finance: Related to stock markets, investments, economic policies, banking, or personal finance.
Other: Any topic outside health or finance (skip analysis).
If Health or Finance, Verify Truthfulness Using:

Trusted Sources (if provided): WHO, FDA, SEC, IMF, etc.
General Knowledge: If no source is provided, verify using logical reasoning, common facts, and expert knowledge.
Input:

Extracted Information: {combined_input}
Context (if available): (If missing, analyze without it)
Output:

Category: Health | Finance | Other
If Other: "This information is outside the scope of health and finance. Skipping analysis."
If Health or Finance:
Verdict: ✅ True | ❌ False | ⚠️ Uncertain
Reasoning: Explanation based on available sources OR logical analysis
Confidence Score: (0-100%)
Suggested Corrections (if applicable)
    """
    
    try:
        response = client.chat.completions.create(
            extra_body={},
            model="deepseek/deepseek-r1:free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Error calling DeepSeek API:", e)
        return "DeepSeek API call failed"

# -------------------------------
# 5. Process each row and collect results
# -------------------------------
results = []

for idx, row in df.iterrows():
    caption = row['caption']          # Adjust if your actual column name is different.
    image_url = row['displayUrl']       # Adjust if your actual column name is different.
    
    print(f"Processing row {idx+1}...")
    # Extract text from the image using pytesseract
    image_text = extract_text_from_image(image_url)
    
    # Process the combined text with DeepSeek API
    deepseek_result = process_row(caption, image_text)
    print("caption :", caption)
    print("extracted_image_text :", image_text)
    print("deepseek_result :", deepseek_result)
    results.append({
        "caption": caption,
        "extracted_image_text": image_text,
        "deepseek_result": deepseek_result
    })

# -------------------------------
# 6. Save the results to a new Excel file
# -------------------------------
output_file = "processed_results.xlsx"
results_df = pd.DataFrame(results)
results_df.to_excel(output_file, index=False)

print(f"Processing complete. Results saved to {output_file}")
