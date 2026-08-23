import json
import os
import sys
import shutil
from pathlib import Path

# These are exactly identical to the prompts in stages/manim_codegen.py
MANIM_SYSTEM = """You are an expert Manim Community Edition (ManimCE) programmer.
You generate clean, executable Python code that creates beautiful mathematical animations.

RULES:
1. Always import from manim: `from manim import *`
2. Use ONE class per scene, inheriting from Scene.
3. Class name MUST be named with the Scene_ Prefix followed by 3 digits (e.g. Scene_001, Scene_002).
4. Implement the construct(self) method.
5. Use self.play() for animations, self.wait() for pauses.
6. Use standard ManimCE objects: Text, MathTex, Tex, Circle, Square, Rectangle, Arrow, NumberLine, Axes, VGroup, etc.
7. Use raw strings for MathTex: MathTex(r"...")
8. Set background color in construct: self.camera.background_color = "#1a1a2e"
9. Avoid syntax errors, ensure all parentheses (), brackets [], and quotes "" are perfectly matched.
10. Manim coordinates MUST be 3D: [x, y, 0] or np.array([x, y, 0]). NEVER pass 2D points [x, y].
11. Polygon vertices: Use polygon.get_vertices()[i]. NEVER call .get_edge(i).
12. NEVER load external image files or ImageMobject("path.jpg"). Always use pure vector Mobjects (Rectangle, Text, etc.).
13. Output ONLY executable Python code inside ```python ``` blocks."""


MANIM_PROMPT = """Generate a Manim scene for this educational animation:

SCENE ID: {scene_id} (class name MUST be Scene_{scene_id_padded})
TITLE: {title}
DURATION: ~{duration}s of animation

NARRATION (what the voiceover says — animate in sync with this):
{narration}

VISUAL DESCRIPTION (what the viewer should see):
{visual_description}

MANIM INTENT (specific animation instructions):
{manim_intent}

KEY OBJECTS TO USE: {key_objects}

ON-SCREEN TEXT/EQUATIONS:
{on_screen_text}

BACKGROUND COLOR: {bg_color}
ACCENT COLORS: {accent_colors}

Generate the complete Python file inside a ```python ``` block. Remember:
- Class name: Scene_{scene_id_padded}
- from manim import *
- Beautiful, smooth animations
- Clean positioning (use .to_edge(), .shift(), .next_to())
- Match the narration timing with self.wait() calls"""


def extract_prompts(storyboard_path, run_name="Run1"):
    """Reads storyboard.json and dumps identical .txt prompts into the specified Run directory."""
    storyboard_path = Path(storyboard_path)
    if not storyboard_path.exists():
        print(f"Error: {storyboard_path} not found.")
        return
        
    book_name = storyboard_path.parent.name
    
    base_dir = Path(__file__).parent / run_name
    claude_in_dir = base_dir / "inputs" / "claude" / book_name
    gemini_in_dir = base_dir / "inputs" / "gemini" / book_name
    claude_out_dir = base_dir / "outputs" / "claude" / book_name
    gemini_out_dir = base_dir / "outputs" / "gemini" / book_name
    
    claude_in_dir.mkdir(parents=True, exist_ok=True)
    gemini_in_dir.mkdir(parents=True, exist_ok=True)
    claude_out_dir.mkdir(parents=True, exist_ok=True)
    gemini_out_dir.mkdir(parents=True, exist_ok=True)

    with open(storyboard_path, "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    # Collect all scenes
    all_scenes = []
    for section in storyboard.get("sections", []):
        for scene in section.get("scenes", []):
            all_scenes.append(scene)

    print(f"[{book_name}] Found {len(all_scenes)} scenes. Generating prompt text files...")

    for i, scene in enumerate(all_scenes):
        scene_id = scene.get("global_scene_id", scene.get("scene_id", i + 1))
        scene_id_padded = f"{scene_id:03d}"
        
        on_screen_text = scene.get("on_screen_text", [])
        if isinstance(on_screen_text, list):
            on_screen_text = "\n".join(f"  - {t}" for t in on_screen_text)

        key_objects = scene.get("key_objects", [])
        if isinstance(key_objects, list):
            key_objects = ", ".join(key_objects)

        user_prompt = MANIM_PROMPT.format(
            scene_id=scene_id,
            scene_id_padded=scene_id_padded,
            title=scene.get("title", "Untitled"),
            duration=scene.get("duration_seconds", 30),
            narration=scene.get("narration_text", ""),
            visual_description=scene.get("visual_description", ""),
            manim_intent=scene.get("manim_intent", ""),
            key_objects=key_objects,
            on_screen_text=on_screen_text or "(none)",
            bg_color=scene.get("background_color", "#1a1a2e"),
            accent_colors=", ".join(scene.get("accent_colors", ["#e94560", "#0f3460"])),
        )

        full_prompt = f"### SYSTEM INSTRUCTIONS (Paste this into the System Prompt / Project Instructions if possible):\n{MANIM_SYSTEM}\n\n"
        full_prompt += f"----------------------------------------------------\n\n"
        full_prompt += f"### USER PROMPT:\n{user_prompt}\n"

        prompt_name = f"scene_{scene_id_padded}_prompt.txt"
        py_name = f"scene_{scene_id_padded}.py"
        
        # Save identical copies to both Claude and Gemini input directories
        with open(claude_in_dir / prompt_name, "w", encoding="utf-8") as f:
            f.write(full_prompt)
            
        with open(gemini_in_dir / prompt_name, "w", encoding="utf-8") as f:
            f.write(full_prompt)
            
        # Pre-create empty python files to make pasting easier
        with open(claude_out_dir / py_name, "w", encoding="utf-8") as f:
            f.write("# Paste Claude's generated python code here\n")
            
        with open(gemini_out_dir / py_name, "w", encoding="utf-8") as f:
            f.write("# Paste Gemini's generated python code here\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_manim_prompts.py <path_to_storyboard.json> [run_name]")
        print("Example: python extract_manim_prompts.py ../outputs/book/storyboard.json Run1")
    else:
        sb_path = sys.argv[1]
        run_name = sys.argv[2] if len(sys.argv) > 2 else "Run1"
        extract_prompts(sb_path, run_name)
