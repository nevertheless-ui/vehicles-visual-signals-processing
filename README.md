# vehicles-visual-signals-processing
![Title](https://github.com/nevertheless-ui/vehicles-visual-signals-processing/blob/main/images/title.jpeg)
Project for vehicles signals recognition for Master Degree Paper, Russia, Moscow, MISIS 2021-2022
#### - Python version: 3.9.10
- Annotation tool: [CVAT](https://github.com/openvinotoolkit/cvat)
- Project is CLOSED

### USAGE

There are 2 types of NN in this repository:
1. CNN for single image classification - train_cnn_model.py
2. LSTM for sequence classification - train_lstm_model.py

HINT: use key -h to check arguments to check parameters of learning

### DATASETS

- [Archive with 3 datasets](https://disk.yandex.ru/d/yyNMBcOJmjEXCA)
1. Single images (854 items)
2. Difference betwen first and last frame (838 items)
3. Sequence of 5 image as AVI files (807 items)

![Example of sequences](https://github.com/nevertheless-ui/vehicles-visual-signals-processing/blob/main/images/dataset_sequence_example.jpg)

### MODEL RESULTS

1. LSTM results
![LSTM](https://github.com/nevertheless-ui/vehicles-visual-signals-processing/blob/main/results/2022-06-08--13-48-20_ep1000_batch30_validBatch30_lr0.01_lrm0.3_optADAM_LSTM10000_patience150.png)
2. CNN with single images
![Singleimages](https://github.com/nevertheless-ui/vehicles-visual-signals-processing/blob/main/results/2022-06-08--14-13-24_ep1000_batch8_validBatch8_lr0.005_lrm0.3_optADAM_LSTM10000_patience100.png)
3. CNN with difference
![Differences](https://github.com/nevertheless-ui/vehicles-visual-signals-processing/blob/main/results/2022-06-08--14-40-56_ep1000_batch8_validBatch8_lr0.0005_lrm0.3_optADAM_LSTM10000_patience100.png)

### DATASET COOKBOOK:

To start video chunks from video:
> usage: dataset_generator.py [-h] [-i INPUT] [-o OUTPUT] [-m {sequence,singleshot}] [--overwrite] [--debug]
>
> optional arguments:
> -h, --help            show this help message and exit
>
> -i INPUT, --input INPUT
>                       Input directory with videos and annotation archive
>
> -o OUTPUT, --output OUTPUT
>                       Output directory for dataset
>
> -m {sequence,singleshot}, --mode {sequence,singleshot}
>                       Dataset generator mode. Sequence for MJPG and singleshot for JPG
>
> --overwrite           Overwrite current dataset directory if exists
>
> --debug               Enable debug log writing

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
