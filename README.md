# GroundVision-YOLO
Ground-level plant detection using YOLOv11 — detecting plants from 0–20 cm above soil for precision agriculture.


This repository contains the research, dataset preparation pipeline, and YOLOv11-based experiments developed for a postgraduate applied project at Unitec Institute of Technology. The goal is to detect and identify plants from ground-level images (0–20 cm above soil) using a custom dataset of 16 plant species.

The work focuses on evaluating the effect of different data augmentation strategies (geometric and photometric) on model performance, with metrics such as mAP@50, precision, and recall. The repository includes scripts for dataset structuring, annotation validation, YOLO training experiments (exp_baseline, exp_geo_mild, exp_geo_stronger, exp_color_heavy), and result visualizations.

Future development aims to expand the dataset with additional species and enable real-time inference on Android devices through ONNX or TensorFlow Lite conversion.

GroundVision-YOLO/
│
├── datasetCustom.yaml # YOLO dataset configuration
├── split.py # Dataset splitting script (train/val/test)
├── sanityCheck.py # Sanity check for image-label consistency
├── plant_names_extractor.py # Extracts unique plant species from filenames
├── main.ipynb #Google Colab file
│
├── /split/ # Final dataset (train, val, test)
│ ├── /train/images
│ ├── /train/labels
│ ├── /val/images
│ ├── /val/labels
│ ├── /test/images
│ └── /test/labels
│
├── /runs/ # YOLO experiment output folder
│ ├── exp_baseline/
│ ├── exp_geo_mild/
│ ├── exp_geo_stronger/
│ └── exp_color_heavy/
│
└── README.md
