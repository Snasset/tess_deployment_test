# Gunakan base image Ubuntu yang relatif baru
FROM ubuntu:22.04

# Set environment variable untuk non-interaktif instalasi apt
ENV DEBIAN_FRONTEND=noninteractive

# Update package list dan instal dependensi Tesseract serta library tambahan kamu
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:alex-p/tesseract-ocr && \
    apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ind \
    libgl1 \            
    libglib2.0-0 \     
    python3 \
    python3-pip \
    # Tambahkan juga dependensi OpenCV lain yang umum jika nanti muncul error lain
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    libsm6 \
    libice6 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Cek versi Tesseract untuk verifikasi (akan terlihat di log build)
RUN tesseract --version

# Buat direktori kerja untuk aplikasi Streamlit
WORKDIR /app

# Copy requirements.txt dan install dependensi Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy aplikasi Streamlit dan file lainnya
COPY . .

# Exposed port untuk Streamlit (defaultnya 8501)
EXPOSE 8501

# Perintah untuk menjalankan Streamlit saat container dimulai
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]