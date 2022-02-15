# vehicles-visual-signals-processing

Project for vehicles signals recognition for Master Degree Paper, Russia, Moscow, MISIS 2021-2022
#### - Python version: 3.9.10
- Annotation tool: [CVAT](https://github.com/openvinotoolkit/cvat)
- Project is active


### DATASETS

- [Baseline dataset.]()

Contains MJPG files with 5 frames each with __ classes: tail-lights (_ items) and break-lights (_ items)

Seqences example(https://github.com/nevertheless-ui/vehicles-visual-signals-processing/blob/main/images/dataset_sequence_example.jpg)


### DATASET COOKBOOK:

To start video chunks from video:
- python dataset_generator.py

Example: [raw_data]()

Extractor description:
1. Default directory for input video files: "data\raw_data" (can be changed in .\utils\constants.py)
2. Natively supported video file format:
- ".TS" with 30 FPS.
- Example: "REC25915.ts"
3. Annotation support type:
- XML (CVAT v.1.1)
- Must be track with 2 points
- Must be placed "as is" in native ZIP archive from CVAT export
- Must be named natively with CVAT export name
- Example: "task_rec25915.ts_cvat for video 1.1.zip"
4. Extracted video chunks are placed in new dataset directory
5. Extractor creates MJPG chunk from each availible track annotation:
- format: "{file}_{label_name}_{class_type}_{class_name}_tr{track_num}_seq{chunk_num}_fr{frame_num}.mjpg"


### HINTS:
1. Creating virtual environment:
- python -m venv .venv

2. Activating virtual environment:
- CMD: .\.venv\Scripts\activate.bat
- PowerShell: .\.venv\Scripts\Activate.ps1
- Linux Terminal: source .venv/bin/activate

3. Installation requirements:
- pip3 install -r requirements.txt

4. [Installation CUDA for Windows](https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html)

5. [Installation PyTorch docs](https://pytorch.org/get-started/locally/)
