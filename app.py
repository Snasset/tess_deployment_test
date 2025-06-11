import os
import platform
import numpy as np
import cv2
from PIL import Image
import streamlit as st
import pytesseract
from ultralytics import YOLO

from utils.preproc import preprocess
from utils.postproc import ekstrak_nutrisi, konversi_ke_100g, cek_kesehatan_bpom, koreksi_teks

# SETUP
os.environ["TESSDATA_PREFIX"] = os.path.abspath("./tess_trainneddata")
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

model = YOLO("tabledet_model/best.pt")

st.title("🍽️ Ekstraksi & Evaluasi Nutrisi")

# Main
st.subheader("1️⃣ Informasi Produk")

kategori_pilihan = st.selectbox("📦 Pilih Kategori Produk", [
    "Minuman Siap Konsumsi",
    "Pasta & Mi Instan",
    "Susu Bubuk Plain",
    "Susu Bubuk Rasa",
    "Keju",
    "Yogurt Plain",
    "Yogurt Rasa",
    "Serbuk Minuman Sereal",
    "Oatmeal",
    "Sereal Siap Santap (Flake/Keping)",
    "Sereal Batang (Bar)",
    "Granola",
    "Biskuit dan Kukis",
    "Roti dan Produk Roti",
    "Kue (Kue Kering dan Lembut)",
    "Puding Siap Santap",
    "Sambal",
    "Kecap Manis",
    "Makanan Ringan Siap Santap"
])

takaran = st.number_input("📏 Masukkan Takaran Saji (g/ml)", min_value=1.0, step=1.0)


st.subheader("2️⃣ Upload Gambar Label Nutrisi")
uploaded_file = st.file_uploader("📤 Upload Gambar", type=["jpg", "png", "jpeg"])


if uploaded_file and st.button("🔍 Cek Nutrisi"):
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="📷 Gambar yang Diunggah", use_column_width=True)

    img_np = np.array(image)
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    results = model(img_bgr)
    found = False

    for result in results:
        if result.boxes is not None and len(result.boxes) > 0:
            best_box = max(result.boxes, key=lambda b: b.conf[0])
            found = True

            x1, y1, x2, y2 = map(int, best_box.xyxy[0])
            crop = img_np[y1:y2, x1:x2]
            crop_pil_raw = Image.fromarray(crop)
            crop_pil = preprocess(crop_pil_raw)

            st.image(crop_pil, caption="🧾 Tabel Nutrisi Terdeteksi", width=350)

            text = pytesseract.image_to_string(
                crop_pil,
                lang="model_50k_custom",
                config="--oem 1 --psm 6"
            )
            text_koreksi = koreksi_teks(text)
            

            st.markdown("**📄 OCR Output:**")
            st.code(text_koreksi.strip())

            nutrisi = ekstrak_nutrisi(text_koreksi)

            st.markdown("### 📊 Data Nutrisi Terdeteksi:")
            for k, v in nutrisi.items():
                st.write(f"- **{k}**: {v}")

            nutrisi_normalized = konversi_ke_100g(nutrisi, takaran)

            hasil_evaluasi = cek_kesehatan_bpom(kategori_pilihan, nutrisi_normalized)

            st.markdown("### ✅ Evaluasi BPOM:")
            for hasil in hasil_evaluasi:
                if "⚠️" in hasil:
                    st.warning(hasil)
                elif "✅" in hasil:
                    st.success(hasil)
                else:
                    st.info(hasil)

        else:
            st.error("Tidak ada tabel nutrisi terdeteksi oleh model.")
