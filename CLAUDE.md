# OpenToonz + Claude Direct Control
You are connected directly to OpenToonz (`scene2d.tnz`).
To modify the OpenToonz 2D animation scene, run these exact commands via Bash:
- Change 2D background color: `python3 toonz_control.py bgcolor R G B` (e.g., `python3 toonz_control.py bgcolor 200 80 10`)
- Change 2D animation length: `python3 toonz_control.py frames 48`
- Change 2D frame rate: `python3 toonz_control.py fps 24`
- Render & push to GitHub OpenToonz cloud runner: `git add scene2d.tnz toonz_control.py && git commit -m "Update OpenToonz scene" && git push`
