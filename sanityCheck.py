import os
import re
from collections import defaultdict

# ==== CONFIG ====
# Change this path to the folder you want to check (e.g. train/images, val/images, or test/images)
folder_path ="./split/val/images"

# =================

# Regex to extract species name before first '('
pattern = re.compile(r'^([^()]+)')

# Dictionary to hold species → count
species_counts = defaultdict(int)

# File extensions considered as images
image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

# Loop through files
for fname in os.listdir(folder_path):
    if not any(fname.lower().endswith(ext) for ext in image_exts):
        continue

    match = pattern.match(os.path.splitext(fname)[0])
    if match:
        species = match.group(1).strip()
        species_counts[species] += 1
    else:
        print(f"[WARN] Could not parse species from: {fname}")

# Print summary
print("\n=== Image Count Per Species ===")
for species, count in sorted(species_counts.items()):
    img_word = "image" if count == 1 else "images"
    print(f"{species} — {count} {img_word}")

print("\n✅ Sanity check complete!")
