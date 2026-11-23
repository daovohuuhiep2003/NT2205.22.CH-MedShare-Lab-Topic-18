#!/usr/bin/env bash
# ==============================================================================
# MedShare-Lab (Topic 18 — NT2205.11.CH)
# Script thiết lập môi trường hoàn chỉnh trên Ubuntu (22.04 / 24.04 LTS)
# Bao gồm: System build tools, Docker & Compose, Python 3.12+, venv, thư viện Core,
#          thư viện kiểm thử/benchmark, công cụ mã hóa ổ đĩa (cryptsetup), DB clients.
# ==============================================================================

set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# Màu hiển thị
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Xác định thư mục gốc của repository
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}   MEDSHARE-LAB (TOPIC 18) — UBUNTU ENVIRONMENT SETUP SCRIPT     ${NC}"
echo -e "${BLUE}==================================================================${NC}"
echo -e "${CYAN}Thư mục dự án:${NC} ${REPO_ROOT}"
echo ""

# ------------------------------------------------------------------------------
# 1. Kiểm tra quyền và hệ điều hành
# ------------------------------------------------------------------------------
if [[ "$(uname -s)" != "Linux" ]]; then
    echo -e "${RED}[LỖI] Script này chỉ hỗ trợ hệ điều hành Linux (Ubuntu/Debian)!${NC}"
    exit 1
fi

if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    echo -e "${CYAN}Hệ điều hành phát hiện:${NC} ${NAME} ${VERSION_ID} (${VERSION_CODENAME})"
else
    echo -e "${YELLOW}[CẢNH BÁO] Không tìm thấy /etc/os-release. Đảm bảo bạn đang dùng Ubuntu/Debian.${NC}"
fi

# Hàm thực thi lệnh với sudo nếu không phải root
run_as_root() {
    if [[ $EUID -eq 0 ]]; then
        "$@"
    elif [[ -n "${SUDO_ASKPASS:-}" ]]; then
        sudo -A "$@"
    else
        sudo "$@"
    fi
}

# ------------------------------------------------------------------------------
# 2. Cập nhật hệ thống và cài đặt các gói nền tảng (Build Tools, Compilers, Crypto C libs)
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}--- [Bước 1/6] Cập nhật hệ thống & Cài đặt công cụ biên dịch C/C++ & Thư viện lõi ---${NC}"
run_as_root apt-get update -y

PACKAGES=(
    # Công cụ cơ bản & mạng
    ca-certificates
    curl
    gnupg
    lsb-release
    wget
    git
    jq
    tree
    htop
    # Biên dịch C/C++ và công cụ build cho SEAL / ABE / liboqs
    build-essential
    cmake
    ninja-build
    clang
    g++
    gcc
    make
    pkg-config
    flex
    bison
    libtool
    automake
    autoconf
    # Thư viện native C/C++ cho mật mã
    # Lưu ý: libpbc-dev KHÔNG có trên Ubuntu apt (22.04/24.04). Stanford PBC
    # được biên dịch từ nguồn ở bước riêng bên dưới (giống workers/abe/Dockerfile).
    libssl-dev
    libgmp-dev
    libffi-dev
    # Công cụ tạo ổ đĩa mã hóa ảo cho Baseline B1
    cryptsetup
    cryptsetup-bin
    # Database client phục vụ kiểm thử direct query bypass
    postgresql-client
    # Python 3 và dev headers
    python3
    python3-pip
    python3-venv
    python3-dev
)

echo -e "${YELLOW}Đang cài đặt các packages:${NC} ${PACKAGES[*]}"

INSTALLABLE=()
MISSING_PKGS=()
for pkg in "${PACKAGES[@]}"; do
    if apt-cache show "${pkg}" >/dev/null 2>&1; then
        INSTALLABLE+=("${pkg}")
    else
        MISSING_PKGS+=("${pkg}")
    fi
done

