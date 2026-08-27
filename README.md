# Concept to Canvas Collaboration: Architectural Blueprint

Welcome to the **Concept to Canvas** repository. This is an advanced, fully automated educational pipeline. It autonomously ingests raw educational PDFs (like NCERT textbooks) and converts them into 30-60 minute, fully narrated, 3Blue1Brown-style Manim educational videos.

This README serves as the complete architectural blueprint of the system, detailing the exact internal workings, LLM prompts, and JSON schemas that power each stage.

---

## 🧠 The 6-Stage Pipeline Architecture

The entire process is orchestrated by `pipeline.py`. When you run the pipeline, it passes your PDF through 6 deeply integrated stages.

### Stage 0: PDF Text Extraction (`stages/pdf_extractor.py`)
This stage transforms the unstructured PDF into a machine-readable format.
- **Input:** Raw `.pdf` file.
- **Internal Mechanism:** Uses `PyMuPDF` to iterate through every page. It heuristically categorizes text blocks into regular paragraphs, section headings, and identifies structured elements like "Examples" and "Exercises".
- **Output:** `chapter_content.json`. This contains the raw `chapter_title`, `num_pages`, and a structured array of `sections` and `examples` extracted directly from the text.

### Stage 1: Deep Analysis (`stages/deep_analyzer.py`)
This stage acts as the "Subject Matter Expert". It doesn't write the script; it figures out *how* to teach the material.
- **Input:** `chapter_content.json`
- **The Prompt:** The LLM is instructed to act as an expert educational content analyst specializing in Indian school curricula. It is explicitly commanded to go *far beyond* the textbook by adding historical context, surprising connections, and exam tricks.
- **Output Schema (`deep_analysis.json`):** The LLM is forced to output this exact JSON structure:
  ```json
  {
      "ancient_history": [
          {"era": "...", "person": "...", "event": "...", "fun_angle": "..."}
      ],
      "core_concepts": [
          {"name": "...", "definition": "...", "intuition": "...", "visual_idea": "..."}
      ],
      "misconceptions": [
          {"wrong_belief": "...", "correct_understanding": "...", "visual_fix": "..."}
      ],
      "fun_facts": [],
      "tricks_and_shortcuts": [],
      "worked_examples": []
  }
  ```

### Stage 2: Storyboard Planning (`stages/storyboard_planner.py`)
This stage acts as the "Director". It takes the raw pedagogical concepts and maps them into a strict cinematic flow.
- **Input:** `deep_analysis.json`
- **The Prompt:** The LLM acts as an award-winning director creating 3Blue1Brown-style videos. We enforce a strict pedagogical arc: **Hook (1-2 scenes) → History (4-6 scenes) → Core Concepts (Intuition then Definition) → Misconceptions → Examples → Summary.**
- **Output Schema (`storyboard.json`):** This is the ultimate master blueprint. It generates an array of 50-80 individual "scenes". Each scene looks like this:
  ```json
  {
      "scene_id": 1,
      "teaching_beat": "HOOK",
      "narration_text": "The exact voiceover script to be read aloud (40-80 words).",
      "visual_description": "What the viewer physically sees on screen.",
      "manim_intent": "Precise Manim instructions (e.g., use FadeIn, Transform, VGroup).",
      "key_objects": ["MathTex", "Circle", "NumberLine"],
      "on_screen_text": ["Any specific LaTeX equations"]
  }
  ```

### Stage 3: Manim Code Generation (`stages/manim_codegen.py`)
This stage acts as the "Programmer". It translates the storyboard intent into executable Python code.
- **Input:** `storyboard.json`
- **The Process:** We loop through every single scene in the storyboard and feed it to the `manim-coder` model. 
- **The System Rules:** To prevent Manim hallucinations, the LLM is forced to obey 13 strict rules, including:
  1. Class names MUST be `Scene_XXX`.
  2. Inherit strictly from `Scene`.
  3. Manim coordinates MUST be 3D `[x, y, 0]` (prevents 2D array crashes).
  4. NEVER load external image files; use pure vector objects.
- **Output:** Raw `.py` script files dumped into the `scenes/` folder.

### Stage 4: Audio Generation (`stages/audio_generator.py`)
- **Input:** The `narration_text` strings from `storyboard.json`.
- **Process:** Connects to a Text-To-Speech (TTS) engine. It iterates through every scene and synthesizes a warm, engaging voiceover.
- **Output:** Voiceover `.mp3` files dumped into the `audio/` folder.

### Stage 5: Rendering & Assembly (`stages/renderer.py` & `stages/assembler.py`)
- **Input:** The `.py` Manim scripts and the `.mp3` audio files.
- **Process:** 
  1. `renderer.py` loops through all python files and runs `manim -qm` to compile them into `.mp4` video segments.
  2. `assembler.py` uses FFmpeg to multiplex each visual `.mp4` with its matching `.mp3`. If the audio is longer than the animation, the animation freezes on the last frame perfectly. 
  3. Finally, FFmpeg concatenates all 50-80 mixed scenes sequentially.
