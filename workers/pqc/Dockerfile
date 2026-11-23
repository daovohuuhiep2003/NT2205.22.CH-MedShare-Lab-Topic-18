# ==============================================================================
# MedShare-Lab (Topic 18 — NT2205.11.CH)
# Dockerfile cho Post-Quantum Cryptography (PQC) Worker (workers/pqc/)
# Chuẩn triển khai: FIPS 203 (ML-KEM-768) & FIPS 204 (ML-DSA-65)
# Thư viện: Open Quantum Safe (liboqs C + oqs-python)
# ==============================================================================

FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Cài đặt các công cụ biên dịch và thư viện native
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    git \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Biên dịch và cài đặt liboqs C library
RUN git clone --depth=1 --branch main https://github.com/open-quantum-safe/liboqs.git /tmp/liboqs && \
    cd /tmp/liboqs && \
    mkdir build && cd build && \
    cmake -GNinja -DCMAKE_INSTALL_PREFIX=/usr/local -DBUILD_SHARED_LIBS=ON .. && \
    ninja install && \
    ldconfig && \
    rm -rf /tmp/liboqs

# 3. Cài đặt oqs-python wrapper
RUN git clone --depth=1 --branch main https://github.com/open-quantum-safe/liboqs-python.git /tmp/liboqs-python && \
    cd /tmp/liboqs-python && \
    pip install --no-cache-dir . && \
    rm -rf /tmp/liboqs-python

# 4. Cài đặt các gói phụ trợ
RUN pip install --no-cache-dir cryptography pydantic fastapi uvicorn requests

COPY . /app/

EXPOSE 9003

CMD ["python", "smoke_test.py"]
