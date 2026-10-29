"""
TỔNG HỢP KHẢO SÁT TRẢI NGHIỆM NGƯỜI HỌC (bảng hỏi Google Forms, xuất ra tệp CSV).
Quy ước đặt tên câu hỏi trong Google Forms (thang 1 = Rất không đồng ý ... 5 = Rất đồng ý):
  [S1] ... [S10]  10 câu thang đo khả dụng SUS (System Usability Scale)
  [H1] ... [Hn]   các câu về hiệu quả học tập
  Các câu khác (câu hỏi mở, thông tin người trả lời) được bỏ qua khi tính điểm.
Cách dùng:  Google Forms -> Câu trả lời -> Tải xuống (.csv) -> lưu thành khao_sat.csv cạnh tệp này
            python tong_hop_khao_sat.py
Kết quả: ket_qua/khao_sat.txt và ket_qua/khao_sat.png
"""
import os
import re
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TEP = "khao_sat.csv"
if not os.path.exists(TEP):      # khảo sát làm ngay trong ứng dụng (tab "Đánh giá & góp ý")
    import du_lieu_hoc_tap as dl
    TEP = os.path.join(dl.THU_MUC, "khao_sat.csv")
if not os.path.exists(TEP) or os.path.getsize(TEP) == 0:
    raise SystemExit("Chưa có dữ liệu khảo sát: cho người học làm khảo sát ở tab \"Đánh giá & góp ý\" của ứng dụng, "
                     "hoặc tải câu trả lời Google Forms (.csv) và lưu với tên khao_sat.csv.")
hang = list(csv.reader(open(TEP, encoding="utf-8-sig")))
tieu_de, du_lieu = hang[0], hang[1:]
cot = {}
for j, t in enumerate(tieu_de):
    m = re.match(r"\s*\[(S|H)(\d+)\]\s*(.*)", t)
    if m:
        cot[(m.group(1), int(m.group(2)))] = (j, m.group(3).strip())


def diem(v):
    m = re.match(r"\s*(\d)", v or "")
    return int(m.group(1)) if m else np.nan


n = len(du_lieu)
dong = [f"KHẢO SÁT TRẢI NGHIỆM NGƯỜI HỌC – số người trả lời: {n}", ""]
# ---- SUS ----
s_cols = sorted(k for k in cot if k[0] == "S")
if len(s_cols) == 10:
    sus = []
    for r in du_lieu:
        x = [diem(r[cot[k][0]]) for k in s_cols]
        if not any(np.isnan(x)):
            # câu lẻ: điểm - 1; câu chẵn: 5 - điểm; tổng × 2,5 -> thang 0-100
            sus.append(sum((v - 1) if i % 2 == 0 else (5 - v) for i, v in enumerate(x)) * 2.5)
    sus = np.array(sus)
    muc = "xuất sắc" if sus.mean() >= 80.3 else "tốt" if sus.mean() >= 68 else "trung bình" if sus.mean() >= 51 else "kém"
    dong += [f"1. Điểm khả dụng SUS (thang 0–100, trung bình chuẩn = 68): trung bình {sus.mean():.1f}, "
             f"độ lệch chuẩn {sus.std(ddof=1) if len(sus) > 1 else 0:.1f}, thấp nhất {sus.min():.1f}, cao nhất {sus.max():.1f} "
             f"(n = {len(sus)}) -> mức {muc}", ""]
else:
    dong += [f"1. Không đủ 10 câu SUS (tìm thấy {len(s_cols)} câu đánh dấu [S1]...[S10]).", ""]
# ---- Từng câu ----
dong.append(f"2. Kết quả từng câu (thang 1–5)")
dong.append(f"   {'Câu':5s} {'TB':>5s} {'ĐLC':>5s} {'% đồng ý (4–5)':>15s}  Nội dung")
nhan, tb = [], []
for k in sorted(cot):
    j, noi_dung = cot[k]
    x = np.array([diem(r[j]) for r in du_lieu], float); x = x[~np.isnan(x)]
    if not len(x):
        continue
    dong.append(f"   {k[0]}{k[1]:<4d} {x.mean():5.2f} {x.std(ddof=1) if len(x) > 1 else 0:5.2f} {(x >= 4).mean() * 100:14.0f}%  {noi_dung}")
    if k[0] == "H":
        nhan.append(f"H{k[1]}"); tb.append(x.mean())
os.makedirs("ket_qua", exist_ok=True)
open(os.path.join("ket_qua", "khao_sat.txt"), "w", encoding="utf-8").write("\n".join(dong))
print("\n".join(dong))
if tb:
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.barh(nhan[::-1], tb[::-1], color="#0A58A8"); ax.set_xlim(1, 5); ax.set_xlabel("Điểm trung bình (1–5)")
    for i, v in enumerate(tb[::-1]):
        ax.text(v + .05, i, f"{v:.2f}", va="center")
    plt.tight_layout(); plt.savefig(os.path.join("ket_qua", "khao_sat.png"), dpi=150, facecolor="white")
    print("Đã lưu ket_qua/khao_sat.txt và ket_qua/khao_sat.png")
