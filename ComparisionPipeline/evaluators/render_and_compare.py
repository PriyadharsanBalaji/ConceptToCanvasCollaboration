import subprocess
from pathlib import Path
import sys

def render_and_compare(py_dir):
    """
    Finds all generated .py files from Claude/Gemini,
    compiles them using Manim, and reports success/failure.
    """
    py_dir = Path(py_dir)
    if not py_dir.exists():
        print(f"Error: Directory {py_dir} not found.")
        return

    py_files = sorted(list(py_dir.glob("*.py")))
    if not py_files:
        print(f"No Python files found in {py_dir}. Did you paste the LLM outputs here?")
        return
        
    print(f"Found {len(py_files)} scenes to render in {py_dir}")
    print("="*60)
    
    success_count = 0
    fail_count = 0

    # Ensure videos don't overwrite each other by saving them in the evaluated folder
    media_out = py_dir / "media"
    
    # Use the specific venv where Manim is installed
    venv_python = r"E:\ProjectM\CTC_Production\V1\venv\Scripts\python.exe"
    python_exe = venv_python if Path(venv_python).exists() else sys.executable

    for py_file in py_files:
        print(f"\nRendering {py_file.name}...")
        
        cmd = [python_exe, "-m", "manim", "-qm", "--media_dir", str(media_out), str(py_file)]
        
        # Run manim subprocess
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"[SUCCESS] {py_file.name} rendered without errors.")
            success_count += 1
        else:
            print(f"[FAILED] {py_file.name} threw a Manim syntax/compilation error.")
            # Print the last few lines of the error to help debug
            error_lines = result.stderr.strip().split("\n")
            print("   ERROR: " + "\n   ".join(error_lines[-5:]))
            fail_count += 1

    print("\n" + "="*60)
    print(f"RENDER COMPARISON RESULTS:")
    print(f"Total Scenes Attempted: {len(py_files)}")
    print(f"Successful Compiles:    {success_count}")
    print(f"Failed Compiles:        {fail_count}")
    print("="*60)
    print("Note: If a scene fails, Claude/Gemini likely hallucinated invalid Manim functions.")
    print("Compare this success rate against the baseline 'maternion/manim-coder'!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_and_compare.py <path_to_directory_with_py_files>")
        print("Example: python render_and_compare.py Run1/outputs/claude_manim")
    else:
        render_and_compare(sys.argv[1])
