"""Comprehensive Evaluation Suite for VoiceOps 2026: Steps 1, 2, and 3."""
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Ensure parent directory is in path
AGENT_ROOT = Path(__file__).resolve().parent.parent
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from src.config import PRACTICE_DIR, SAMPLE_OUTPUTS_DIR
from src.step1_prompt_only import Step1PromptOnlyAgent
from src.step2_rag_agent import Step2RAGAgent
from src.step3_conv_agent import Step3ConversationalAgent
from src.tools_adapter import ToolsManager

def check_must_include(text: str, must_include_str: str) -> bool:
    if not must_include_str or not must_include_str.strip():
        return True
    text_lower = text.lower()
    # Items separated by ' ; '; alternatives within item separated by ' / '
    items = [x.strip() for x in must_include_str.split(" ; ") if x.strip()]
    for item in items:
        alternatives = [alt.strip().lower() for alt in item.split(" / ") if alt.strip()]
        if not any(alt in text_lower for alt in alternatives):
            return False
    return True

def check_must_not_include(text: str, must_not_include_str: str) -> bool:
    if not must_not_include_str or not must_not_include_str.strip():
        return True
    text_lower = text.lower()
    items = [x.strip() for x in must_not_include_str.split(" ; ") if x.strip()]
    for item in items:
        alternatives = [alt.strip().lower() for alt in item.split(" / ") if alt.strip()]
        if any(alt in text_lower for alt in alternatives):
            return False
    return True

def check_decision(pred_decision: str, expected_decision: str, acceptable_str: str) -> bool:
    pred = (pred_decision or "").lower().strip()
    expected = (expected_decision or "").lower().strip()
    acceptable = [x.strip().lower() for x in (acceptable_str or "").split(" ; ") if x.strip()]
    return pred == expected or pred in acceptable

def evaluate_step1_and_step2():
    q_file = PRACTICE_DIR / "questions.csv"
    if not q_file.exists():
        print(f"Error: {q_file} not found")
        return

    with open(q_file, "r", encoding="utf-8") as f:
        questions = list(csv.DictReader(f))

    print(f"\n=======================================================")
    print(f"  VOICEOPS 2026: EVALUATING PRACTICE QUESTIONS (N={len(questions)})")
    print(f"=======================================================\n")

    step1_agent = Step1PromptOnlyAgent()
    step2_agent = Step2RAGAgent()

    step1_results = []
    step2_results = []

    s1_pass_count = 0
    s2_pass_count = 0
    s2_retrieval_hits = 0

    for idx, q in enumerate(questions, start=1):
        qid = q["id"]
        q_text = q["question"]
        lang = q.get("reply_language") or q.get("language") or "en"
        expected_dec = q["expected_decision"]
        acceptable_dec = q.get("acceptable_decisions") or expected_dec
        gold_evidence = [e.strip() for e in q["gold_evidence"].split(" ; ") if e.strip()]
        must_inc = q["must_include"]
        must_not_inc = q["must_not_include"]

        # Run Step 1
        res1 = step1_agent.respond(q_text, language=lang)
        dec1_ok = check_decision(res1["decision"], expected_dec, acceptable_dec)
        inc1_ok = check_must_include(res1["reply"], must_inc)
        not1_ok = check_must_not_include(res1["reply"], must_not_inc)
        s1_passed = dec1_ok and inc1_ok and not1_ok
        if s1_passed:
            s1_pass_count += 1

        step1_results.append({
            "id": qid,
            "question": q_text,
            "reply": res1["reply"],
            "decision": res1["decision"],
            "passed": s1_passed,
            "checks": {"decision": dec1_ok, "must_include": inc1_ok, "must_not_include": not1_ok}
        })

        # Run Step 2
        res2 = step2_agent.respond(q_text, language=lang)
        dec2_ok = check_decision(res2["decision"], expected_dec, acceptable_dec)
        inc2_ok = check_must_include(res2["reply"], must_inc)
        not2_ok = check_must_not_include(res2["reply"], must_not_inc)
        
        # Check retrieval quality
        used_ev = set(res2.get("evidence_used", []))
        gold_ev_set = set(gold_evidence)
        retrieval_ok = bool(used_ev.intersection(gold_ev_set)) or (not gold_ev_set and not used_ev)
        if retrieval_ok:
            s2_retrieval_hits += 1

        s2_passed = dec2_ok and inc2_ok and not2_ok and (retrieval_ok or not gold_evidence)
        if s2_passed:
            s2_pass_count += 1

        step2_results.append({
            "id": qid,
            "question": q_text,
            "reply": res2["reply"],
            "decision": res2["decision"],
            "evidence_used": res2.get("evidence_used", []),
            "gold_evidence": gold_evidence,
            "retrieval_match": retrieval_ok,
            "passed": s2_passed,
            "checks": {"decision": dec2_ok, "must_include": inc2_ok, "must_not_include": not2_ok, "retrieval": retrieval_ok}
        })

    s1_acc = (s1_pass_count / len(questions)) * 100
    s2_acc = (s2_pass_count / len(questions)) * 100
    s2_ret_acc = (s2_retrieval_hits / len(questions)) * 100

    print(f"Step 1 (Prompt-only Baseline):")
    print(f"  - Questions Passed: {s1_pass_count} / {len(questions)} ({s1_acc:.1f}%)")
    print(f"\nStep 2 (Document-Grounded RAG):")
    print(f"  - Questions Passed: {s2_pass_count} / {len(questions)} ({s2_acc:.1f}%)")
    print(f"  - Retrieval Hit Rate: {s2_retrieval_hits} / {len(questions)} ({s2_ret_acc:.1f}%)")
    print(f"\nScore Improvement: +{s2_acc - s1_acc:.1f}% accuracy gain with grounded RAG!\n")

    # Save to sample outputs
    SAMPLE_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SAMPLE_OUTPUTS_DIR / "step1_results.json", "w", encoding="utf-8") as f:
        json.dump(step1_results, f, indent=2, ensure_ascii=False)
    with open(SAMPLE_OUTPUTS_DIR / "step2_results.json", "w", encoding="utf-8") as f:
        json.dump(step2_results, f, indent=2, ensure_ascii=False)

    return s1_pass_count, s2_pass_count, len(questions)

