import os
from groq import Groq

# --- Paste your Groq API Key here if not setting the GROQ_API_KEY environment variable ---
GROQ_API_KEY = "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"
# -----------------------------------------------------------------------------------------

def ask_groq(prompt):
    # Determine the API Key to use
    api_key = os.environ.get("GROQ_API_KEY", GROQ_API_KEY)
    
    if api_key == "YOUR_GROQ_API_KEY" or not api_key:
        return "Error: Please set your GROQ_API_KEY in Model/groq.py or as an environment variable."
        
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2, # Lower temperature is much better for scoring and strict JSON output
            max_completion_tokens=2048,
            top_p=1,
            stream=False,
            stop=None
        )
        
        return completion.choices[0].message.content or ""
        
    except Exception as e:
        return f"Error calling Groq: {e}"