if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}[CẢNH BÁO] Bỏ qua gói không có trên apt:${NC} ${MISSING_PKGS[*]}"
fi

run_as_root apt-get install -y "${INSTALLABLE[@]}"

# ------------------------------------------------------------------------------
# 2b. Python 3.12+ (Ubuntu 22.04 mặc định chỉ có 3.10; dự án yêu cầu 3.12+)
# ------------------------------------------------------------------------------
PYTHON_BIN="python3"
if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="python3.12"
elif apt-cache show python3.12 >/dev/null 2>&1; then
    echo -e "${YELLOW}Cài đặt Python 3.12 từ kho Ubuntu...${NC}"
    run_as_root apt-get install -y python3.12 python3.12-venv python3.12-dev
    PYTHON_BIN="python3.12"
else
    echo -e "${YELLOW}Cài đặt Python 3.12 từ PPA deadsnakes (Ubuntu ${VERSION_ID:-unknown})...${NC}"
    run_as_root apt-get install -y software-properties-common
    if run_as_root add-apt-repository -y ppa:deadsnakes/ppa; then
        run_as_root apt-get update -y
        run_as_root apt-get install -y python3.12 python3.12-venv python3.12-dev
        PYTHON_BIN="python3.12"
    else
        echo -e "${YELLOW}[CẢNH BÁO] Không thêm được deadsnakes PPA. Dùng $(python3 --version) hiện có.${NC}"
    fi
fi
echo -e "${CYAN}Python dùng cho .venv:${NC} $(${PYTHON_BIN} --version 2>&1)"

# ------------------------------------------------------------------------------
# 2c. Stanford PBC (pairing-based crypto) — không có gói libpbc-dev trên Ubuntu
# ------------------------------------------------------------------------------
echo -e "${YELLOW}Kiểm tra / biên dịch Stanford PBC 0.5.14...${NC}"
if ldconfig -p 2>/dev/null | grep -q 'libpbc\.so'; then
    echo -e "${GREEN}[OK] libpbc đã có trên hệ thống.${NC}"
else
    PBC_TMP="$(mktemp -d)"
    if wget -q -O "${PBC_TMP}/pbc-0.5.14.tar.gz" "https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz" \
        || wget -q --no-check-certificate -O "${PBC_TMP}/pbc-0.5.14.tar.gz" "https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz"; then
        tar -xzf "${PBC_TMP}/pbc-0.5.14.tar.gz" -C "${PBC_TMP}"
        if (
            cd "${PBC_TMP}/pbc-0.5.14"
            ./configure
            make -j"$(nproc)"
            run_as_root make install
        ); then
            run_as_root ldconfig
            echo -e "${GREEN}[OK] Đã cài Stanford PBC vào /usr/local.${NC}"
        else
            echo -e "${YELLOW}[CẢNH BÁO] Biên dịch PBC thất bại. ABE worker vẫn build PBC trong Docker.${NC}"
        fi
    else
        echo -e "${YELLOW}[CẢNH BÁO] Không tải được PBC từ crypto.stanford.edu. ABE worker vẫn build PBC trong Docker.${NC}"
    fi
    rm -rf "${PBC_TMP}"
fi

# ------------------------------------------------------------------------------
# 3. Cài đặt Docker Engine & Docker Compose Plugin chính thức
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}--- [Bước 2/6] Kiểm tra & Cài đặt Docker Engine và Docker Compose ---${NC}"

if command -v docker &>/dev/null && docker compose version &>/dev/null; then
    echo -e "${GREEN}[OK] Docker và Docker Compose đã được cài đặt:${NC}"
    docker --version
    docker compose version
