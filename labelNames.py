import os, re, shutil, urllib.parse

# ==== CONFIG ====
base_dir = "./"
labels_dir = os.path.join(base_dir, "labels")   # existing labels folder
output_dir = os.path.join(base_dir, "labels2")  # new folder for cleaned labels

os.makedirs(output_dir, exist_ok=True)

for fname in os.listdir(labels_dir):
    if not fname.lower().endswith(".txt"):
        continue

    # 1️⃣ Decode URL-encoded chars and strip prefix like 7da3c033__
    decoded = urllib.parse.unquote(fname)
    decoded = decoded.split("__")[-1]

    # 2️⃣ Replace both "\" and "/" with "_" temporarily
    decoded = decoded.replace("\\", "_").replace("/", "_")

    # 3️⃣ Remove any leading "Dataset_" (or "Dataset-" etc.)
    decoded = re.sub(r'^Dataset[_\-]+', '', decoded, flags=re.IGNORECASE)

    # 4️⃣ Remove invalid Windows filename chars
    clean_name = re.sub(r'[<>:"/\\|?*]', '_', decoded)

    src = os.path.join(labels_dir, fname)
    dst = os.path.join(output_dir, clean_name)

    shutil.copy2(src, dst)
    print(f"✅ {fname} → {clean_name}")

print("\nAll cleaned label files saved to:", output_dir)
