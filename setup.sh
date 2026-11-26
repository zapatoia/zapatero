#!/usr/bin/env bash
# Prepara el entorno de render (Ubuntu/Debian).
set -e
command -v ffmpeg >/dev/null || (apt-get update && apt-get install -y ffmpeg)
apt-get install -y libegl1 libgl1 fonts-inter >/dev/null 2>&1 || (apt-get update && apt-get install -y libegl1 libgl1 fonts-inter)
pip install -r requirements.txt
python3 -c "import skia; print('skia', skia.__version__)"