else
    echo -e "${YELLOW}Cài đặt Docker Engine từ repository chính thức của Docker...${NC}"
    run_as_root install -m 0755 -d /etc/apt/keyrings
    
    # Tải GPG key chính thức của Docker
    if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
        run_as_root curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        run_as_root chmod a+r /etc/apt/keyrings/docker.asc
    fi

    # Thêm Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
      run_as_root tee /etc/apt/sources.list.d/docker.list > /dev/null

    run_as_root apt-get update -y
    run_as_root apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Khởi động dịch vụ Docker (nếu systemd khả dụng)
    if pidof systemd &>/dev/null; then
        run_as_root systemctl enable docker
        run_as_root systemctl start docker
    fi
    echo -e "${GREEN}[OK] Cài đặt Docker hoàn tất!${NC}"
fi

# Cấp quyền cho user hiện tại chạy docker không cần sudo
CURRENT_USER="${SUDO_USER:-$USER}"
if [[ "${CURRENT_USER}" != "root" ]]; then
    if ! groups "${CURRENT_USER}" | grep -q '\bdocker\b'; then
        echo -e "${YELLOW}Thêm người dùng '${CURRENT_USER}' vào nhóm 'docker'...${NC}"
        run_as_root usermod -aG docker "${CURRENT_USER}"
        echo -e "${CYAN}[LƯU Ý] Bạn cần đăng xuất và đăng nhập lại (hoặc chạy 'newgrp docker') để kích hoạt nhóm docker.${NC}"
    else
        echo -e "${GREEN}[OK] Người dùng '${CURRENT_USER}' đã thuộc nhóm 'docker'.${NC}"
    fi
fi

# ------------------------------------------------------------------------------
# 4. Thiết lập Python Virtual Environment (.venv) cho Core & Tests
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}--- [Bước 3/6] Thiết lập Python Virtual Environment (.venv) ---${NC}"
cd "${REPO_ROOT}"

if [[ ! -d "${REPO_ROOT}/.venv" ]]; then
    echo -e "${YELLOW}Khởi tạo môi trường ảo Python tại ${REPO_ROOT}/.venv...${NC}"
    "${PYTHON_BIN}" -m venv "${REPO_ROOT}/.venv"
else
    echo -e "${GREEN}[OK] Môi trường ảo ${REPO_ROOT}/.venv đã tồn tại.${NC}"
fi

# Kích hoạt venv để cài đặt gói
VENV_PIP="${REPO_ROOT}/.venv/bin/pip"
VENV_PYTHON="${REPO_ROOT}/.venv/bin/python"

echo -e "${YELLOW}Nâng cấp pip, setuptools và wheel...${NC}"
"${VENV_PIP}" install --upgrade pip setuptools wheel

# ------------------------------------------------------------------------------
# 5. Cài đặt các thư viện Python (Core Gateway/Broker, Testing & Benchmarking)
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}--- [Bước 4/6] Cài đặt các thư viện Python theo chuẩn đồ án ---${NC}"

PYTHON_DEPS=(
    # --- Core Security, Gateway & Broker ---
    "cryptography>=43.0.0"
    "fastapi>=0.110.0"
    "uvicorn>=0.29.0"
    "pydantic>=2.7.0"
    "requests>=2.31.0"
    "httpx>=0.27.0"
    # --- CP-ABE Helpers & Compatibility ---
    "pycryptodome>=3.20.0"
    # --- Database Adapters ---
    "psycopg[binary]>=3.1.0"
    "pymongo>=4.7.0"
    # --- Software KMS Client ---
    "hvac>=2.2.0"
    # --- Testing & Adversarial Evaluation ---
    "pytest>=8.0.0"
    "pytest-asyncio>=0.23.0"
    # --- Benchmarking & Workload Harness ---
    "locust>=2.24.0"
    # --- Data Analysis & Visualization (CI 95%, Leakage) ---
    "pandas>=2.2.0"
    "numpy>=1.26.0"
    "matplotlib>=3.8.0"
    "seaborn>=0.13.0"
)

echo -e "${YELLOW}Đang cài đặt các thư viện Python vào .venv:${NC}"
for dep in "${PYTHON_DEPS[@]}"; do
    echo "  - ${dep}"
