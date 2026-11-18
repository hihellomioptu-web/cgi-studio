import subprocess, re, os

# 1. Generate voiceover + exact word/phrase timestamps
subprocess.run([
    "edge-tts", "--voice", "en-US-ChristopherNeural", "--rate=+8%",
    "--file", "script.txt", "--write-media", "voiceover.mp3",
    "--write-subtitles", "captions.vtt"
], check=True)

# 2. Get exact audio duration
dur_out = subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", "voiceover.mp3"
]).decode().strip()
total_dur = float(dur_out)

# 3. Parse VTT cues to trigger red keyword overlays at the EXACT spoken second
with open("captions.vtt") as f:
    vtt = f.read()

keywords = [
    ("1498", "MAY 1498\n4 SHIPS"),
    ("twenty", "1502\n~20 SHIPS"),
    ("Miri", "THE MIRI\n~400 ABOARD"),
    ("cartaz", "CARTAZ\n1510 → 1961"),
    ("Cochin", "1663 · COCHIN\nCLOTH → SPICES"),
    ("fifty thousand", "1757 PLASSEY\n3,000 vs 50,000"),
    ("seventeen million", "17.7M RUPEES\n(REPORTED)"),
    ("ten million", "1765 DIWANI\n7–10M (EST.)"),
    ("hundred and five", "1849 · AGE 10\n105.6 CT"),
    ("forty-five trillion", "$45 TRILLION\n(CONTESTED)")
]

triggers = []
blocks = vtt.strip().split("\n\n")
for b in blocks:
    lines = b.splitlines()
    if len(lines) >= 3 and "-->" in lines[1]:
        t_str = lines[1].split("-->")[0].strip()
        parts = re.split("[:.]", t_str)
        sec = int(parts[0])*3600 + int(parts[1])*60 + int(parts[2]) + int(parts[3])/1000.0
        text = " ".join(lines[2:])
        for word, badge in keywords:
            if word.lower() in text.lower() and not any(badge == x[1] for x in triggers):
                triggers.append((sec, badge))

# 4. Build stylized Teal & Amber animated background + synced overlays
draw_filters = [
    "geq=r='12+10*sin(2*PI*T/12)':g='42+18*cos(2*PI*T/10)':b='52+22*sin(2*PI*T/8)'",
    "drawbox=x=60:y=280:w=960:h=1180:color=0x0a1f26@0.85:t=fill",
    "drawbox=x=60:y=280:w=960:h=1180:color=0xd98a2b@0.9:t=6",
    "drawtext=text='SEA RAIDERS OF INDIA':fontcolor=white@0.8:fontsize=34:x=(w-text_w)/2:y=95"
]

for i, (start, badge) in enumerate(triggers):
    end = triggers[i+1][0] if i+1 < len(triggers) else total_dur
    for line_idx, line in enumerate(badge.split("\n")):
        safe = line.replace(":", "\\:")
        y_pos = 1120 + (line_idx * 75)
        draw_filters.append(
            f"drawtext=text='{safe}':fontcolor=#ff2e2e:borderw=4:bordercolor=black:"
            f"fontsize=62:x=(w-text_w)/2:y={y_pos}:enable='between(t,{start:.2f},{end:.2f})'"
        )

draw_filters.append(
    "subtitles=captions.vtt:force_style='Alignment=2,MarginV=120,Fontsize=20,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2'"
)

vf = ",".join(draw_filters)
subprocess.run([
    "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x0d2b33:s=1080x1920:r=30:d={total_dur}",
    "-i", "voiceover.mp3", "-vf", vf,
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "sea_raiders_9x16.mp4"
], check=True)
