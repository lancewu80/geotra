# GPU access comes from the host's NVIDIA driver via `docker run --gpus`
# / compose `deploy.resources.reservations.devices` (see
# ../DEPLOYMENT.md). The pip-installed torch wheel below bundles its own
# CUDA/cuDNN runtime, so a plain Python base image is enough — no
# nvidia/cuda base image or manual CUDA toolkit install needed.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# install a CUDA-matched torch build first so ultralytics' dependency
# resolution doesn't pull a mismatched or CPU-only wheel afterwards.
# cu121 works with any host driver supporting CUDA >= 12.1 (check with
# `nvidia-smi` on the host); swap the index URL if the driver is older.
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 \
    && pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
