# Gunakan base image Ubuntu yang relatif baru
FROM ubuntu:22.04

# Set environment variable untuk non-interaktif instalasi apt
ENV DEBIAN_FRONTEND=noninteractive

# Update package list dan instal dependensi Tesseract
# Tambahkan PPA untuk Tesseract 5 (ini adalah PPA yang populer untuk versi terbaru)
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:alex-p/tesseract-ocr && \
    apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    # tesseract-ocr-ind \ # Hapus komentar jika perlu bahasa Indonesia
    python3 \
    python3-pip \
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