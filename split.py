import os
import re
import shutil
import random
import math
from collections import defaultdict

# ========= CONFIG =========
SRC_IMAGES = "./Images"   # folder with images
SRC_LABELS = "./labels"    # folder with labels (same stems as images)
OUT_BASE   = "./split"     # output root (will create train/val/test subfolders)

# Desired split counts (total images across all species)
TRAIN_TARGET = 90
VAL_TARGET   = 35
TEST_TARGET  = 20

# Random seed for reproducibility
RNG_SEED = 42

# File extensions considered images
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

# ==========================

random.seed(RNG_SEED)
os.makedirs(OUT_BASE, exist_ok=True)

def ensure_dirs(base):
    for split in ("train", "val", "test"):
        for sub in ("images", "labels"):
            os.makedirs(os.path.join(base, split, sub), exist_ok=True)

def img_stem_and_species(fname):
    """Return (stem, species) where species is text before first '('."""
    stem, ext = os.path.splitext(fname)
    m = re.match(r'^([^()]+)', stem)
    if not m:
        return stem, None
    species = m.group(1).strip()
    return stem, species

# 1) Gather items grouped by species
species_items = defaultdict(list)
total_images = 0
missing_labels = []

for fname in os.listdir(SRC_IMAGES):
    if not any(fname.lower().endswith(ext) for ext in IMG_EXTS):
        continue
    stem, species = img_stem_and_species(fname)
    if not species:
        print(f"[WARN] Could not parse species from filename: {fname}")
        continue

    img_path = os.path.join(SRC_IMAGES, fname)
    lbl_path = os.path.join(SRC_LABELS, stem + ".txt")
    if not os.path.isfile(lbl_path):
        missing_labels.append(fname)
        continue

    species_items[species].append((img_path, lbl_path))
    total_images += 1

if missing_labels:
    print(f"[WARN] {len(missing_labels)} images skipped due to missing labels (showing up to 10):")
    for m in missing_labels[:10]:
        print("   -", m)

if total_images == 0:
    raise SystemExit("No valid image-label pairs found. Check SRC_IMAGES and SRC_LABELS.")

# 2) Shuffle within each species
for sp in species_items:
    random.shuffle(species_items[sp])

species_list = sorted(species_items.keys())
print(f"[INFO] Found {len(species_list)} species and {total_images} total pairs.")

# 3) Compute per-species allocations with min 1 per split (if possible)
ratio_train = TRAIN_TARGET / total_images
ratio_val   = VAL_TARGET   / total_images
ratio_test  = TEST_TARGET  / total_images

allocations = {}  # species -> dict(split->count)
for sp in species_list:
    n = len(species_items[sp])
    if n >= 3:
        # Start with fractional allocation, then ensure min 1 each
        raw = [
            ("train", ratio_train * n),
            ("val",   ratio_val   * n),
            ("test",  ratio_test  * n),
        ]
        # floor and track fractional parts
        floored = {k: int(math.floor(v)) for k, v in raw}
        fracs = sorted(((k, v - floored[k]) for k, v in raw), key=lambda x: x[1], reverse=True)
        base_sum = sum(floored.values())
        # distribute remainder to largest fractional parts
        remainder = n - base_sum
        for i in range(remainder):
            floored[fracs[i % 3][0]] += 1
        # guarantee at least 1 in each split
        for split in ("train", "val", "test"):
            if floored[split] == 0:
                # steal from the largest bucket
                largest = max(("train","val","test"), key=lambda s: floored[s])
                if floored[largest] > 1:
                    floored[largest] -= 1
                    floored[split] += 1
        # Correct any drift
        ssum = sum(floored.values())
        if ssum != n:
            # add/remove to match exactly n
            while ssum < n:
                pick = max(("train","val","test"), key=lambda s: (ratio_train if s=="train" else ratio_val if s=="val" else ratio_test))
                floored[pick] += 1
                ssum += 1
            while ssum > n:
                pick = max(("train","val","test"), key=lambda s: floored[s])
                floored[pick] -= 1
                ssum -= 1
        allocations[sp] = floored
    else:
        # Not enough images to guarantee 1-per-split; round-robin
        counts = {"train": 0, "val": 0, "test": 0}
        order = ["train", "val", "test"]
        for i in range(n):
            counts[order[i % 3]] += 1
        allocations[sp] = counts

