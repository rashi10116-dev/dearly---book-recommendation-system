import os
import re

emoji_pattern = re.compile(
    r'[\U00010000-\U0010ffff]'
    r'|[\u2600-\u27bf]'
    r'|[\u2300-\u23ff]'
    r'|[\u2b50-\u2b55]'
    r'|[\u200d]'
    r'|[\ufe0f]'
)

found = []
for root, _, files in os.walk('frontend/src'):
    for f in files:
        if f.endswith(('.jsx', '.js', '.html', '.css')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                for line_no, line in enumerate(fp, 1):
                    emojis = emoji_pattern.findall(line)
                    if emojis:
                        found.append((path, line_no, line.strip(), emojis))

if found:
    print(f"Found {len(found)} emojis:")
    for p, l, text, em in found:
        print(f" - {p}:{l} -> {em} in '{text[:70]}'")
else:
    print("SUCCESS: EXACTLY ZERO EMOJIS FOUND IN FRONTEND SOURCE CODE!")

