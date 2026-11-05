# ✨ Taleora — Illustrated Audio Storybook Generator

Taleora transforms three user-provided keywords into a complete illustrated and narrated storybook for children and young readers.

Built with Python, Google Gemini, Streamlit, Salesforce BLIP, Edge TTS, Meta MusicGen, ReportLab, and MoviePy.

---

## 🌟 Key Features

- **U1 — Genre and Audience Prompt Engineering:**
  - Structured prompt engine adhering to 6 distinct story genres (Fantasy, Sci-Fi, Adventure, Mystery, Fairy Tale, Bedtime Story).
  - 4 calibrated target audience tiers (Ages 3-5, 6-8, 9-12, 13+) controlling vocabulary, sentence length, and narrative complexity.
  - Strict 3-keyword integration validation.

- **U2 — Story Generation and Character Consistency:**
  - Gemini LLM structured story generation returning guaranteed Pydantic/JSON schemas.
  - Automatic Character Bible generation (physical traits, signature wardrobe, distinctive accessories).
  - Sequential scene breakdowns with character consistency tags pre-injected into image prompts.

- **U3 — Scene Image Generation and BLIP Verification:** *(Phase 2)*
  - High-resolution scene illustration generation.
  - Salesforce BLIP visual inspection & caption verification.

- **U4 — TTS Narration, MusicGen & Multi-Format Export:** *(Phase 3)*
  - Natural neural narration with Edge TTS.
  - Instrumental background music loops with Meta MusicGen.
  - Formatted illustrated PDF storybook via ReportLab.
  - Assembled MP4 storybook video with MoviePy & FFmpeg.

- **U5 — Child Safety & Originality Checking:** *(Phase 4)*
  - Wholesome content guardrail verification.
  - Originality & premise uniqueness scoring.

---

## 🚀 Quick Start Guide

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-username/Taleora.git
cd Taleora

# Create a Python 3.11 virtual environment
py -3.11 -m venv .venv

# Activate the virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

Copy `.env.example` to `.env` and insert your Google Gemini API Key:

```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

*(You can also enter your API key directly in the Streamlit application sidebar).*

### 4. Run the Application

```bash
streamlit run app.py
```

---

## 📁 Project Architecture

```text
Taleora/
├── app.py                      # Main Streamlit web application
├── config.py                   # Central configuration, genres, and audience tiers
├── requirements.txt            # Project dependencies
├── .env.example                # Example environment variable file
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
│
├── modules/
│   ├── prompt_engine.py        # U1: Genre, audience, and structured prompt construction
│   ├── character_manager.py    # U2: Character bible & visual consistency injection
│   ├── story_generator.py      # U2: Gemini LLM structured story generation & persistence
│   ├── image_generator.py      # U3: Scene image generator (Phase 2)
│   ├── blip_verifier.py        # U3: BLIP captioning & visual verification (Phase 2)
│   ├── audio_generator.py      # U4: Edge TTS scene narration (Phase 3)
│   ├── music_generator.py      # U4: MusicGen background music (Phase 3)
│   ├── safety_filter.py        # U5: Child safety content guardrail (Phase 4)
│   ├── originality_checker.py  # U5: Story originality & uniqueness scoring (Phase 4)
│   └── export_manager.py       # U4: PDF & MP4 video assembly (Phase 3)
│
├── outputs/
│   ├── stories/                # Saved story JSON structures
│   ├── images/                 # Generated scene illustrations
│   ├── audio/                  # TTS narration & generated music
│   ├── videos/                 # Assembled MP4 storybook videos
│   └── pdfs/                   # Exported illustrated PDF storybooks
│
└── assets/                     # Logos, sample assets, and previews
```

---

## 📜 License & Acknowledgements

Created for Academic GenAI Portfolio Demonstration.
Uses Google Gemini API, Salesforce BLIP, Microsoft Edge TTS, and Meta MusicGen.
