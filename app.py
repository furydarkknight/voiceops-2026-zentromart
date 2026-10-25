"""Interactive Web Application for ZentroMart VoiceOps 2026."""
import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.step3_conv_agent import Step3ConversationalAgent
from src.step2_rag_agent import Step2RAGAgent
from src.step4_voice_agent import VoiceNormalizer, Step4VoiceAgent
from src.tools_adapter import ToolsManager

app = Flask(__name__, template_folder=str(_ROOT / "templates"), static_folder=str(_ROOT / "static"))
CORS(app)

tools_mgr = ToolsManager()
conv_agent = Step3ConversationalAgent(tools_manager=tools_mgr)
rag_agent = Step2RAGAgent(retriever=conv_agent.retriever)
voice_agent = Step4VoiceAgent(conv_agent=conv_agent)

# Track turns per conversation in session
conversation_turns = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "status": "online",
        "reference_date": "2026-10-20",
        "gnani_stt_model": "en-IN",
        "gnani_tts_model": "timbre-v2.5",
        "gnani_tts_voice": "Kaveri",
        "has_live_gnani": voice_agent.has_live_gnani
    })

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    conv_id = data.get("conversation_id") or "web_session_01"
    language = data.get("language") or "en"

    if not message:
        return jsonify({"error": "No message provided"}), 400

    current_turn = conversation_turns.get(conv_id, 0) + 1
    conversation_turns[conv_id] = current_turn

    session = tools_mgr.get_session(conv_id)

    # Determine if message is an opening greeting or standalone question
    is_greeting = any(
        message.strip().lower() == g
        for g in [
            "hello", "hi", "hey",
            "hi, i need some help with an order.",
            "hello, mujhe order ke baare mein help chahiye.",
            "नमस्ते, मुझे अपने ऑर्डर के बारे में मदद चाहिए।",
            "help with my order"
        ]
    )

    if current_turn == 1 and is_greeting:
        agent_out = conv_agent.process_turn(conv_id, turn=1, message=message, language=language)
    elif session.order_id or any(d in message for d in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]):
        # Has active order context or digits provided
        agent_out = conv_agent.process_turn(conv_id, turn=current_turn, message=message, language=language)
    else:
        # Run grounded RAG query
        agent_out = rag_agent.respond(message, language=language)

    reply_text = agent_out.get("reply", "")
    evidence = agent_out.get("evidence_used") or agent_out.get("gold_evidence", [])
    decision = agent_out.get("decision", "answer")
    tool_calls = agent_out.get("tool_calls", [])

    speech_text = VoiceNormalizer.normalize_for_speech(reply_text)

    # Try playing sound via Windows winsound if on local server
    try:
        import winsound
        # gentle system beep confirmation
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass

    session_info = {
        "order_id": session.order_id,
        "verified": session.verified,
        "details": {
            "customer_first_name": session.order_details.get("customer_first_name") if session.order_details else None,
            "is_plus": session.order_details.get("is_plus") if session.order_details else None,
            "status": session.order_details.get("status") if session.order_details else None
        } if session.order_details else None
    }

    return jsonify({
        "reply": reply_text,
        "speech_text": speech_text,
        "evidence_used": evidence,
        "decision": decision,
        "tool_calls": tool_calls,
        "turn": current_turn,
        "session": session_info
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=======================================================")
    print(f"  ZentroMart VoiceOps 2026 Web Server Running!")
    print(f"  URL: http://0.0.0.0:{port}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
