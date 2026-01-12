# syntax=docker/dockerfile:1
# FROM python:3.13-slim-bookworm
FROM nvidia/cuda:12.9.1-cudnn-devel-ubuntu20.04

ARG PYTHON_VERSION=3.10

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL="C.UTF-8"
ENV LANG="C.UTF-8"
ENV TZ=Asia/Tokyo

WORKDIR /workspace

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python${PYTHON_VERSION} \
    python3-pip \
    python-is-python3 \
    ca-certificates \
    tzdata \
    curl \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 && \
    update-alternatives --set python3 /usr/bin/python${PYTHON_VERSION}

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install -r /app/requirements.txt

CMD ["/bin/bash"]
