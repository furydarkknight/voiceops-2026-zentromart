#!/usr/bin/env python3
"""VoiceOps 2026 Batch Runner.

Takes a folder of customer audio files, runs the conversational voice agent,
and saves the audio and text replies alongside the document chunks used.

Usage:
    python run.py --input-dir <path_to_audio_folder> --output-dir <path_to_output_folder>
    or:
    python run.py <path_to_audio_folder> [<path_to_output_folder>]
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Add project root to path
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.step4_voice_agent import Step4VoiceAgent

def main():
    parser = argparse.ArgumentParser(description="VoiceOps 2026 Batch Audio Processor")
    parser.add_argument("pos_input", nargs="?", default=None, help="Input directory containing customer audio files")
    parser.add_argument("pos_output", nargs="?", default=None, help="Output directory to save replies and metadata")
    parser.add_argument("--input-dir", "-i", dest="opt_input", default=None, help="Input directory containing customer audio files")
    parser.add_argument("--output-dir", "-o", dest="opt_output", default=None, help="Output directory to save replies and metadata")
    parser.add_argument("--voice", default="Kaveri", help="Gnani TTS voice name (default: Kaveri)")
    parser.add_argument("--model", default="timbre-v2.5", help="Gnani TTS model name (default: timbre-v2.5)")
    parser.add_argument("--lang", default="en-IN", help="Language code (default: en-IN)")
    parser.add_argument("--play", action="store_true", help="Play synthesized replies out loud through speakers")

    args = parser.parse_args()

    input_path = args.opt_input or args.pos_input or str(_ROOT / "sample_inputs")
    output_path = args.opt_output or args.pos_output or str(_ROOT / "sample_outputs" / "batch_run")

    input_dir = Path(input_path).resolve()
    output_dir = Path(output_path).resolve()

    print(f"=== VoiceOps 2026 Batch Audio Processor ===")
    print(f"Input Directory : {input_dir}")
    print(f"Output Directory: {output_dir}")
    print(f"TTS Settings    : Model={args.model}, Voice={args.voice}, Language={args.lang}")
    if args.play:
        print(f"Audio Playback  : Enabled (Playing through speakers)\n")
    else:
        print(f"Audio Playback  : Files saved to disk (use --play to hear aloud)\n")

    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist.")
        sys.exit(1)

    agent = Step4VoiceAgent(voice=args.voice, model=args.model, language=args.lang)
    results = agent.run_batch(input_dir=input_dir, output_dir=output_dir)

    print(f"\nProcessing Complete! Processed {len(results)} audio file(s).")
    print(f"Results and synthesized audio replies saved to: {output_dir}")
    for r in results:
        print(f" - [{Path(r['input_audio']).name}] -> Heard: \"{r['heard']}\"")
        print(f"   Reply: \"{r['reply_text']}\"")
        print(f"   Chunks: {r['evidence_used']}\n")

        if args.play:
            audio_out = r.get("output_audio")
            if audio_out and os.path.exists(audio_out):
                try:
                    import winsound
                    print(f"   Playing audio: {Path(audio_out).name}...")
                    winsound.PlaySound(audio_out, winsound.SND_FILENAME)
                except Exception as e:
                    print(f"   (Audio playback notice: {e})")

if __name__ == "__main__":
    main()
