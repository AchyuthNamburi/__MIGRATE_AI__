# backend/core/llm.py
from langchain_groq import ChatGroq
from backend.config import settings

def get_llm():
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="llama-3.1-8b-instant",  # ✅ Fastest, cheapest, good enough
        temperature=0.1,
        max_tokens=2048
    )