done

"${VENV_PIP}" install "${PYTHON_DEPS[@]}"

# ------------------------------------------------------------------------------
# 6. Thiết lập mã nguồn tham khảo CP-ABE (daovohuuhiep2003/Project-MMH-CP-ABE)
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}--- [Bước 5/7] Thiết lập mã nguồn tham khảo CP-ABE ---${NC}"
ABE_REF_DIR="${REPO_ROOT}/workers/abe/reference"
mkdir -p "${ABE_REF_DIR}"

if [[ ! -f "${ABE_REF_DIR}/CP-ABE/Include/SerializeAC17.py" ]]; then
    echo -e "${YELLOW}Đang tải mã nguồn tham khảo CP-ABE từ GitHub...${NC}"
    TMP_CLONE_DIR=$(mktemp -d)
    if git clone --depth=1 https://github.com/daovohuuhiep2003/Project-MMH-CP-ABE.git "${TMP_CLONE_DIR}" 2>/dev/null; then
        cp -r "${TMP_CLONE_DIR}/CP-ABE" "${ABE_REF_DIR}/" 2>/dev/null || true
        cp "${TMP_CLONE_DIR}/README.md" "${ABE_REF_DIR}/README_REF.md" 2>/dev/null || true
        rm -rf "${TMP_CLONE_DIR}"
        echo -e "${GREEN}[OK] Đã tải thành công mã nguồn CP-ABE vào ${ABE_REF_DIR}${NC}"
    else
        rm -rf "${TMP_CLONE_DIR}"
        echo -e "${YELLOW}[LƯU Ý] Không thể clone repo trực tiếp (có thể môi trường offline).${NC}"
        echo -e "${CYAN}        Bạn có thể sao chép thủ công các file SerializeAC17.py và CPABE.py vào: ${ABE_REF_DIR}${NC}"
    fi
else
    echo -e "${GREEN}[OK] Mã nguồn tham khảo CP-ABE đã sẵn sàng tại ${ABE_REF_DIR}.${NC}"
fi

# ------------------------------------------------------------------------------
# 7. Khởi tạo cấu trúc thư mục hạ tầng và biến môi trường
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}--- [Bước 6/7] Tạo thư mục runtime hạ tầng và phân quyền ---${NC}"
mkdir -p "${REPO_ROOT}/infra/runtime"
mkdir -p "${REPO_ROOT}/evidence/runs"
mkdir -p "${REPO_ROOT}/benchmarks/results"
mkdir -p "${REPO_ROOT}/analysis/output"

echo -e "${GREEN}[OK] Các thư mục runtime cục bộ đã sẵn sàng.${NC}"

# ------------------------------------------------------------------------------
# 8. Kiểm tra đối soát toàn diện (Sanity Check)
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}--- [Bước 7/7] Kiểm tra sức khỏe môi trường (Sanity Checks) ---${NC}"

# Kiểm tra Python version và import các module cốt lõi
"${VENV_PYTHON}" - <<'EOF'
import importlib
import importlib.metadata
import importlib.util
import sys

print(f"  [+] Python version: {sys.version.split()[0]} ({sys.executable})")

# (import_name, dist_name, description)
# locust.gevent monkey-patches ssl; importing it after cryptography/pymongo
# causes RecursionError on Python 3.12. Verify locust via metadata only.
modules = [
    ("cryptography", "cryptography", "AES-256-GCM & HKDF Core"),
    ("Crypto", "pycryptodome", "PyCryptodome (CP-ABE Helpers)"),
    ("fastapi", "fastapi", "Gateway REST API"),
    ("uvicorn", "uvicorn", "ASGI Server"),
    ("pydantic", "pydantic", "Schema Validation"),
    ("psycopg", "psycopg", "PostgreSQL 16 Client"),
    ("pymongo", "pymongo", "MongoDB 7.0 Client"),
    ("hvac", "hvac", "Vault KMS Client"),
    ("pytest", "pytest", "Testing Harness"),
    ("locust", "locust", "Benchmark Load Generator"),
    ("pandas", "pandas", "Benchmark Data Analysis"),
    ("numpy", "numpy", "Numerical Stats (CI 95%)"),
    ("matplotlib", "matplotlib", "Performance Visualization"),
]

