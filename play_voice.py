#!/usr/bin/env python3
"""Plays ZentroMart AI Voice replies directly through computer speakers."""
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.step4_voice_agent import VoiceNormalizer

def play_text(text: str):
    print(f"\n[AI Agent Speaking]: {text}")
    norm_text = VoiceNormalizer.normalize_for_speech(text)
    
    # Generate spoken wav
    out_wav = _ROOT / "sample_outputs" / "live_speech.wav"
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 155)
        # Select voice
        voices = engine.getProperty('voices')
        for v in voices:
            if 'india' in v.name.lower() or 'zira' in v.name.lower() or 'female' in v.name.lower():
                engine.setProperty('voice', v.id)
                break
        engine.save_to_file(norm_text, str(out_wav))
        engine.runAndWait()
    except Exception as e:
        print(f"TTS warning: {e}")

    if out_wav.exists():
        try:
            import winsound
            print("Playing audio through speakers now...")
            winsound.PlaySound(str(out_wav), winsound.SND_FILENAME)
            print("Finished playback.")
        except Exception as e:
            print(f"Playback error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    else:
        msg = "Hello! I am ZentroMart's AI customer support assistant. How can I assist you with your order today?"
    play_text(msg)
