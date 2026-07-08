# test_groq.py
"""Simple Groq connection test - uses < 100 tokens"""

import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq
try:
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.1-8b-instant",  # Fast + low token usage
        temperature=0.1,
        max_tokens=50  # ← LIMIT TOKENS
    )

    # Simple prompt - uses < 100 tokens
    response = llm.invoke("Say 'Groq is working!' in exactly 5 words.")
    
    print("✅ Groq is working!")
    print(f"📝 Response: {response.content}")
    print(f"📊 Tokens used: ~{len(response.content.split()) * 1.3} (estimated)")

except Exception as e:
    print(f"❌ Groq error: {str(e)}")