SKIP_IMPORT = {"locust"}

all_ok = True
for mod_name, dist_name, desc in modules:
    try:
        if mod_name not in SKIP_IMPORT:
            mod = importlib.import_module(mod_name)
            ver = getattr(mod, "__version__", None) or importlib.metadata.version(dist_name)
        else:
            if importlib.util.find_spec(mod_name) is None:
                raise ImportError(f"No module named {mod_name}")
            ver = importlib.metadata.version(dist_name)
        print(f"  [+] {mod_name:15} {ver:12} : {desc}")
    except Exception as e:
        print(f"  [!] {mod_name:15} KHÔNG TÌM THẤY! ({e})")
        all_ok = False

if not all_ok:
    sys.exit(1)
EOF

# Kiểm tra Docker
echo -e "\n  [+] Kiểm tra Docker:"
if command -v docker &>/dev/null; then
    docker --version | sed 's/^/      /'
    docker compose version | sed 's/^/      /'
else
    echo -e "      ${RED}[!] Docker chưa được cài đặt đúng.${NC}"
fi

# Kiểm tra Cryptsetup
echo -e "\n  [+] Kiểm tra Cryptsetup (LUKS Baseline B1):"
if command -v cryptsetup &>/dev/null; then
    cryptsetup --version | sed 's/^/      /'
else
    echo -e "      ${RED}[!] Cryptsetup chưa được cài đặt.${NC}"
fi

# Kiểm tra C/C++ Compilers & CMake
echo -e "\n  [+] Kiểm tra C/C++ Build Tools:"
cmake --version | head -n 1 | sed 's/^/      /'
gcc --version | head -n 1 | sed 's/^/      /'
g++ --version | head -n 1 | sed 's/^/      /'

# Kiểm tra Dockerfile của CP-ABE worker
echo -e "\n  [+] Kiểm tra Worker Dockerfiles:"
if [[ -f "${REPO_ROOT}/workers/abe/Dockerfile" ]]; then
    echo -e "      ${GREEN}[OK] workers/abe/Dockerfile đã sẵn sàng (Stanford PBC + Charm).${NC}"
fi

# Chạy thử check_repo.py của dự án
echo -e "\n  [+] Chạy tooling kiểm tra repository hiện tại:"
"${VENV_PYTHON}" -B "${REPO_ROOT}/scripts/check_repo.py" | sed 's/^/      /'

echo ""
echo -e "${GREEN}==================================================================${NC}"
echo -e "${GREEN}   THIẾT LẬP MÔI TRƯỜNG UBUNTU THÀNH CÔNG CHO MEDSHARE-LAB!      ${NC}"
echo -e "${GREEN}==================================================================${NC}"
echo -e "${CYAN}Để bắt đầu làm việc, hãy kích hoạt virtual environment:${NC}"
echo -e "    ${YELLOW}source .venv/bin/activate${NC}"
echo ""
echo -e "${CYAN}Để build các Worker mật mã nâng cao (PQC, HE, ABE), chạy:${NC}"
echo -e "    ${YELLOW}docker build -t medshare-pqc-worker ./workers/pqc${NC}"
echo -e "    ${YELLOW}docker build -t medshare-he-worker ./workers/he${NC}"
echo -e "    ${YELLOW}docker build -t medshare-abe-worker ./workers/abe${NC}"
echo ""
echo -e "${CYAN}Để chạy smoke test kiểm tra Worker CP-ABE vừa build:${NC}"
echo -e "    ${YELLOW}docker run --rm medshare-abe-worker${NC}"
echo ""
