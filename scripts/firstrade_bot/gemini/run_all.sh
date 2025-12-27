#!/bin/zsh
source .env
echo "Run parse using image $IMAGE_PATH"
python parse_image.py
echo "Updateing google sheet"
python update_sheet.py
