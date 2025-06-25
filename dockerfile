# Base image Ubuntu terbaru
FROM ubuntu:22.04

# Set env agar tidak interaktif
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    libsm6 \
    libice6 \
    python3 \
    python3-pip \
    && add-apt-repository -y ppa:alex-p/tesseract-ocr5 \
    && apt-get update && apt-get install -y tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Cek versi Tesseract
RUN tesseract --version

# Set workdir
WORKDIR /app

# Copy semua file
COPY . .

# Install Python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Port untuk Streamlit
EXPOSE 8501

# Jalankan Streamlit
CMD ["sh", "-c", "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"]