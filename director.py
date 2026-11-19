import os, json, re, urllib.request, urllib.parse, subprocess, glob

topic = open("topic.txt").read().strip() if os.path.exists("topic.txt") else ""

# 1. Optional Wikipedia Fact Research
if topic:
    try:
        q = urllib.parse.quote(topic)
        url = f"https://wikipedia.org{q}&gsrlimit=2"
        req = urllib.request.Request(url, headers={"User-Agent": "CGIStudioBot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        pages = data.get("query", {}).get("pages", {})
        facts = " ".join(p.get("extract", "") for p in pages.values())
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', facts) if len(s.strip()) > 25][:8]
        if sentences:
            with open("script.txt", "w") as f:
                f.write("\n".join(sentences) + "\n")
    except Exception as e:
        print("Using existing script.txt:", e)

with open("script.txt") as f:
    script_text = f.read().strip()

# 2. Generate Neural Voiceover + Exact Subtitles
subprocess.run([
    "edge-tts", "--voice", "en-US-ChristopherNeural", "--rate=+6%",
    "--file", "script.txt", "--write-media", "voiceover.mp3",
    "--write-subtitles", "captions.vtt"
], check=True)

total_dur = float(subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", "voiceover.mp3"
]).decode().strip())

# 3. Generate Background Drone + Ocean Wave SFX & Mix With Voiceover
subprocess.run([
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", f"aevalsrc=0.05*sin(2*PI*55*t)+0.03*sin(2*PI*82.5*t):d={total_dur}",
    "-f", "lavfi", "-i", f"anoisesrc=c=pink:a=0.02:d={total_dur}",
    "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=shortest[bg]",
    "-map", "[bg]", "bg_sfx.mp3"
], check=True)

subprocess.run([
    "ffmpeg", "-y", "-i", "voiceover.mp3", "-i", "bg_sfx.mp3",
    "-filter_complex", "[0:a]volume=1.35[vo];[1:a]volume=0.30[bg];[vo][bg]amix=inputs=2:duration=first[aout]",
    "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "full_audio.m4a"
], check=True)

# 4. Collect 3D Blender Renders + AI CGI Frames
shots = sorted(glob.glob("renders_3d/*.png"))[:4]
lines = [l.strip() for l in script_text.splitlines() if l.strip()]
os.makedirs("renders_ai", exist_ok=True)
style = "Unreal Engine 5 3D CGI render, hard amber sunlight shadows, teal atmosphere, cinematic 8k, vertical 9:16"

for i in range(6):
    beat = lines[i % len(lines)][:110]
    p = urllib.parse.quote(f"{beat}, {style}")
    u = f"https://pollinations.ai{p}?width=1080&height=1920&nologo=true&seed={300+i}"
    out_p = f"renders_ai/ai_{i:02d}.jpg"
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r, open(out_p, "wb") as f:
            img_bytes = r.read()
            if len(img_bytes) > 5000:
                f.write(img_bytes)
                shots.append(out_p)
    except Exception:
        pass

if not shots:
    raise RuntimeError("No visual shots available")

# 5. Render each shot individually with smooth 3D camera zoom + fade transitions (100% crash-proof)
shot_dur = total_dur / len(shots)
frames_per_shot = max(30, int(shot_dur * 30))
clip_paths = []

for idx, img in enumerate(shots):
    clip = f"clip_{idx:02d}.mp4"
    z_expr = "min(zoom+0.0010,1.18)" if idx % 2 == 0 else "max(1.18-0.0010*on,1.0)"
    fade_out_st = max(0.1, shot_dur - 0.35)
    vf = (
        f"scale=2160:3840,zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames_per_shot}:s=1080x1920:fps=30,setsar=1,"
        f"fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out_st:.2f}:d=0.35,format=yuv420p"
    )
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-t", f"{shot_dur:.2f}", "-i", img,
        "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", clip
    ], check=True)
    clip_paths.append(clip)

with open("concat.txt", "w") as f:
    for c in clip_paths:
        f.write(f"file '{os.path.abspath(c)}'\n")

subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt",
    "-c", "copy", "base_video.mp4"
], check=True)

# 6. Apply Vignette, Top Title, Red Number Overlays & Bottom Subtitles
with open("captions.vtt") as f:
    vtt = f.read()

red_cues = []
for b in vtt.strip().split("\n\n"):
    lns = b.splitlines()
    for idx_line, line in enumerate(lns):
        if "-->" in line and idx_line + 1 < len(lns):
            t_start = line.split("-->").strip()
            p = re.split("[:.]", t_start)
            if len(p) >= 4:
                sec = int(p)*3600 + int(p)*60 + int(p) + int(p)/1000.0
                txt = " ".join(lns[idx_line+1:])
                nums = re.findall(r'\b(?:\$?\d[\d,.]*\s*(?:million|billion|trillion|ships|carats|years|men|%|CT)?)\b', txt, re.I)
                if nums and len(nums.strip()) >= 2:
                    red_cues.append((sec, sec + 2.5, nums.upper().strip()))
            break

title = (topic.upper() if topic else "SEA RAIDERS OF INDIA")[:28].replace(":", "\\:").replace("'", "")
overlays = [
    "vignette=PI/4",
    "drawbox=x=0:y=1150:w=1080:h=770:color=black@0.45:t=fill",
    f"drawtext=text='{title}':fontcolor=white@0.85:shadowcolor=black:shadowx=3:shadowy=3:fontsize=36:x=(w-text_w)/2:y=85"
]

for st, en, badge in red_cues:
    safe = badge.replace(":", "\\:").replace("'", "")
    overlays.append(
        f"drawtext=text='{safe}':fontcolor=#ff2626:borderw=5:bordercolor=black:shadowcolor=black@0.8:shadowx=5:shadowy=5:"
        f"fontsize=72:x=(w-text_w)/2:y=1180:enable='between(t,{st:.2f},{en:.2f})'"
    )

overlays.append(
    "subtitles=captions.vtt:force_style='Alignment=2,MarginV=125,Fontsize=21,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Shadow=2,Outline=2'"
)

subprocess.run([
    "ffmpeg", "-y", "-i", "base_video.mp4", "-i", "full_audio.m4a",
    "-vf", ",".join(overlays),
    "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
    "-c:a", "copy", "-shortest", "cgi_studio_final.mp4"
], check=True)
print("FINISHED SUCCESSFULLY!")
