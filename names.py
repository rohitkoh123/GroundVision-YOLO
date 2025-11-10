import os
import re

# ✅ Folder containing all your images
folder_path = "./Dataset"

# ✅ Output text file (saved in the same folder as this script)
output_file = "plant_names.txt"

# Keep only the part before the first '(' — e.g. CapeDaisy(1)(2) → CapeDaisy
pattern = re.compile(r'^[^()]+')

plant_names = set()

for filename in os.listdir(folder_path):
    if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")):
        continue  # Skip non-image files
    name, _ = os.path.splitext(filename)
    match = pattern.match(name)
    if match:
        clean_name = match.group(0).strip()
        plant_names.add(clean_name)

# ✅ Save unique names into a text file
with open(output_file, "w") as f:
    for name in sorted(plant_names):
        f.write(name + "\n")

print(f"✅ Done! Found {len(plant_names)} unique plant names and saved them to {output_file}")
