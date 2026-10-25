"""Configuration and path resolution for VoiceOps 2026 ZentroMart Agent."""
import os
from datetime import date
from pathlib import Path

# Paths
AGENT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_DIR = Path(r"c:\Users\admin\Desktop\Capstone_Project_Dataset_FTTT_2026")

if (AGENT_ROOT / "kb").exists():
    DATASET_DIR = AGENT_ROOT
else:
    DATASET_DIR = Path(os.environ.get("DATASET_DIR", str(DEFAULT_DATASET_DIR))).resolve()

KB_DIR = DATASET_DIR / "kb"
DATA_DIR = DATASET_DIR / "data"
PRACTICE_DIR = DATASET_DIR / "practice"
TOOLS_DIR = DATASET_DIR / "tools"
SAMPLE_OUTPUTS_DIR = AGENT_ROOT / "sample_outputs"

# Reference date frozen for Capstone: 20 October 2026
REFERENCE_DATE = date(2026, 10, 20)

# Official warehouse holidays
HOLIDAYS = {
    date(2026, 8, 15),  # Independence Day
    date(2026, 10, 2),  # Gandhi Jayanti
    date(2026, 10, 19), # Warehouse closure (festival)
    date(2026, 11, 9),  # Warehouse closure (festival)
}

# Precedence hierarchy weights (higher is better)
DOC_TYPE_PRECEDENCE = {
    "policy": 50,
    "agent_guide": 40,
    "help": 30,
    "faq": 20,
    "marketing": 10,
    "meta": 5,
}

# Gnani Voice settings
DEFAULT_TTS_VOICE = "Kaveri"
DEFAULT_TTS_MODEL = "timbre-v2.5"
DEFAULT_LANGUAGE_CODE = "en-IN"
DEFAULT_STT_LANGUAGE = "en-IN"
