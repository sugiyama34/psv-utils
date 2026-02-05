# psv-utils
Utilities related to PackedSfenValue format

# how to use with Docker

Build docker image

```bash
./docker/docker_build.sh
```

Run container

```bash
./docker/docker_run.sh --name rescore --gpus all
```

Run rescore code in the container

```bash
python rescore_with_dlshogi.py <PATH_TO_INPUT> <PATH_TO_OUTPUT> --model-path <MODEL_PATH> --batch-size 4096 --score-scaling 1200.0 --blend-ratio 1.0 --enable-cuda --enable-tensorrt
```

# Download & Upload files between Google Drive

After building a docker image, run container with specifying port

```bash
./docker/docker_run.sh --name download --port 8765
```

Download:

```bash
python3 google_drive_utils/download_from_drive.py --port 8765 --out-dir <OUTPUT_DIRECTORY> --file-id <GOOGLE_DRIVEs_FILE_ID>
```

Then, follow the instructions given in your terminal.
(e.g. auth, login, etc.)

Upload:

```bash
python3 google_drive_utils/upload_into_drive.py --port 8765 --file <YOUR_FILE_PATH> --folder-id <GOOGLE_DRIVE_FOLDER_ID>
```

Then, follow the instructions given in your terminal.
(e.g. auth, login, etc.)
