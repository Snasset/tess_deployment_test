import os
import platform
import numpy as np
import cv2
from PIL import Image
import streamlit as st
import pytesseract
from ultralytics import YOLO

from utils.preproc import preprocess
from utils.postproc import ekstrak_nutrisi, klasifikasi_produk, cek_bpom_sereal_flake

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
        for i, box in enumerate(result.boxes):
            found = True
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            crop = img_np[y1:y2, x1:x2]
            crop_pil_raw = Image.fromarray(crop)
            crop_pil = preprocess(crop_pil_raw)

            st.image(crop_pil, caption=f"Cropped #{i+1}", width=300)

            text = pytesseract.image_to_string(
                crop_pil,
                lang="model_50k_custom",
                config="--oem 1 --psm 6 -c classify_bln_numeric_mode=1 -c tessedit_char_whitelist=0123456789.,%mgG"
            )
            st.markdown(f"**📄 OCR Output #{i+1}:**")
            st.code(text.strip())

            nutrisi = ekstrak_nutrisi(text)
            kategori = klasifikasi_produk(text)
            st.success(f"📦 Kategori Produk: **{kategori}**")

            st.markdown("### 📊 Data Nutrisi:")
            for k, v in nutrisi.items():
                unit = "mg" if k == "Garam" else "g"
                st.write(f"- **{k}**: {v} {unit}")

            if kategori == "Sereal Flake (Ready to Eat)":
                warning = cek_bpom_sereal_flake(nutrisi)
                if warning:
                    st.warning("⚠️ **Peringatan BPOM:**")
                    for w in warning:
                        st.markdown(f"- {w}")
                else:
                    st.success("✅ Semua nilai sesuai dengan batas BPOM.")

    if not found:
        st.warning("❌ Tidak ada bagian tabel nutrisi terdeteksi oleh YOLO.")
