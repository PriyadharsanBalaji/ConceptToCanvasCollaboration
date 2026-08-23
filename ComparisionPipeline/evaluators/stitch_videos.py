import os
import subprocess
from pathlib import Path
import sys
import shutil

def run_ffmpeg(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"FFmpeg Error: {result.stderr}")
    return result.returncode == 0

def stitch_videos(media_dir, audio_dir=None, output_file="full_stitched_video.mp4"):
    media_path = Path(media_dir)
    if not media_path.exists():
        print(f"Error: Could not find directory {media_dir}")
        return

    # Find all final mp4 files (ignoring partial movie files)
    print("Scanning for mp4 files...")
    video_files = []
    
    # Manim outputs look like: media/videos/scene_001/720p30/Scene_001.mp4
    for mp4_path in media_path.rglob("*.mp4"):
        if "partial_movie_files" not in mp4_path.parts and mp4_path.name != output_file:
            video_files.append(mp4_path)
            
    if not video_files:
        print("No valid MP4 files found to stitch!")
        return

    # Sort them so Scene_001 comes before Scene_002, etc.
    video_files.sort(key=lambda x: x.name)
    
    print(f"Found {len(video_files)} video clips to stitch.")
    
    files_to_stitch = video_files
    temp_dir = media_path / "temp_audio_mix"
    
    if audio_dir:
        audio_path = Path(audio_dir)
        if audio_path.exists():
            print(f"\nAudio directory provided! Mixing audio for each scene...")
            temp_dir.mkdir(exist_ok=True)
            files_to_stitch = []
            
            for vf in video_files:
                # Map Scene_001.mp4 to scene_001.mp3
                scene_name = vf.stem.lower() 
                mp3_file = audio_path / f"{scene_name}.mp3"
                mixed_out = temp_dir / vf.name
                
                if mp3_file.exists():
                    print(f" Mixing audio for {vf.name}...")
                    # Mix audio and video. If lengths differ, keep both streams intact.
                    cmd = [
                        "ffmpeg", "-y", 
                        "-i", str(vf), 
                        "-i", str(mp3_file), 
                        "-c:v", "copy", 
                        "-c:a", "aac", 
                        str(mixed_out)
                    ]
                    if run_ffmpeg(cmd):
                        files_to_stitch.append(mixed_out)
                    else:
                        files_to_stitch.append(vf)
                else:
                    print(f" Warning: No audio found for {vf.name}. Leaving silent.")
                    files_to_stitch.append(vf)
        else:
            print(f"\nWarning: Audio directory {audio_dir} not found. Proceeding without audio.")

    # FFmpeg requires a text file listing the inputs
    concat_list_path = media_path / "concat_list.txt"
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for vf in files_to_stitch:
            safe_path = str(vf.absolute()).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    output_path = media_path / output_file
    
    print("\nStitching final video with FFmpeg...")
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(output_path)
    ]
    
    if run_ffmpeg(cmd):
        print(f"\n[SUCCESS] All scenes have been stitched together.")
        print(f"Your final video is saved at:\n{output_path.absolute()}")
    else:
        print("\n[FAILED] FFmpeg failed to stitch the videos.")
        
    # Clean up temp files
    if concat_list_path.exists():
        concat_list_path.unlink()
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stitch_videos.py <path_to_media_dir> [path_to_audio_dir]")
        print("Example: python stitch_videos.py ../media/videos ../InputRunJson/book/audio")
    else:
        audio_d = sys.argv[2] if len(sys.argv) > 2 else None
        stitch_videos(sys.argv[1], audio_d)
