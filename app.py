import os
import platform
import numpy as np
import cv2
from PIL import Image
import streamlit as st
import pytesseract
from ultralytics import YOLO
from util_helper.postproc import ekstrak_nutrisi, konversi_ke_100g, cek_kesehatan_bpom
from util_helper.preproc import resize_img
import subprocess
from paddleocr import PaddleOCR
# import paddleocr
# st.write(f"Versi paddleocr **{paddleocr.__version__}**")
# import pytesseract
import logging

ocr = PaddleOCR(
    rec_model_dir='paddleppocr/best_model_50k/paddlev3_50k/inference',
    det_model_dir='paddleppocr/en_PP-OCRv3_det_infer',
    textline_orientation_model_dir='paddleppocr/ch_ppocr_mobile_v2.0_cls_infer',
    rec_char_dict_path='paddleppocr/en_dict.txt',
    lang='en',
    use_textline_orientation=False
)
logging.basicConfig(level=logging.INFO)


# st.write(f"Versi Pytesseract (wrapper): **{pytesseract.__version__}**")
# st.write(f"testing 1")
# uploaded_file = st.file_uploader("Upload Gambar", type=["jpg", "jpeg", "png"])
# if uploaded_file is not None:
#     image = Image.open(uploaded_file).convert('RGB')
#     st.image(image, caption='Gambar Diupload', use_column_width=True)
#     image_np = np.array(image)

#     result = ocr.ocr(image_np, cls=False)

#     st.subheader("Hasil OCR:")
#     for line in result:
#         for (bbox, text_data) in line:
#             text, conf = text_data
#             st.write(f"📌 {text} (confidence: {conf:.2f})")
# st.write(f"testing 2")



# Load model YOLO
model = YOLO("tabledet_model/best.pt")


st.title("🍽️ Ekstraksi & Evaluasi Nutrisi")

# Step 1: Input Kategori & Takaran
st.subheader("1️⃣ Informasi Produk")
kategori_pilihan = st.selectbox("📦 Pilih Kategori Produk", [
    "Minuman Siap Konsumsi", "Pasta & Mi Instan", "Susu Bubuk Plain", "Susu Bubuk Rasa",
    "Keju", "Yogurt Plain", "Yogurt Rasa", "Serbuk Minuman Sereal", "Oatmeal",
    "Sereal Siap Santap (Flake/Keping)", "Sereal Batang (Bar)", "Granola",
    "Biskuit dan Kukis", "Roti dan Produk Roti", "Kue (Kue Kering dan Lembut)",
    "Puding Siap Santap", "Sambal", "Kecap Manis", "Makanan Ringan Siap Santap"
])

# takaran = st.number_input("📏 Masukkan Takaran Saji (g/ml)", min_value=1.0, step=1.0)

# Step 2: Upload Gambar
st.subheader("2️⃣ Upload Gambar Label Nutrisi")

st.write("Pilih gambar")

uploaded_file = st.file_uploader("📤 Upload Gambar", type=["jpg", "jpeg", "png"], key="upload_gambar")
image_source = uploaded_file

# Step 3: Proses Deteksi Tabel & OCR (hanya jika tombol ditekan)
if image_source and st.button("🔍 Cek Nutrisi"):
    image = Image.open(image_source).convert("RGB")
    st.session_state["image"] = image

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
            crop_bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)

            # Resize dan simpan ke file temp .tif
            resized_img = resize_img(crop_bgr, target_char_height=31)
            temp_path = "processed_tmp.tif"
            Image.fromarray(resized_img).save(temp_path, dpi=(300, 300))

            # Panggil Tesseract via CLI
            with st.spinner("🔍 Menjalankan OCR dengan PaddleOCR..."):
                ocr_result_raw = ocr.ocr(crop_bgr, cls=False)

    # Gabungkan hasil menjadi satu string
                ocr_result = ""
                for line in ocr_result_raw[0]:
                    text = line[1][0]
                    ocr_result += text + "\n"

                st.session_state["crop_image"] = Image.open(temp_path)
                st.session_state["ocr_raw"] = ocr_result
                st.session_state["nutrisi"] = ekstrak_nutrisi(ocr_result)
                os.remove(temp_path)

        else:
            st.error("❌ Tidak ada tabel nutrisi terdeteksi oleh model.")
            st.stop()

# Step 4: Tampilkan OCR & Koreksi User (jika sudah ada hasil)
if "nutrisi" in st.session_state:
    st.subheader("3️⃣ Data Nutrisi")

    st.image(st.session_state["image"], caption="📷 Gambar yang Diunggah", use_column_width=True)
    st.image(st.session_state["crop_image"], caption="🧾 Tabel Nutrisi Terdeteksi", width=350)

    st.markdown("**📄 Hasil OCR yang Dikoreksi:**")
    st.code(st.session_state["ocr_raw"])

    nutrisi_input = {}

    label_nutrisi_fix = [
        "Takaran Saji",
        "Energi",
        "Lemak",
        "Gula",
        "Serat",
        "Garam",
        "Protein",
        "Karbohidrat",
        "Kalsium"
    ]

    with st.form("form_koreksi"):
        st.markdown("Silakan koreksi nilai nutrisi di bawah jika diperlukan:")
        for label in label_nutrisi_fix:
            val = st.session_state["nutrisi"].get(label, "-")
            if label == "Takaran Saji":
                nutrisi_input[label] = st.text_input(
                    f"{label}", value=val, key=f"input_{label}",
                    help="Masukkan angka tanpa satuan (g/ml)"
                )
            else:
                nutrisi_input[label] = st.text_input(f"{label}", value=val, key=f"input_{label}")
        submit = st.form_submit_button("✅ Evaluasi")
        
    if submit:
        try:
            takaran_input = float(nutrisi_input["Takaran Saji"])
        except (ValueError, TypeError):
            st.error("❌ Takaran Saji harus berupa angka.")
            st.stop()
        nutrisi_normalized = konversi_ke_100g(nutrisi_input, takaran_input)
        hasil_evaluasi = cek_kesehatan_bpom(kategori_pilihan, nutrisi_normalized)

        st.subheader("4️⃣ Hasil Evaluasi BPOM")
        for hasil in hasil_evaluasi:
            if "⚠️" in hasil:
                st.warning(hasil)
            elif "✅" in hasil:
                st.success(hasil)
            else:
                st.info(hasil)
