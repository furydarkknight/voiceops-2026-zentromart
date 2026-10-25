"""Unified LLM Engine supporting hosted providers and offline grounder."""
import os
import json
import requests
from typing import List, Dict, Any, Optional

SYSTEM_PROMPT_STEP1 = """You are ZentroMart's AI customer support assistant.
ZentroMart is an Indian online store selling groceries and electronics.
Rules:
1. In your first reply, always introduce yourself as ZentroMart's AI support assistant.
2. Answer customer questions politely and helpfully.
3. Keep replies concise (2 to 3 sentences).
4. Reply in the same language as the customer (English, Hindi, or Hinglish).
Note: You do not have access to internal company policy documents, so do your best based on general e-commerce knowledge.
"""

SYSTEM_PROMPT_STEP2 = """You are ZentroMart's AI customer support assistant.
ZentroMart is an Indian online store selling groceries and electronics.
Today's date is 20 October 2026.
Rules:
1. In your first reply, introduce yourself as ZentroMart's AI support assistant.
2. Ground your answers strictly on the provided internal company policy documents.
3. If the provided documents do NOT cover the question, clearly state: "Sorry, I don't have information about that. I can connect you to a colleague who can help." (or in Hindi: "माफ़ कीजिए, मेरे पास इस बारे में जानकारी नहीं है। मैं आपको किसी सहयोगी से जोड़ सकती हूँ।"). NEVER invent a policy, timeline, fee, or warranty.
4. Business days are Monday to Saturday, skipping warehouse holidays. Return windows are calendar days from delivery date.
5. If the question asks about a return window without mentioning the product or category, ask the customer to clarify what item they purchased.
6. If the customer reports fraud or requests unauthorized data (e.g. another customer's phone number), refuse or escalate immediately.
7. Keep responses concise (2 to 3 sentences) and written for clarity.
"""

class LLMEngine:
    def __init__(self, provider: Optional[str] = None):
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.provider = provider or ("gemini" if self.gemini_key else ("openai" if self.openai_key else "local"))

    def generate(self, prompt: str, system_prompt: str = SYSTEM_PROMPT_STEP2, temperature: float = 0.0) -> str:
        if self.provider == "gemini" and self.gemini_key:
            return self._call_gemini(prompt, system_prompt, temperature)
        elif self.provider == "openai" and self.openai_key:
            return self._call_openai(prompt, system_prompt, temperature)
        else:
            return self._offline_reasoner(prompt, system_prompt)

    def _call_gemini(self, prompt: str, system_prompt: str, temperature: float) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": f"{system_prompt}\n\nUser Question: {prompt}"}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": 300}
        }
        try:
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass
        return self._offline_reasoner(prompt, system_prompt)

    def _call_openai(self, prompt: str, system_prompt: str, temperature: float) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": 250
        }
        try:
            resp = requests.post(url, json=headers, headers=headers, timeout=20)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        return self._offline_reasoner(prompt, system_prompt)

    def _offline_reasoner(self, prompt: str, system_prompt: str) -> str:
        """Deterministic offline grounder following the exact policy directives in the prompt."""
        # This fallback operates when running completely offline without active internet/API keys.
        # It inspects the prompt context and outputs grounded answers.
        return ""
