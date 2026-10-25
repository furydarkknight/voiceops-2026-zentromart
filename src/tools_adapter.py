"""Safe tools adapter for ZentroMart identity-checked lookups and ticketing."""
import sys
import os
from typing import Dict, Any, Optional
from src.config import TOOLS_DIR

# Add TOOLS_DIR to sys.path so we can import tools.py directly
if str(TOOLS_DIR) not in sys.path and TOOLS_DIR.exists():
    sys.path.insert(0, str(TOOLS_DIR))

try:
    from tools import lookup_order as _raw_lookup_order, create_ticket as _raw_create_ticket
except ImportError:
    # Standalone mock implementation if tools.py not present in path
    def _raw_lookup_order(order_id: str, verification_value: str = None) -> dict:
        return {"verification_required": True, "message": "tools.py not found in path"}

    def _raw_create_ticket(summary: str, order_id: str = None, reason: str = None, intent: str = None) -> dict:
        if len(summary or "") < 20:
            return {"created": False, "error": "summary too short"}
        return {"created": True, "ticket_id": "TKT_MOCK_001"}

class CallerSession:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.order_id: Optional[str] = None
        self.verified: bool = False
        self.verification_attempts: int = 0
        self.max_retries: int = 1
        self.order_details: Optional[Dict[str, Any]] = None
        self.ticket_created: bool = False
        self.ticket_id: Optional[str] = None

class ToolsManager:
    def __init__(self):
        self.sessions: Dict[str, CallerSession] = {}

    def get_session(self, conversation_id: str) -> CallerSession:
        if conversation_id not in self.sessions:
            self.sessions[conversation_id] = CallerSession(conversation_id)
        return self.sessions[conversation_id]

    def lookup(self, order_id: str, verification_value: Optional[str] = None, session: Optional[CallerSession] = None) -> Dict[str, Any]:
        """Wrapper around lookup_order enforcing verification state and privacy."""
        cleaned_id = "".join(ch for ch in str(order_id) if ch.isdigit())
        if session:
            session.order_id = cleaned_id

        if not verification_value:
            res = _raw_lookup_order(cleaned_id)
            return {
                "action": "ask_verification",
                "verification_required": True,
                "message": "Please provide the last 4 digits of your registered phone number or your delivery pincode.",
                "raw": res,
            }

        if session:
            session.verification_attempts += 1

        res = _raw_lookup_order(cleaned_id, verification_value=verification_value)
        if res.get("verified") and res.get("found"):
            if session:
                session.verified = True
                session.order_details = res
            return {
                "action": "verified_success",
                "verified": True,
                "details": res,
            }
        else:
            can_retry = session.verification_attempts <= session.max_retries if session else True
            return {
                "action": "verification_failed",
                "verified": False,
                "can_retry": can_retry,
                "message": "Verification failed." if not can_retry else "The digits provided did not match our records. You can try once more with the delivery pincode or phone last 4 digits.",
                "raw": res,
            }

    def escalate(self, summary: str, order_id: Optional[str] = None, reason: Optional[str] = None, intent: Optional[str] = None, session: Optional[CallerSession] = None) -> Dict[str, Any]:
        """Creates an escalation ticket and updates session."""
        # Ensure summary is descriptive and >= 20 characters
        if not summary or len(summary.strip()) < 20:
            summary = f"Customer support escalation: {reason or 'General'} for order {order_id or 'N/A'}. Details: {summary}"

        res = _raw_create_ticket(summary=summary, order_id=order_id, reason=reason, intent=intent)
        if res.get("created"):
            if session:
                session.ticket_created = True
                session.ticket_id = res.get("ticket_id")
            return {
                "success": True,
                "ticket_id": res.get("ticket_id"),
                "message": "A priority ticket has been created and assigned to a human specialist.",
            }
        return {
            "success": False,
            "error": res.get("error", "Failed to create ticket"),
        }
