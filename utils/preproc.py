import os
import cv2
import numpy as np
from PIL import Image

def preprocess(img_pil):
    img = np.array(img_pil.convert("RGB"), dtype=np.uint8)

    # 1. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # 2. Adjust brightness and contrast
    alpha = 0.6
    beta = 50
    adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

    # 3. Highlight suppression
    mask_highlight = cv2.inRange(adjusted, 240, 255)
    highlight_blur = cv2.GaussianBlur(adjusted, (5, 5), 0)
    adjusted_highlight = adjusted.copy()
    adjusted_highlight[mask_highlight > 0] = highlight_blur[mask_highlight > 0]

    # 4. CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(adjusted_highlight)

    # 5. Denoising
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10, templateWindowSize=7, searchWindowSize=21)

    # 6. Convert to RGB
    result_rgb = cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)

    return Image.fromarray(result_rgb)