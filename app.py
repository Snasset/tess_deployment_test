import os
import re
import cv2
import streamlit as st
from PIL import Image
import numpy as np
import pytesseract
from ultralytics import YOLO
import platform

# === SETUP ===
os.environ["TESSDATA_PREFIX"] = os.path.abspath("./tessdata/eng_5k_11ki_custom.traineddata")
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

model = YOLO("tabledet_model/best.pt")

st.title("🍽️ YOLOv8 + Custom OCR + Klasifikasi Gizi BPOM")

# ===== Fungsi Ekstra =====
def preprocess_for_ocr(pil_img):
    img_gray = np.array(pil_img.convert("L"))
    _, img_thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    img_clean = cv2.morphologyEx(img_thresh, cv2.MORPH_OPEN, kernel)
    img_resized = cv2.resize(img_clean, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return Image.fromarray(img_resized)

def ekstrak_nutrisi(text):
    nutrisi = {}
    patterns = {
        "Lemak Total": r"lemak total.*?(\d+\.?\d*)\s*g",
        "Gula Total": r"gula total.*?(\d+\.?\d*)\s*g",
        "Serat": r"serat.*?(\d+\.?\d*)\s*g",
        "Garam": r"garam.*?(\d+\.?\d*)\s*mg"
    }
    for k, p in patterns.items():
        match = re.search(p, text, re.I)
        if match:
            nutrisi[k] = float(match.group(1))
    return nutrisi

def klasifikasi_produk(text):
    text = text.lower()
    if "serat" in text and "gula" in text and "lemak" in text:
        return "Sereal Flake (Ready to Eat)"
    elif "garam" in text and "gula" in text and "lemak" in text:
        return "Makanan Ringan Siap Santap"
    elif "kalsium" in text:
        return "Yogurt / Susu Bubuk"
    elif "gula" in text and "ml" in text:
        return "Minuman Siap Konsumsi"
    return "Tidak Diketahui"

def cek_bpom_sereal_flake(nut):
    msg = []
    if nut.get("Lemak Total", 0) > 4:
        msg.append("⚠️ Lemak Total melebihi batas maksimum (4 g/100g)")
    if nut.get("Gula Total", 0) > 20:
        msg.append("⚠️ Gula Total melebihi batas maksimum (20 g/100g)")
    if nut.get("Serat", 0) < 3:
        msg.append("⚠️ Serat kurang dari batas minimum (3 g/100g)")
    return msg

# ===== Streamlit Main =====
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
            crop_pil = preprocess_for_ocr(crop_pil_raw)

            st.image(crop_pil, caption=f"Cropped #{i+1}", width=300)

            # OCR
            text = pytesseract.image_to_string(
                crop_pil,
                lang="eng_5k_11ki_custom+eng+ind",
                config="--oem 1 --psm 6"
            )
            st.markdown(f"**📄 OCR Output #{i+1}:**")
            st.code(text.strip())

            # Klasifikasi + Ekstrak
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
