from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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"            # Replace with your actual API key
)

completion = client.chat.completions.create(
  extra_body={},
  model="deepseek/deepseek-r1:free",
  messages=[
    {
      "role": "user",
      "content": """
Instruction:
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

Extracted Information: apple is not good for health.

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
    }
  ]
)
print(completion.choices[0].message.content)