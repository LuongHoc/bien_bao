"""
Ghép tên, nhóm, đặc điểm, ý nghĩa (theo MÃ BIỂN, trong y_nghia_bien_bao.json)
với số thứ tự lớp của mạng nơron (trong lop.json) -> tạo bien_bao.json cho ứng dụng.
Cách dùng:  python ghep_y_nghia.py
"""
import json

lop = json.load(open("lop.json", encoding="utf-8"))
y_nghia = json.load(open("y_nghia_bien_bao.json", encoding="utf-8"))
bien_bao, thieu = {}, []
for l in lop:
    if l["ma"] in y_nghia:
        bien_bao[str(l["id"])] = y_nghia[l["ma"]]
    else:
        thieu.append(l["ma"])
        bien_bao[str(l["id"])] = {"ten": f"{l['ma']} - (cần bổ sung tên)", "nhom": "(cần bổ sung)",
                                  "dac_diem": "(cần bổ sung)", "y_nghia": "(cần bổ sung)"}
with open("bien_bao.json", "w", encoding="utf-8") as f:
    json.dump(bien_bao, f, ensure_ascii=False, indent=2)
print(f"Đã tạo bien_bao.json cho {len(lop)} biển.")
print("Thiếu mô tả:", ", ".join(thieu) if thieu else "không có")
