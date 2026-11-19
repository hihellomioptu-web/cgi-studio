import sys, re

tnz_file = "scene2d.tnz"
with open(tnz_file, "r") as f:
    xml = f.read()

cmd = sys.argv[1] if len(sys.argv) > 1 else ""

if cmd == "bgcolor" and len(sys.argv) == 5:
    r, g, b = sys.argv[2], sys.argv[3], sys.argv[4]
    xml = re.sub(r'(<bgColor>\s*)\d+\s+\d+\s+\d+\s+\d+(\s*</bgColor>)', rf'\g<1>{r} {g} {b} 255\g<2>', xml)
    print(f"OpenToonz background set to RGB({r}, {g}, {b})")
elif cmd == "frames" and len(sys.argv) == 3:
    frames = sys.argv[2]
    xml = re.sub(r'framecount="\d+"', f'framecount="{frames}"', xml)
    print(f"OpenToonz frame count set to {frames}")
elif cmd == "fps" and len(sys.argv) == 3:
    fps = sys.argv[2]
    xml = re.sub(r'(<fps>\s*)\d+(\s*</fps>)', rf'\g<1>{fps}\g<2>', xml)
    print(f"OpenToonz FPS set to {fps}")
else:
    print("Usage: python3 toonz_control.py [bgcolor R G B | frames N | fps N]")

with open(tnz_file, "w") as f:
    f.write(xml)
