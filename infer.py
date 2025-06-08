import os
import cv2
from PIL import Image
import pytesseract
from ultralytics import YOLO

# === SETUP ===

# Path ke custom traineddata Tesseract
os.environ["TESSDATA_PREFIX"] = "E:/Skripsi/tess_deployment/tessdata"  # atau tempat file .traineddata kamu
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load YOLOv8 custom model
model = YOLO("tabledet_model/best.pt")  # ganti dengan model deteksimu

# Path gambar yang ingin diolah
image_path = "testimages/cropped_img_indo.jpg"

# Load gambar
image_bgr = cv2.imread(image_path)
image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

# === YOLO INFERENCE ===

results = model(image_rgb)

# Ambil bounding boxes
for result in results:
    for i, box in enumerate(result.boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0])  # koordinat bbox
        crop = image_rgb[y1:y2, x1:x2]  # crop bagian deteksi

        # Konversi ke PIL agar bisa dipakai oleh pytesseract
        crop_pil = Image.fromarray(crop)

        # OCR pakai Tesseract custom model
        text = pytesseract.image_to_string(
            crop_pil,
            lang="eng_5k_11ki_custom",
            config="--oem 1 --psm 6"
        )

        print(f"[{i+1}] OCR Result:\n{text.strip()}\n{'-'*40}")