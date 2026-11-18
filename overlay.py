overlays = [
    (0, 3, "MAY 1498 · 4 SHIPS"),
    (6, 13, "1502 · ~20 SHIPS"),
    (13, 21, "THE MIRI · ~400 ABOARD"),
    (21, 29, "CARTAZ · 1510 → 1961"),
    (29, 37, "1663 · COCHIN · CLOTH → SPICES"),
    (37, 46, "1757 PLASSEY · 3,000 vs 50,000"),
    (46, 58, "17.7M RUPEES (REPORTED)"),
    (58, 71, "1765 DIWANI · 7–10 MILLION (EST.)"),
    (71, 83, "1849 · AGE 10 · 105.6 CT"),
    (83, 95, "$45 TRILLION (CONTESTED)")
]

filters = [
    "drawtext=text='SEA RAIDERS OF INDIA':fontcolor=white@0.75:fontsize=34:x=(w-text_w)/2:y=90"
]

for start, end, label in overlays:
    safe_text = label.replace(":", "\\:")
    filters.append(
        f"drawtext=text='{safe_text}':fontcolor=#ff2a2a:borderw=4:bordercolor=black:"
        f"fontsize=68:x=(w-text_w)/2:y=h-420:enable='between(t,{start},{end})'"
    )

print(",".join(filters))
