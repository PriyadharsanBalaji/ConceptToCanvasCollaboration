# Concept to Canvas Collaboration

Welcome to the **Concept to Canvas** pipeline. This repository houses an automated, end-to-end educational pipeline that autonomously converts raw educational PDFs (like textbook chapters) into fully animated, fully narrated, 30-60 minute educational videos using Manim CE and Large Language Models.

---

## 🚀 How to Run the Pipeline

The pipeline is orchestrated by `pipeline.py`. It is highly modular and resumable. 

**Basic Run (End-to-End):**
```bash
python pipeline.py --pdf path/to/book.pdf
```

**Generate Storyboard Only (Stops after Stage 2):**
```bash
python pipeline.py --pdf path/to/book.pdf --plan-only
```

**Resume from a Crash / Specific Stage:**
```bash
# Example: Resume from Stage 3 (Manim Code Generation)
python pipeline.py --pdf path/to/book.pdf --resume --stage 3
```

---

## 🧠 The 6-Stage Core Pipeline

When you run `pipeline.py`, the system processes your PDF through 6 distinct stages. All intermediate outputs are saved into a dedicated directory based on the PDF's name. Here is exactly what happens under the hood at every stage:

### Stage 0: PDF Text Extraction (`stages/pdf_extractor.py`)
- **Input:** Raw `.pdf` file (e.g., `iemh101.pdf`).
- **Process:** Parses the PDF using PyMuPDF to extract raw text, categorize headings, and identify structured data like examples and exercises.
- **Output:** `chapter_content.json` — A highly structured JSON representation of the entire chapter's text.

### Stage 1: Deep Analysis (`stages/deep_analyzer.py`)
- **Input:** `chapter_content.json`
- **Process:** An LLM analyzes the raw chapter content to determine the optimal pedagogical structure. It plans the pacing, difficulty curve, and high-level visual requirements necessary to teach the concepts effectively.
- **Output:** `deep_analysis.json` — The pedagogical master plan.

### Stage 2: Storyboard Planning (`stages/storyboard_planner.py`)
- **Input:** `deep_analysis.json`
- **Process:** An LLM breaks the pedagogical plan down into discrete ~30-second "scenes". For every single scene, it generates a perfect Voiceover Narration script and highly specific "Visual Intents" detailing exactly what needs to be drawn on screen to match the audio.
- **Output:** `storyboard.json` — The ultimate master blueprint containing every scene, script, and visual cue.

### Stage 3: Manim Code Generation (`stages/manim_codegen.py`)
- **Input:** `storyboard.json`
- **Process:** The pipeline feeds each scene's detailed storyboard prompt into a specialized code generation model (like `manim-coder`). The model writes executable Python classes inheriting from Manim's `Scene`.
- **Output:** Raw `.py` script files dumped into the `scenes/` folder.

### Stage 4: Audio Generation (`stages/audio_generator.py`)
- **Input:** The `narration_text` from `storyboard.json`.
- **Process:** Connects to a Text-To-Speech (TTS) engine to synthesize the voiceover for every single scene.
- **Output:** Voiceover `.mp3` files dumped into the `audio/` folder.

### Stage 5: Rendering & Assembly (`stages/renderer.py` & `stages/assembler.py`)
- **Input:** The `.py` Manim scripts and the `.mp3` audio files.
- **Process:** `renderer.py` compiles the Python code into MP4s using the local Manim CE engine. Then, `assembler.py` uses FFmpeg to perfectly mix the visual MP4s with their corresponding audio MP3s, and stitches all scenes chronologically.
- **Output:** `final_video.mp4` — The fully completed educational video.

---

## 🧪 The LLM Comparison Workflow (`ComparisionPipeline/`)

This repository also contains a dedicated evaluation sandbox located in the `ComparisionPipeline/` directory. 

We use this to manually test and benchmark massive API models (like **Claude** and **Gemini**) against our local `manim-coder` model to see who generates better mathematical animations.

### How it works:
1. **Prompt Extraction:** It hijacks the output from **Stage 2** (`storyboard.json`). By running `extract_manim_prompts.py`, we convert the JSON into strict `.txt` prompts containing the System Prompt and User Prompt.
2. **Manual Generation:** You paste these text prompts into Claude or Gemini's web UI, and paste their generated python code back into the `outputs/` folder.
3. **Automated Evaluation:** You run `evaluators/render_and_compare.py`. This script automatically tests the LLM's code for syntax errors and renders the Manim videos into isolated media folders.
4. **Stitching & Mixing:** You run `evaluators/stitch_videos.py`. This script automatically grabs the original TTS audio files from **Stage 4** of the main pipeline, frame-perfectly mixes them with Claude/Gemini's new animations, and stitches them into a final comparative video.

*For complete details on the prompt architecture and testing commands, read the dedicated `ComparisionPipeline/README.md` inside that folder!*
