import os
import platform
import numpy as np
import cv2
import subprocess
import shutil
from PIL import Image
import streamlit as st
from ultralytics import YOLO
from paddleocr import PaddleOCR

from util_helper.preproc import resize_img, filter_smooth, preproc_img
from util_helper.postproc import ekstrak_nutrisi, konversi_ke_100g, cek_kesehatan_bpom, postproc_paddle

# === SETUP ===
os.environ["TESSDATA_PREFIX"] = os.path.abspath("./tess_trainneddata")
tessdata_dir = os.path.abspath("./tess_trainneddata")
tesseract_path = shutil.which("tesseract")
if tesseract_path is None:
    st.error("❌ Tesseract tidak ditemukan.")
else:
    try:
        result = subprocess.run([tesseract_path, "--version"], capture_output=True, text=True, check=True)
        st.sidebar.success(f"Tesseract: {result.stdout.splitlines()[0]}")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Cek versi gagal: {e}")

# === LOAD MODEL ===
model = YOLO("tabledet_model/best.pt")
ocr = PaddleOCR(
    rec_model_dir='paddleppocr/infer_ppocrrecv3',
    det_model_dir='paddleppocr/en_PP-OCRv3_det_infer',
    textline_orientation_model_dir='paddleppocr/ch_ppocr_mobile_v2.0_cls_infer',
    rec_char_dict_path='paddleppocr/en_dict.txt',
    lang='en',
    use_textline_orientation=False
)

# === STREAMLIT UI ===
st.title("🍽️ Ekstraksi & Evaluasi Nutrisi")
st.subheader("📤 Upload Gambar Label Nutrisi")
uploaded_file = st.file_uploader("Upload Gambar", type=["jpg", "jpeg", "png"], key="upload_gambar")

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(image)
    st.image(image, caption="📷 Gambar Diupload", use_column_width=True)

    tab_tess, tab_paddle = st.tabs(["🧪 Tesseract OCR", "🧠 PaddleOCR"])

    # === TESSERACT TAB ===
    with tab_tess:
        if st.button("🔍 Jalankan OCR Tesseract"):
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            results = model(img_bgr)

            if results and results[0].boxes is not None:
                box = max(results[0].boxes, key=lambda b: b.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                crop = img_np[y1:y2, x1:x2]
                crop_bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)

                # resized = resize_img(crop_bgr, target_char_height=35)
                # filtered = filter_smooth(resized,1,50,75)
                preproc_img = preproc_img(crop_bgr)
                temp_path = "processed_tmp.tif"
                Image.fromarray(preproc_img).save(temp_path, dpi=(300, 300))

                tess_output_txt = "tess_result"
                cmd = [
                    tesseract_path, temp_path, tess_output_txt,
                    "--tessdata-dir", tessdata_dir,
                    "-l", "ind+model_50k_custom",
                    "--dpi", "300",
                    "--psm", "6",
                    "--oem", "1",
                    "-c", "tessedit_write_images=true",
                    "-c", "tessedit_char_blacklist=\\\"|#$-:*“”/><[]{}()&£"
                ]
                subprocess.run(cmd, check=True)

                if os.path.exists("tessinput.tif"):
                    st.image(Image.open("tessinput.tif"), caption="🖼️ Gambar Preprocessed Tesseract")
                    os.remove("tessinput.tif")

                with open(tess_output_txt + ".txt", "r", encoding="utf-8") as f:
                    ocr_text = f.read()

                st.session_state["crop_image"] = Image.open(temp_path)
                st.session_state["ocr_raw"] = ocr_text
                st.session_state["nutrisi"] = ekstrak_nutrisi(ocr_text)
                st.image(temp_path, caption="📋 Tabel Nutrisi Ter-crop", width=350)
                st.code(ocr_text)
                os.remove(temp_path)
                os.remove(tess_output_txt + ".txt")
            else:
                st.warning("❌ Tabel tidak ditemukan.")

    # === PADDLE TAB ===
    with tab_paddle:
        if st.button("🔍 Jalankan OCR PaddleOCR"):
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            results = model(img_bgr)

            if results and results[0].boxes is not None:
                box = max(results[0].boxes, key=lambda b: b.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                crop = img_np[y1:y2, x1:x2]
                crop_bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)

                # resized = resize_img(crop_bgr, target_char_height=30)
                temp_path = "paddle_tmp.png"
                Image.fromarray(crop_bgr).save(temp_path)

                with st.spinner("🔎 Menjalankan PaddleOCR..."):
                    ocr_raw = ocr.ocr(crop_bgr, cls=False)
                ocr_cleaned = postproc_paddle(ocr_raw)
                text_out = ocr_cleaned
                st.session_state["crop_image"] = Image.open(temp_path)
                st.session_state["ocr_raw"] = text_out
                st.session_state["nutrisi"] = ekstrak_nutrisi(text_out)
                st.image(temp_path, caption="📋 Tabel Nutrisi Ter-crop", width=350)
                st.code(text_out)
                os.remove(temp_path)
            else:
                st.warning("❌ Tabel tidak ditemukan.")

# === EVALUASI ===
if "nutrisi" in st.session_state:
    st.subheader("🧪 Koreksi & Evaluasi Nutrisi")

    kategori_pilihan = st.selectbox("📦 Pilih Kategori Produk", [
        "Minuman Siap Konsumsi", "Pasta & Mi Instan", "Susu Bubuk Plain", "Susu Bubuk Rasa",
        "Keju", "Yogurt Plain", "Yogurt Rasa", "Serbuk Minuman Sereal", "Oatmeal",
        "Sereal Siap Santap (Flake/Keping)", "Sereal Batang (Bar)", "Granola",
        "Biskuit dan Kukis", "Roti dan Produk Roti", "Kue (Kue Kering dan Lembut)",
        "Puding Siap Santap", "Sambal", "Kecap Manis", "Makanan Ringan Siap Santap"
    ])

    st.markdown("**📄 Hasil OCR yang Dikoreksi:**")
    st.code(st.session_state["ocr_raw"])

    label_nutrisi_fix = [
        "Takaran Saji", "Energi", "Lemak", "Gula", "Serat",
        "Garam", "Protein", "Karbohidrat", "Kalsium"
    ]
    nutrisi_input = {}

    with st.form("form_koreksi"):
        for label in label_nutrisi_fix:
            val = st.session_state["nutrisi"].get(label, "-")
            nutrisi_input[label] = st.text_input(f"{label}", value=val, key=f"input_{label}")
        submitted = st.form_submit_button("✅ Evaluasi")

    if submitted:
        try:
            takaran = float(nutrisi_input["Takaran Saji"])
        except:
            st.error("❌ Takaran Saji harus berupa angka.")
            st.stop()

        nutrisi_norm = konversi_ke_100g(nutrisi_input, takaran)
        hasil = cek_kesehatan_bpom(kategori_pilihan, nutrisi_norm)

        st.subheader("📊 Evaluasi Berdasarkan Aturan BPOM")
        for line in hasil:
            if "⚠️" in line:
                st.warning(line)
            elif "✅" in line:
                st.success(line)
            else:
                st.info(line)