- **Output:** `final_video.mp4` — The fully completed educational video.

---

## 🧪 The LLM Comparison Workflow (`ComparisionPipeline/`)

How does our local `manim-coder` stack up against giant API models like **Claude** and **Gemini**? 

We built the `ComparisionPipeline/` directory as an evaluation sandbox to manually test this.

### The Evaluation Workflow:
1. **Extraction (`extract_manim_prompts.py`):** We "hijack" the `storyboard.json` generated at the end of Stage 2. This script converts the JSON back into exact `.txt` prompts containing the System Instructions (the 13 strict rules) and the User Prompt (the exact Scene intent).
2. **Generation:** You manually paste these prompts into the Claude/Gemini UI, and paste their generated python code into the `outputs/` folder.
3. **Automated Evaluation (`evaluators/render_and_compare.py`):** This script automatically tests the API LLM's code. It runs Manim locally, utilizing the `--media_dir` flag to isolate output videos so Claude and Gemini don't overwrite each other. It outputs a success/failure compile report.
4. **Stitching & Mixing (`evaluators/stitch_videos.py`):** This script automatically grabs the original TTS audio files from **Stage 4** of the main pipeline, frame-perfectly mixes them with Claude/Gemini's new animations using FFmpeg, and stitches them into a final comparative video.

---

## 📚 V2: Iterative Whole-Book Processing (New Architecture)

In **V2**, we introduced a major architectural change to solve the LLM "Context Window Limit". 

When passing an entire 200-page textbook to `qwen2.5:14b`, the LLM would hit its ~35,000 character limit and severely truncate the output, meaning you only ever got a video about the *first chapter*.

**How V2 Solves This (`--whole-book`):**
1. **The Chunker:** When you run `run.py --whole-book`, Stage 0 extracts the entire PDF as normal into `master_content.json`. However, it then mathematically divides the book into logical "chunks" of exactly 25,000 characters each.
2. **Iterative Isolation:** The pipeline then loops over these chunks. It creates completely isolated sub-directories (e.g., `chunk_1/`, `chunk_2/`) and runs all 5 Stages (Deep Analysis → Assembly) *inside* that specific folder independently.
3. **Super Assembly:** Once all chunks have successfully produced their own fully narrated Manim video (`final_...mp4`), V2 automatically boots up a final FFmpeg "Super Assembly" process that seamlessly stitches all the chunk videos together (preserving all audio tracks!) into one master `THE_COMPLETE_BOOK.mp4`.

This guarantees that you can process infinitely long textbooks without ever dropping data!

---

## 🎬 V3: Reel-Style Continuous Flow & Advanced Formatting (New Architecture)

In **V3**, we introduced a complete narrative and formatting overhaul based on user feedback that the videos felt too rigid, contained boring historical trivia, and suffered from text overlapping/spilling off-screen.

**What pushed us to this decision:**
1. **Pacing:** The LLMs were strictly following a textbook-like chapter structure (Hook -> History -> Core Concept), making the videos feel disjointed rather than like a viral, fast-paced YouTube Reel.
2. **Engagement:** History and dates were slowing down the "Wow!" factor of the math.
3. **Manim Bugs:** The LLM was occasionally writing text over existing text, or making text too large for the camera frame.

**How V3 Solves This:**
1. **Purged History:** `deep_analyzer.py` was rewritten to completely ban ancient history and trivia, replacing it with `real_world_application` (e.g., video game physics) to keep kids hooked.
2. **Continuous Flow Narrative:** `storyboard_planner.py`'s rigid 7-part arc was destroyed. It now uses a "Continuous Journey" directive. Every single scene MUST end with a transition phrase or cliffhanger question that leads perfectly into the next scene. 
3. **Advanced Manim Constraints:** `manim_codegen.py` was updated with critical formatting rules:
   - **No Off-Screen Text:** Enforced `.scale_to_fit_width(config.frame_width - 1)`.
   - **No Overlapping Text:** Enforced clearing the screen (`self.clear()`) or stacking cleanly (`VGroup.arrange(DOWN)`) before introducing new concepts.

---

## ⚙️ Execution Commands

**Run the Full Main Pipeline (Single Chapter):**
```bash
python run.py --pdf iemh101.pdf
```

**Run V2 Whole-Book Processing:**
```bash
# Process the entire book automatically by chunking it!
python run.py --pdf iemh101.pdf --whole-book

# Limit the whole book processing to the first 5 chunks
python run.py --pdf iemh101.pdf --whole-book --max-chunks 5
```
