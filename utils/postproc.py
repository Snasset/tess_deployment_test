import re

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