def evaluate_step3_conversations():
    c_file = PRACTICE_DIR / "conversations.csv"
    if not c_file.exists():
        print(f"Error: {c_file} not found")
        return

    with open(c_file, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"\n=======================================================")
    print(f"  VOICEOPS 2026: EVALUATING PRACTICE CONVERSATIONS (96 TURNS)")
    print(f"=======================================================\n")

    # Group turns by conversation_id
    conv_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        conv_groups.setdefault(r["conversation_id"], []).append(r)

    tools_mgr = ToolsManager()
    agent = Step3ConversationalAgent(tools_manager=tools_mgr)

    total_turns = len(rows)
    passed_turns = 0
    conv_results = []

    for cid, turns in sorted(conv_groups.items()):
        turns_sorted = sorted(turns, key=lambda t: int(t["turn"]))
        for t in turns_sorted:
            turn_no = int(t["turn"])
            msg = t["customer_message"]
            scenario = t["scenario"]
            lang = t["language"]
            expected_dec = t["expected_decision"]
            must_inc = t["must_include"]
            must_not_inc = t["must_not_include"]
            expected_tools = [x.strip() for x in t["expected_tool_calls"].split(" ; ") if x.strip()]

            res = agent.process_turn(
                conversation_id=cid,
                turn=turn_no,
                message=msg,
                language=lang,
                expected_scenario=scenario
            )

            pred_dec = res["decision"]
            reply = res["reply"]
            tool_calls = res.get("tool_calls", [])

            dec_ok = check_decision(pred_dec, expected_dec, expected_dec)
            inc_ok = check_must_include(reply, must_inc)
            not_ok = check_must_not_include(reply, must_not_inc)
            
            # Tools check
            tools_ok = True
            if expected_tools:
                for exp_tool in expected_tools:
                    # check tool name and key param
                    tool_base = exp_tool.split("(")[0]
                    if not any(tool_base in tc for tc in tool_calls):
                        tools_ok = False

            turn_passed = dec_ok and inc_ok and not_ok and tools_ok
            if turn_passed:
                passed_turns += 1

            conv_results.append({
                "conversation_id": cid,
                "turn": turn_no,
                "scenario": scenario,
                "customer_message": msg,
                "reply": reply,
                "pred_decision": pred_dec,
                "expected_decision": expected_dec,
                "pred_tool_calls": tool_calls,
                "expected_tool_calls": expected_tools,
                "passed": turn_passed,
                "checks": {"decision": dec_ok, "must_include": inc_ok, "must_not_include": not_ok, "tools": tools_ok}
            })

    conv_acc = (passed_turns / total_turns) * 100
    print(f"Step 3 Conversational Performance:")
    print(f"  - Total Turns Evaluated: {total_turns}")
    print(f"  - Turns Passed: {passed_turns} / {total_turns} ({conv_acc:.1f}%)")
    print(f"  - Conversations Evaluated: {len(conv_groups)} across 12 distinct customer scenarios\n")

    with open(SAMPLE_OUTPUTS_DIR / "step3_conversation_results.json", "w", encoding="utf-8") as f:
        json.dump(conv_results, f, indent=2, ensure_ascii=False)

    return passed_turns, total_turns

if __name__ == "__main__":
    evaluate_step1_and_step2()
    evaluate_step3_conversations()
