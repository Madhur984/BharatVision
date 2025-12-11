#!/bin/bash
# Helper script to build and run the Docker repro
set -e
IMAGE_NAME=legal-metrology-repro:latest
cd "$(dirname "$0")/.."

docker build -t $IMAGE_NAME -f docker/Dockerfile .

docker run --rm -p 8501:8501 $IMAGE_NAME
