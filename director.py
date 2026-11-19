import os, sys, json, re, urllib.request, urllib.parse, subprocess

topic = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""

# Step A: If a new topic is passed, research real facts from Wikipedia API and build script.txt
if topic:
    print(f"Researching real facts for: {topic}")
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

# Step B: Read script.txt and generate neural voiceover + exact VTT timestamps
with open("script.txt") as f:
    script_text = f.read().strip()

subprocess.run([
    "edge-tts", "--voice", "en-US-ChristopherNeural", "--rate=+6%",
    "--file", "script.txt", "--write-media", "voiceover.mp3",
    "--write-subtitles", "captions.vtt"
], check=True)

dur_out = subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", "voiceover.mp3"
]).decode().strip()
total_dur = float(dur_out)

# Step C: Generate high-detail Unreal-style 3D CGI frames for each beat via Flux API
lines = [l.strip() for l in script_text.splitlines() if l.strip()]
num_shots = min(max(len(lines), 4), 10)
shot_dur = total_dur / num_shots
os.makedirs("renders", exist_ok=True)

style_suffix = "stylized photoreal 3D CGI render, Unreal Engine 5 Lumen lighting, hard amber key light, deep teal shadows, dramatic volumetric fog, vertical 9:16 composition, 8k"
img_paths = []

for i in range(num_shots):
    beat = lines[i % len(lines)][:140]
    prompt = urllib.parse.quote(f"{beat}, {style_suffix}")
    img_url = f"https://pollinations.ai{prompt}?width=1080&height=1920&nologo=true&seed={100+i}"
    out_img = f"renders/shot_{i:02d}.jpg"
    print(f"Generating CGI shot {i+1}/{num_shots}...")
    req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(out_img, "wb") as f:
        f.write(r.read())
    img_paths.append(out_img)

# Step D: Extract numbers/dates from VTT for bold red 3D-style keyword overlays
with open("captions.vtt") as f:
    vtt = f.read()

red_cues = []
for b in vtt.strip().split("\n\n"):
    lns = b.splitlines()
    if len(lns) >= 3 and "-->" in lns[1]:
        t_start = lns[1].split("-->")[0].strip()
        p = re.split("[:.]", t_start)
        sec = int(p[0])*3600 + int(p[1])*60 + int(p[2]) + int(p[3])/1000.0
        txt = " ".join(lns[2:])
        nums = re.findall(r'\b(?:\$?\d[\d,.]*\s*(?:million|billion|trillion|ships|carats|years|men|%|CT)?)\b', txt, re.I)
        if nums:
            badge = nums[0].upper().strip()
            if len(badge) >= 2:
                red_cues.append((sec, sec + 2.8, badge))

# Step E: Smooth 3D Camera Motion, Cross-Dissolves, Shadows, Fonts & Subtitles in FFmpeg
inputs = []
filter_parts = []
frames_per_shot = int(shot_dur * 30) + 15

for idx, img in enumerate(img_paths):
    inputs += ["-loop", "1", "-t", f"{shot_dur + 0.5:.2f}", "-i", img]
    zoom_dir = "min(zoom+0.0012,1.22)" if idx % 2 == 0 else "max(1.22-0.0012*on,1.0)"
    filter_parts.append(
        f"[{idx}:v]scale=2160:3840,zoompan=z='{zoom_dir}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_per_shot}:s=1080x1920:fps=30,setsar=1,format=yuv420p[v{idx}];"
    )

# Chain smooth xfade transitions between every shot
prev = "[v0]"
for idx in range(1, len(img_paths)):
    offset = idx * shot_dur - 0.4
    out_lbl = f"[xf{idx}]"
    filter_parts.append(f"{prev}[v{idx}]xfade=transition=fadeblack:duration=0.4:offset={offset:.2f}{out_lbl};")
    prev = out_lbl

# Add cinema vignette, shadow gradient, top title, dynamic red numbers, and white captions
title_text = (topic.upper() if topic else "SEA RAIDERS OF INDIA")[:28].replace(":", "\\:")
fx = [
    f"{prev}vignette=PI/4,eq=contrast=1.10:saturation=1.18",
    "drawbox=x=0:y=1150:w=1080:h=770:color=black@0.48:t=fill",
    f"drawtext=text='{title_text}':fontcolor=white@0.85:shadowcolor=black:shadowx=3:shadowy=3:fontsize=36:x=(w-text_w)/2:y=85"
]

for start, end, badge in red_cues:
    safe = badge.replace(":", "\\:").replace("'", "")
    fx.append(
        f"drawtext=text='{safe}':fontcolor=#ff2626:borderw=5:bordercolor=black:shadowcolor=black@0.8:shadowx=6:shadowy=6:"
        f"fontsize=74:x=(w-text_w)/2:y=1180:enable='between(t,{start:.2f},{end:.2f})'"
    )

fx.append(
    "subtitles=captions.vtt:force_style='Alignment=2,MarginV=125,Fontsize=21,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Shadow=2,Outline=2'[outv]"
)

inputs += ["-i", "voiceover.mp3"]
full_filter = "".join(filter_parts) + ",".join(fx)

subprocess.run([
    "ffmpeg", "-y", *inputs, "-filter_complex", full_filter,
    "-map", "[outv]", "-map", f"{len(img_paths)}:a",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", "cgi_studio_final.mp4"
], check=True)
print("SUCCESS: cgi_studio_final.mp4 rendered!")
