!/bin/bash

docker pull python:3.11-slim
uv sync --extra prod
USE_DOCKER=true TOURNAMENT_INTERVAL=60 \
  uv run gunicorn -w 1 -b 0.0.0.0:5000 --threads 8 app:app