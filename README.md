# vehicles-visual-signals-processing
WARNING: This readme is obsolete. Will be updated after code refactoring and adding new features!
Project for vehicles signals recognition for Master Degree Paper, Russia, Moscow, MISIS 2021-2022
#### - Python version: 3.9.10
- Annotation tool: [CVAT](https://github.com/openvinotoolkit/cvat)
- Project is active


### DATASETS

- [Baseline dataset.](https://drive.google.com/file/d/1CFDdmcM0Uq_-6dC8D8aA-VsR2-XPrqdZ/view?usp=sharing)

Contains MJPG files with 60 frames each (2 seconds) with 2 classes: tail-lights (227 items) and break-lights (90 items)


### DATASET COOKBOOK:

To start video chunks from video:
- python .\utils\extractor.py

Example: [raw_data](https://drive.google.com/file/d/1LLeEocagJBVZa4zk1njnUfN_9wyF0KTc/view?usp=sharing)

Extractor description:
1. Default directory for input video files: "data\raw_data"
2. Natively supported video file format:
- .TS with 30 FPS value.
- Example: "REC25915.ts"
3. Annotation support type:
- XML (CVAT v.1.1)
- Must be track with 2 points
- Must be placed "as is" in native ZIP archive from CVAT export
- Must be named natively with CVAT export name
- Example: "task_rec25915.ts-*-cvat for video 1.1.zip"
4. Extracted video chunks are placed in DIR named after video file
- Example: directory name - "REC25915.ts_chunks"
5. Extractor creates MJPG chunk from each availible track annotation (default chunk duration - 2 seconds)
- Example: "REC25915.ts_chunk_X_Y.mjpg" (X - track number, Y = chunk number)


### HINTS:
1. Creating virtual environment:
- python -m venv .venv

2. Activating virtual environment:
- CMD: .\.venv\Scripts\activate.bat
- PowerShell: .\.venv\Scripts\Activate.ps1
- Linux Terminal: source .venv/bin/activate

3. Installing requirements:
- pip3 install -r requirements.txt

4. Installing PyTorch with CUDA11 based on https://pytorch.org/get-started/locally/
- pip3 install torch==1.10.0+cu113 torchvision==0.11.1+cu113 torchaudio===0.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html
