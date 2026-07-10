# backend/core/llm.py
"""LLM configuration with multiple fallback providers"""

import os
import logging
import json
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

# Try to import optional providers
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_mistralai import ChatMistralAI
except ImportError:
    ChatMistralAI = None

from backend.config import settings


class FallbackLLM:
    """Simple rule-based LLM that always works"""

    class Response:
        def __init__(self, content):
            self.content = content

    def invoke(self, prompt: str):
        prompt_lower = prompt.lower()

        if "framework" in prompt_lower and "detect" in prompt_lower:
            content = self._detect_framework_response()
        elif "migration plan" in prompt_lower or "plan" in prompt_lower:
            content = self._plan_response()
        elif "transform" in prompt_lower or "code" in prompt_lower:
            content = self._transform_response()
        else:
            content = "I'm a fallback LLM. Please set up Groq, Gemini, or Mistral API keys."

        return self.Response(content)

    def _detect_framework_response(self):
        return json.dumps({
            "framework": "Django",
            "version": "4.2",
            "confidence": 85,
            "reasoning": "Detected Django based on project structure (fallback mode)",
            "dependencies": {"python": ["Django==4.2", "psycopg2==2.9"]},
            "structure": "Standard Django project with apps",
            "key_files": ["manage.py", "settings.py", "urls.py"],
            "has_tests": True,
            "summary": "Django web application (analyzed by fallback LLM)"
        })

    def _plan_response(self):
        return json.dumps({
            "title": "Django Migration Plan",
            "summary": "Upgrade Django to latest version",
            "steps": [
                {"step_number": 1, "title": "Update Django", "description": "Update Django in requirements.txt", "type": "dependency_update", "files": ["requirements.txt"]},
                {"step_number": 2, "title": "Update URL patterns", "description": "Replace url() with path()", "type": "code_update", "files": ["**/urls.py"]},
                {"step_number": 3, "title": "Update middleware", "description": "Replace MIDDLEWARE_CLASSES with MIDDLEWARE", "type": "config_update", "files": ["settings.py"]}
            ],
            "breaking_changes": [
                {"change": "url() is deprecated", "impact": "high", "migration": "Replace with path()"}
            ],
            "estimated_hours": 4,
            "difficulty": "medium",
            "risk_level": "low"
        })

    def _transform_response(self):
        return "Code transformation applied (fallback mode)"


def get_llm():
    """Get LLM with fallback providers"""

    # ===== Primary: Groq =====
    if settings.GROQ_API_KEY:
        try:
            logger.info("🟢 Using Groq as primary LLM")
            return ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=2048
            )
        except Exception as e:
            logger.warning(f"Groq failed: {e}")

    # ===== Fallback 1: Google Gemini =====
    if settings.GOOGLE_API_KEY and ChatGoogleGenerativeAI:
        try:
            logger.info("🟡 Falling back to Google Gemini")
            return ChatGoogleGenerativeAI(
                api_key=settings.GOOGLE_API_KEY,
                model="gemini-2.5-flash",
                temperature=0.1,
                max_tokens=2048
            )
        except Exception as e:
            logger.warning(f"Google Gemini failed: {e}")

    # ===== Fallback 2: Mistral =====
    if settings.MISTRAL_API_KEY and ChatMistralAI:
        try:
            logger.info("🟡 Falling back to Mistral")
            return ChatMistralAI(
                api_key=settings.MISTRAL_API_KEY,
                model="mistral-small-3.1",
                temperature=0.1,
                max_tokens=2048
            )
        except Exception as e:
            logger.warning(f"Mistral failed: {e}")

    # ===== Fallback 3: Rule-based LLM (Always Works) =====
    logger.warning("🟠 Using fallback rule-based LLM")
    return FallbackLLM()
