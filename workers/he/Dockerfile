# ==============================================================================
# MedShare-Lab (Topic 18 — NT2205.11.CH)
# Dockerfile cho Homomorphic Encryption (HE) Worker (workers/he/)
# Thư viện: Microsoft SEAL v4.1.2 (BFV Scheme - Integer Exactness)
# ==============================================================================

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth=1 --branch v4.1.2 https://github.com/microsoft/SEAL.git /tmp/SEAL && \
    cd /tmp/SEAL && \
    cmake -S . -B build -G Ninja -DSEAL_USE_MSGSL=OFF -DSEAL_USE_ZLIB=OFF -DSEAL_USE_ZSTD=OFF && \
    cmake --build build && \
    cmake --install build && \
    rm -rf /tmp/SEAL

COPY . /app/

RUN cmake -S /app -B /app/build -G Ninja && \
    cmake --build /app/build

EXPOSE 9001

CMD ["/app/build/smoke_test"]
