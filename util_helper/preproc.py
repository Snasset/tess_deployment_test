import cv2
import numpy as np
import streamlit as st

def get_valid_heights(thresh_img, draw_debug=False, debug_name="output_contour_visual.jpg"):
    contours, _ = cv2.findContours(thresh_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    valid_heights = []
    debug_img = cv2.cvtColor(thresh_img, cv2.COLOR_GRAY2BGR)

    for cnt in contours:
        x, y, w_c, h_c = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        aspect_ratio = w_c / float(h_c + 1e-5)

        if area < 10 or h_c < 5 or h_c > 100:
            continue
        if aspect_ratio > 10:
            continue
        valid_heights.append(h_c)
        if draw_debug:
            cv2.rectangle(debug_img, (x, y), (x + w_c, y + h_c), (0, 255, 0), 1)

    if draw_debug:
        cv2.imwrite(debug_name, debug_img)

    return valid_heights

def resize_img(img, target_char_height=31, draw_debug=False):
    """
    Resize image agar tinggi huruf (karakter) mendekati target_char_height (misal: 26px).
    """
    st.write(f"🖼️ Original size: {img.shape[1]}×{img.shape[0]}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_intensity = np.mean(gray)
    is_dark_bg = mean_intensity < 100
    if is_dark_bg:
        gray = cv2.bitwise_not(gray)

    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.erode(thresh, kernel, iterations=1)

    valid_heights = get_valid_heights(cleaned, draw_debug=draw_debug)

    if valid_heights:
        avg_height = np.mean(valid_heights)
        scale = target_char_height / avg_height
        if scale < 1:
            scale = 1.5
        elif scale > 2:
            return img
        st.write(f"📏 Total karakter terdeteksi: {len(valid_heights)}")
        st.write(f"🎯 Rata-rata tinggi huruf: {avg_height} → Scale: {scale:.2f}")
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    else:
        img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    st.write(f"📐 After resize: {img.shape[1]}×{img.shape[0]}")
    return img

def preproc_img(input_img):
    resized_img = resize_img(input_img, 26)
    alpha = 0.6
    beta = 40
    clahe_clip = 2.0
    tile_grid_size = (8, 8)
    blur_kernel = (3, 3)
    denoise_h = 30
    img = resized_img

    # === GRAYSCALE
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # === BRIGHTNESS & CONTRAST ADJUST
    adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

    # === HIGHLIGHT MASK 
    # mask = cv2.inRange(adjusted, 240, 255)

    # === BLUR
    blurred = cv2.GaussianBlur(adjusted, blur_kernel, 0)

    # === CLAHE
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=tile_grid_size)
    enhanced = clahe.apply(blurred)

    # === DENOISE
    denoised = cv2.fastNlMeansDenoising(enhanced, h=denoise_h)

    # === OTSU THRESHOLDING
    # mean_intensity = np.mean(denoised)
    # if mean_intensity < 127:
    #     denoised = cv2.bitwise_not(denoised)
    #     _, denoised = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    

    # === CONVERT TO RGB
    final_img = cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)
    return final_img

def filter_smooth(input_img, d_values = 10, sigma_a = 150, sigma_b = 75):
    filtered = cv2.bilateralFilter(input_img, d=d_values, sigmaColor=sigma_a, sigmaSpace=sigma_b)
    return filtered