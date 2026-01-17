import os
import subprocess
import math
import sys

def get_duration(file_path):
    """Get the duration of the audio file in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        # Run ffprobe to get duration
        if os.name == 'nt':
            # Hide console window on Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            startupinfo = None

        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=True,
            startupinfo=startupinfo
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration for {os.path.basename(file_path)}: {e}", flush=True)
        return None

def process_audio(file_paths, speed_factor, segment_length_mins=15, output_base_dir='.'):
    print("Starting audio processing with FFmpeg (Direct Mode)...", flush=True)
    
    # Convert minutes to milliseconds
    segment_length_sec = segment_length_mins * 60
    output_path = os.path.join(output_base_dir, "processed_audio")
    os.makedirs(output_path, exist_ok=True)
    print(f"Output directory ensured: {output_path}", flush=True)
    
    # Prepare filter string for speed change (Time Stretch without pitch shift)
    # atempo filter is limited to 0.5 to 2.0. Chain them for other values.
    filter_chain = []
    s = speed_factor
    while s > 2.0:
        filter_chain.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        filter_chain.append("atempo=0.5")
        s /= 0.5
    if s != 1.0:
        filter_chain.append(f"atempo={s}")
    
    filter_str = ",".join(filter_chain)
    filter_args = ["-filter:a", filter_str] if filter_str else []

    # Process all provided file paths
    for file_path in file_paths:
        if not file_path.lower().endswith('.mp3'):
            continue

        print(f"\nProcessing: {file_path}", flush=True)
        
        duration = get_duration(file_path)
        if duration is None:
            continue

        num_segments = math.ceil(duration / segment_length_sec) if segment_length_sec > 0 else 1
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        ext = ".mp3"

        for i in range(num_segments):
            start_time = i * segment_length_sec
            
            # Generate output filename
            if num_segments > 1:
                segment_filename = f"speed_{speed_factor}x_part{i+1:03d}_{base_name}{ext}"
            else:
                segment_filename = f"speed_{speed_factor}x_{base_name}{ext}"
            
            output_file = os.path.join(output_path, segment_filename)
            
            print(f"  Segment {i+1}/{num_segments}: Start {start_time:.1f}s -> {output_file}", flush=True)

            # Construct FFmpeg command
            cmd = [
                "ffmpeg",
                "-y",                   # Overwrite output
                "-ss", str(start_time), # Seek input (fast)
                "-t", str(segment_length_sec), # Duration
                "-i", file_path,        # Input file
                "-progress", "pipe:1",  # Output progress to stdout
                "-vn"                   # No video
            ] + filter_args + [output_file]

            # Run FFmpeg
            try:
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                else:
                    startupinfo = None

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, # Merge stderr into stdout
                    text=True,
                    startupinfo=startupinfo
                )

                # Read progress line by line
                for line in process.stdout:
                    line = line.strip()
                    # Only print time updates to keep log clean, or errors
                    if line.startswith("out_time="):
                        # Print progress on the same line if possible, or just log it
                        # For GUI log, simple print is safer
                        print(f"    Progress: {line}", flush=True)
                    elif "Error" in line or "Invalid" in line:
                        print(f"    {line}", flush=True)
                
                process.wait()
                
                if process.returncode == 0:
                    print("    Done.", flush=True)
                else:
                    print(f"    Failed with return code {process.returncode}", flush=True)

            except Exception as e:
                print(f"    Error running FFmpeg: {e}", flush=True)

    print("Audio processing complete.", flush=True)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process MP3 files: Change speed and split.")
    parser.add_argument("inputs", nargs="+", help="MP3 files or folders containing MP3s")
    parser.add_argument("--speed", type=float, default=1.5, help="Speed factor (default: 1.5)")
    parser.add_argument("--length", type=int, default=15, help="Segment length in minutes (default: 15)")

    args = parser.parse_args()

    files_to_process = []
    for input_path in args.inputs:
        if os.path.isfile(input_path) and input_path.lower().endswith(".mp3"):
            files_to_process.append(input_path)
        elif os.path.isdir(input_path):
            for root, _, files in os.walk(input_path):
                for file in files:
                    if file.lower().endswith(".mp3"):
                        files_to_process.append(os.path.join(root, file))

    if files_to_process:
        process_audio(files_to_process, args.speed, args.length)
    else:
        print("No MP3 files found.")
