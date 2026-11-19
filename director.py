import os, sys, json, re, urllib.request, urllib.parse, subprocess, glob

topic = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""

if topic:
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

with open("script.txt") as f:
    script_text = f.read().strip()

# Generate Voiceover + Captions
subprocess.run([
    "edge-tts", "--voice", "en-US-ChristopherNeural", "--rate=+6%",
    "--file", "script.txt", "--write-media", "voiceover.mp3",
    "--write-subtitles", "captions.vtt"
], check=True)

total_dur = float(subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", "voiceover.mp3"
]).decode().strip())

# Generate Cinematic Background Drone + Ocean Wave Sound Effects via FFmpeg
subprocess.run([
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", f"aevalsrc=0.06*sin(2*PI*55*t)+0.04*sin(2*PI*82.5*t):d={total_dur}",
    "-f", "lavfi", "-i", f"anoisesrc=c=pink:a=0.025:d={total_dur}",
    "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=shortest,afade=t=in:d=1.5,afade=t=out:st=" + str(max(0, total_dur-2)) + ":d=2[bg]",
    "-map", "[bg]", "bg_sfx.mp3"
], check=True)

# Mix Voiceover + Background Music & Ocean SFX
subprocess.run([
    "ffmpeg", "-y", "-i", "voiceover.mp3", "-i", "bg_sfx.mp3",
    "-filter_complex", "[0:a]volume=1.35[vo];[1:a]volume=0.35[bg];[vo][bg]amix=inputs=2:duration=first[aout]",
    "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "full_audio.m4a"
], check=True)

# Collect 3D Blender Renders + Generate AI CGI Scenes
shots = sorted(glob.glob("renders_3d/*.png"))[:4]
lines = [l.strip() for l in script_text.splitlines() if l.strip()]
os.makedirs("renders_ai", exist_ok=True)
style = "Unreal Engine 5 3D CGI render, hard amber sunlight shadows, teal atmosphere, cinematic 8k, vertical 9:16"

for i in range(6):
    beat = lines[i % len(lines)][:130]
    p = urllib.parse.quote(f"{beat}, {style}")
    u = f"https://pollinations.ai{p}?width=1080&height=1920&nologo=true&seed={200+i}"
    out_p = f"renders_ai/ai_{i:02d}.jpg"
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r, open(out_p, "wb") as f:
            f.write(r.read())
        shots.append(out_p)
    except Exception:
        pass

# If OpenToonz .tnz file exists in repo, render 2D OpenToonz frames via tcomposer and include them
if os.path.exists("scene2d.tnz"):
    os.makedirs("renders_2d", exist_ok=True)
    subprocess.run(["xvfb-run", "-a", "tcomposer", os.path.abspath("scene2d.tnz"), "-o", os.path.abspath("renders_2d/2d_.png")], check=False)
    shots += sorted(glob.glob("renders_2d/*.png"))[:4]

shot_dur = total_dur / max(len(shots), 1)
frames_per_shot = int(shot_dur * 30) + 15

with open("captions.vtt") as f:
    vtt = f.read()

red_cues = []
for b in vtt.strip().split("\n\n"):
    lns = b.splitlines()
    if len(lns) >= 3 and "-->" in lns:
        t_start = lns.split("-->").strip()
        p = re.split("[:.]", t_start)
        sec = int(p)*3600 + int(p)*60 + int(p) + int(p)/1000.0
        txt = " ".join(lns[2:])
        nums = re.findall(r'\b(?:\$?\d[\d,.]*\s*(?:million|billion|trillion|ships|carats|years|men|%|CT)?)\b', txt, re.I)
        if nums and len(nums.strip()) >= 2:
            red_cues.append((sec, sec + 2.6, nums.upper().strip()))

inputs, filters = [], []
for idx, img in enumerate(shots):
    inputs += ["-loop", "1", "-t", f"{shot_dur + 0.5:.2f}", "-i", img]
    z = "min(zoom+0.0012,1.22)" if idx % 2 == 0 else "max(1.22-0.0012*on,1.0)"
    filters.append(f"[{idx}:v]scale=2160:3840,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_per_shot}:s=1080x1920:fps=30,setsar=1,format=yuv420p[v{idx}];")

prev = "[v0]"
for idx in range(1, len(shots)):
    off = idx * shot_dur - 0.4
    filters.append(f"{prev}[v{idx}]xfade=transition=fadeblack:duration=0.4:offset={off:.2f}[xf{idx}];")
    prev = f"[xf{idx}]"

title = (topic.upper() if topic else "SEA RAIDERS OF INDIA")[:28].replace(":", "\\:")
fx = [
    f"{prev}vignette=PI/4,eq=contrast=1.12:saturation=1.18",
    "drawbox=x=0:y=1150:w=1080:h=770:color=black@0.48:t=fill",
    f"drawtext=text='{title}':fontcolor=white@0.85:shadowcolor=black:shadowx=3:shadowy=3:fontsize=36:x=(w-text_w)/2:y=85"
]

for st, en, badge in red_cues:
    safe = badge.replace(":", "\\:").replace("'", "")
    fx.append(f"drawtext=text='{safe}':fontcolor=#ff2626:borderw=5:bordercolor=black:shadowcolor=black@0.8:shadowx=6:shadowy=6:fontsize=74:x=(w-text_w)/2:y=1180:enable='between(t,{st:.2f},{en:.2f})'")

fx.append("subtitles=captions.vtt:force_style='Alignment=2,MarginV=125,Fontsize=21,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Shadow=2,Outline=2'[outv]")

inputs += ["-i", "full_audio.m4a"]
subprocess.run([
    "ffmpeg", "-y", *inputs, "-filter_complex", "".join(filters) + ",".join(fx),
    "-map", "[outv]", "-map", f"{len(shots)}:a",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
    "-c:a", "copy", "-shortest", "cgi_studio_final.mp4"


cd ~/cgi-studio

# 1. Fix mathutils import in build_3d.py
sed -i 's/import bpy, math, os/import bpy, math, os\nfrom mathutils import Vector/' build_3d.py
sed -i 's/bpy.mathutils.Vector/Vector/g' build_3d.py

# 2. Fix director.py list indexing bug (lines[1] instead of lines)
cat << 'EOF' > fix_director.py
with open("director.py") as f:
    code = f.read()
code = code.replace('t_start = lns.split("-->").strip()', 't_start = lns[1].split("-->")[0].strip()')
code = code.replace('sec = int(p)*3600 + int(p)*60 + int(p) + int(p)/1000.0', 'sec = int(p[0])*3600 + int(p[1])*60 + int(p[2]) + int(p[3])/1000.0')
code = code.replace('if nums and len(nums.strip()) >= 2:', 'if nums and len(nums[0].strip()) >= 2:')
code = code.replace('nums.upper().strip()', 'nums[0].upper().strip()')
with open("director.py", "w") as f:
    f.write(code)
