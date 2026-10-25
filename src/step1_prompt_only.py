"""Step 1: Baseline Prompt-only LLM Agent (No Knowledge Base Access)."""
from typing import Dict, Any, Optional
from src.llm_engine import LLMEngine, SYSTEM_PROMPT_STEP1

class Step1PromptOnlyAgent:
    def __init__(self, llm_engine: Optional[LLMEngine] = None):
        self.llm = llm_engine or LLMEngine()

    def respond(self, question: str, language: str = "en") -> Dict[str, Any]:
        """Generates a reply without any RAG context, mimicking Week 1 & 2 baseline."""
        # Generic prompt without any knowledge base documents
        prompt = f"Customer Query: {question}\nLanguage: {language}\nPlease provide an answer as ZentroMart's support assistant."
        raw_reply = self.llm.generate(prompt, system_prompt=SYSTEM_PROMPT_STEP1)

        # Baseline heuristic reply if offline mode
        if not raw_reply:
            raw_reply = self._generic_ecommerce_guess(question, language)

        # Enforce requirement: First reply introduces assistant as AI assistant
        if not any(marker in raw_reply.lower() for marker in ["ai", "assistant", "एआई", "कृत्रिम"]):
            if language == "hi":
                raw_reply = f"नमस्ते, मैं ज़ेंट्रोमार्ट का एआई सपोर्ट असिस्टेंट हूँ। {raw_reply}"
            elif language == "hi-en":
                raw_reply = f"Hello! Main ZentroMart ka AI support assistant hoon. {raw_reply}"
            else:
                raw_reply = f"Hello! I am ZentroMart's AI support assistant. {raw_reply}"

        return {
            "reply": raw_reply,
            "decision": "answer",
            "evidence_used": [],
            "grounded": False,
        }

    def _generic_ecommerce_guess(self, question: str, language: str) -> str:
        q_lower = question.lower()
        if "refund" in q_lower or "रिफ़ंड" in q_lower:
            return "Refunds usually take 5 to 7 business days to reflect in your account."
        elif "return" in q_lower or "वापस" in q_lower or "lautaane" in q_lower:
            return "Generally, items can be returned within 30 days of delivery through our app."
        elif "warranty" in q_lower or "वारंटी" in q_lower:
            return "Most electronics come with a 1-year brand warranty."
        elif "cancel" in q_lower or "कैंसिल" in q_lower:
            return "You can cancel your order directly from the My Orders section in the app."
        elif "midnight" in q_lower or "student" in q_lower or "gst" in q_lower or "store" in q_lower or "दुकान" in q_lower:
            return "Yes, you can check our app or website for available delivery options and discounts."
        return "I can certainly assist you with your ZentroMart order. Please let me know what you need help with."