# 4) Build splits by species allocation
splits = {"train": [], "val": [], "test": []}
for sp in species_list:
    items = species_items[sp]
    idx = 0
    for split in ("train", "val", "test"):
        take = allocations[sp][split]
        splits[split].extend(items[idx:idx+take])
        idx += take

def count_species_per_split(splits):
    res = {k: defaultdict(int) for k in splits}
    for split in splits:
        for img_path, _ in splits[split]:
            stem = os.path.splitext(os.path.basename(img_path))[0]
            m = re.match(r'^([^()]+)', stem)
            sp = m.group(1).strip() if m else "UNKNOWN"
            res[split][sp] += 1
    return res

def totals(splits):
    return {k: len(splits[k]) for k in splits}

# 5) Balance totals to match exact targets while preserving at least 1 per species per split (when possible)
target = {"train": TRAIN_TARGET, "val": VAL_TARGET, "test": TEST_TARGET}
current = totals(splits)
print(f"[INFO] Initial totals -> train={current['train']}, val={current['val']}, test={current['test']}")

def move_one(src_split, dst_split):
    """Move one item from src->dst without breaking species-min-1 in src."""
    if not splits[src_split]:
        return False
    species_counts = count_species_per_split(splits)[src_split]
    # Prefer moving from species with >1 items in src
    for i, (img_path, lbl_path) in enumerate(list(splits[src_split])):
        stem = os.path.splitext(os.path.basename(img_path))[0]
        sp = re.match(r'^([^()]+)', stem).group(1).strip()
        if species_counts[sp] > 1:
            # move it
            item = splits[src_split].pop(i)
            splits[dst_split].append(item)
            return True
    # If impossible without breaking min-1, allow move as last resort
    if splits[src_split]:
        item = splits[src_split].pop()
        splits[dst_split].append(item)
        return True
    return False

# Try to meet exact targets
changed = True
iter_guard = 0
while changed and iter_guard < 2000:
    iter_guard += 1
    changed = False
    current = totals(splits)
    # if all match, stop
    if all(current[k] == target[k] for k in ("train", "val", "test")):
        break
    # find which splits are over / under
    over = [k for k in ("train","val","test") if current[k] > target[k]]
    under = [k for k in ("train","val","test") if current[k] < target[k]]
    if not over or not under:
        break
    # move from a largest-over to a largest-under
    src = max(over, key=lambda k: current[k] - target[k])
    dst = max(under, key=lambda k: target[k] - current[k])
    if move_one(src, dst):
        changed = True

current = totals(splits)
print(f"[INFO] Final totals   -> train={current['train']}, val={current['val']}, test={current['test']}")

# 6) Check species coverage: each split should have at least one of each species (if that species has >=3 images)
coverage = count_species_per_split(splits)
problems = []
for split in ("train","val","test"):
    missing = [sp for sp in species_list if coverage[split].get(sp, 0) == 0 and len(species_items[sp]) >= 3]
    if missing:
        problems.append((split, missing))

if problems:
    print("[WARN] Some splits are missing species (likely because certain species have too few images or exact-count constraints).")
    for split, miss in problems:
        print(f"   {split} missing: {', '.join(miss)}")
else:
    print("[INFO] All splits contain every species (for species with ≥ 3 images).")

# 7) Write files
ensure_dirs(OUT_BASE)

def copy_pair(item, dst_split):
    img_path, lbl_path = item
    img_name = os.path.basename(img_path)
    lbl_name = os.path.basename(lbl_path)
    shutil.copy2(img_path, os.path.join(OUT_BASE, dst_split, "images", img_name))
    shutil.copy2(lbl_path, os.path.join(OUT_BASE, dst_split, "labels", lbl_name))

for split in ("train", "val", "test"):
    for item in splits[split]:
        copy_pair(item, split)

print("[DONE] Copied files to:")
print(f"   {os.path.join(OUT_BASE,'train','images')} / labels")
print(f"   {os.path.join(OUT_BASE,'val','images')}   / labels")
print(f"   {os.path.join(OUT_BASE,'test','images')}  / labels")
