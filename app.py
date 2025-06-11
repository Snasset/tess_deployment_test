import os
import platform
import numpy as np
import cv2
from PIL import Image
import streamlit as st
import pytesseract
from ultralytics import YOLO

from utils.preproc import preprocess
from utils.postproc import ekstrak_nutrisi, konversi_ke_100g, cek_kesehatan_bpom

# === SETUP ===
os.environ["TESSDATA_PREFIX"] = os.path.abspath("./tess_trainneddata")
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

model = YOLO("tabledet_model/best.pt")

st.title("Ekstraksi Nutrisi")

uploaded_file = st.file_uploader("📤 Upload Gambar Label Nutrisi", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
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
            st.markdown("**📄 OCR Output:**")
            st.code(text.strip())

            nutrisi = ekstrak_nutrisi(text)

            st.markdown("### 📊 Data Nutrisi:")
            for k, v in nutrisi.items():
                st.write(f"- **{k}**: {v}")
                
        else:
            st.warning("❌ Tidak ada bagian tabel nutrisi terdeteksi oleh YOLO.")
    kategori_pilihan = st.selectbox(" Pilih Kategori Produk", [
    "Sereal Flake (Ready to Eat)",
    "Sereal Batang (Ready to Eat)",
    "Minuman Siap Konsumsi",
    "Yogurt Plain",
    "Yogurt Berperisa",
    "Susu Bubuk Plain",
    "Granola",
    "Olahan Kacang Berlapis",
    "Pasta/Mie Instan",
    "Biskuit & Kukis",
    "Makanan Ringan Siap Santap"
        ])     
    takaran = st.number_input("📏 Masukkan Takaran Saji (g/ml)", min_value=1.0, step=1.0)
    nutrisi_normalized = konversi_ke_100g(nutrisi, takaran)

    # Evaluasi kesesuaian dengan BPOM
    peringatan = cek_kesehatan_bpom(kategori_pilihan, nutrisi_normalized)

    if peringatan:
        st.warning("⚠️ **Peringatan:**")
        for w in peringatan:
            st.markdown(f"- {w}")
    else:
        st.success("✅ Semua nilai sesuai dengan batas BPOM.")
