# ==============================================================================
# MedShare-Lab (Topic 18 — NT2205.11.CH)
# Dockerfile cho CP-ABE Worker (workers/abe/)
# Môi trường: Python 3.10 + Stanford PBC 0.5.14 + Charm-Crypto (AC17 / BSW07)
# Môi trường: Ubuntu 22.04 LTS (Python 3.10) + Stanford PBC 0.5.14 + Charm-Crypto (AC17 / BSW07)
# Kế thừa mô hình KEM/DEM và Serialization từ daovohuuhiep2003/Project-MMH-CP-ABE
# ==============================================================================

FROM python:3.10-slim-bullseye
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Cài đặt các thư viện nền tảng và công cụ biên dịch C/C++
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    flex \
    bison \
    libgmp-dev \
    libssl-dev \
    wget \
    git \
    ca-certificates \
    curl \
    python3 \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    && rm -rf /var/lib/apt/lists/*

# 2. Biên dịch và cài đặt Stanford PBC Library (0.5.14)
RUN wget --no-check-certificate https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz \
    && tar -xzf pbc-0.5.14.tar.gz \
    && cd pbc-0.5.14 \
    && ./configure \
    && make -j$(nproc) \
    && make install \
    && ldconfig \
    && cd /app \
    && rm -rf pbc-0.5.14*

# 3. Cài đặt Charm-Crypto từ nguồn chính thức
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir pycryptodome cryptography fastapi uvicorn requests pydantic && \
RUN pip3 install --no-cache-dir pycryptodome cryptography fastapi uvicorn requests pydantic && \
    git clone --depth=1 https://github.com/JHUISI/charm.git /tmp/charm && \
    cd /tmp/charm && \
    ./configure.sh && \
    make -j$(nproc) && \
    make install && \
    rm -rf /tmp/charm

RUN pip3 install --no-cache-dir pyparsing

# 4. Thiết lập thư mục làm việc cho worker service
RUN mkdir -p /app/src /app/reference
COPY . /app/

EXPOSE 9002

# Lệnh mặc định chạy smoke test hoặc khởi động service
CMD ["python", "-c", "from charm.toolbox.pairinggroup import PairingGroup; G = PairingGroup('SS512'); print('[OK] Charm-Crypto & PairingGroup initialized successfully!')"]
CMD ["python3", "smoke_test.py"]

