import re

def ekstrak_nutrisi(text):
    nutrisi = {}
    cleaned_text = text.lower().replace(",", ".") 

    targets = {
        "Lemak": [r"lemak(?: total)?"],
        "Gula": [r"gula(?: total)?"],
        "Serat": [r"serat(?: total)?"],
        "Garam": [r"garam(?: total)?"],
        "Protein": [r"protein(?: total)?"],
        "Karbohidrat": [r"karbohidrat(?: total)?"],
        "Kalsium": [r"kalsium(?: total)?"]
    }

    for label, patterns in targets.items():
        for pattern in patterns:
            match = re.search(rf"{pattern}.*?(\d+\.?\d*)\s*(g|mg|ml)", cleaned_text, re.DOTALL)
            if match:
                val = float(match.group(1))
                unit = match.group(2)
                nutrisi[label] = f"{val} {unit}"
                break 

    return nutrisi

def konversi_ke_100g(nutrisi_dict, takaran_saji):
    hasil = {}
    for nutrien, val_unit in nutrisi_dict.items():
        try:
            angka, satuan = val_unit.split()
            angka = float(angka)

            if satuan.lower() in ["g", "mg", "ml"]:
                if satuan == "mg":
                    angka = angka / 1000 

                per_100g = (angka / takaran_saji) * 100
                hasil[nutrien] = f"{round(per_100g, 2)} g"
        except Exception:
            continue 
    return hasil

def cek_kesehatan_bpom(kategori, nutrisi_dict):
    batas_bpom = {
        "Sereal Flake (Ready to Eat)": {
            "Lemak": {"max": 4.0},
            "Gula": {"max": 20.0},
            "Serat": {"min": 3.0}
        },
        "Granola": {
            "Lemak": {"max": 9.0},
            "Gula": {"max": 25.0},
            "Serat": {"min": 3.0}
        },
        "Sereal Batang (Ready to Eat)": {
            "Lemak": {"max": 10.0},
            "Gula": {"max": 20.0},
            "Serat": {"min": 3.0}
        },
        "Makanan Ringan Siap Santap": {
            "Lemak": {"max": 20.0},
            "Garam": {"max": 400.0}
        },
        "Minuman Siap Konsumsi": {
            "Gula": {"max": 6.0}
        },
        "Pasta/Mie Instan": {
            "Lemak": {"max": 20.0},
            "Garam": {"max": 900.0}
        },
        "Yogurt Plain": {
            "Lemak": {"max": 3.0},
            "Gula": {"max": 5.0}
        },
        "Yogurt Berperisa": {
            "Lemak": {"max": 3.0},
            "Gula": {"max": 10.0}
        },
        "Susu Bubuk Plain": {
            "Gula": {"max": 12.5}
        },
        "Olahan Kacang Berlapis": {
            "Lemak": {"max": 40.0},
            "Garam": {"max": 250.0}
        },
        "Biskuit & Kukis": {
            "Lemak": {"max": 20.0},
            "Gula": {"max": 20.0},
            "Garam": {"max": 300.0},
            "Serat": {"min": 3.0}
        }
    }

    hasil = {}

    if kategori not in batas_bpom:
        return {"info": "Kategori tidak ditemukan dalam referensi BPOM"}

    batas = batas_bpom[kategori]

    for nutrien, batasan in batas.items():
        if nutrien not in nutrisi_dict:
            continue  

        val_unit = nutrisi_dict[nutrien]
        val = float(val_unit.split()[0]) 

        result = {"value": val}
        if "max" in batasan:
            limit = batasan["max"]
            result["limit"] = limit
            result["selisih"] = round(val - limit, 2)
            result["status"] = "✅" if val <= limit else "⚠️"
        elif "min" in batasan:
            limit = batasan["min"]
            result["limit"] = limit
            result["selisih"] = round(val - limit, 2)
            result["status"] = "✅" if val >= limit else "⚠️"

        hasil[nutrien] = result

    return hasil