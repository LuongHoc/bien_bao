"""
ĐÁNH GIÁ CHI TIẾT MÔ HÌNH TRÊN TẬP KIỂM THỬ ẢNH TỔNG HỢP (sinh từ hình vẽ chuẩn).
LƯU Ý PHẠM VI: ảnh kiểm thử được sinh từ CÙNG hình chuẩn gốc với ảnh huấn luyện (chỉ khác biến đổi ngẫu nhiên),
nên kết quả ở đây đo khả năng nhận dạng biển chuẩn dưới các biến đổi, KHÔNG thay thế đánh giá trên ảnh chụp
thực tế (xem danh_gia_anh_thuc.py).
Kết quả lưu trong ket_qua/:
  danh_gia_chi_tiet.txt      số đúng/tổng, accuracy, top-5, macro-P/R/F1, theo nhóm, ma trận nhầm lẫn theo nhóm,
                             phân tích điểm Softmax (độ tự tin) và ngưỡng cảnh báo
  lop_f1_thap.csv            các biển có F1 < 0,9 và biển hay bị nhầm thành
  bieu_do_diem_softmax.png   phân bố điểm Softmax của dự đoán đúng / sai
  vi_du_nhan_dang_sai.png    ví dụ ảnh bị nhận dạng sai
  nguong_tin_cay.json        ngưỡng cảnh báo đề xuất (ứng dụng web tự đọc)
Cách dùng:  python danh_gia.py
"""
import os
import json
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix
from mlp import MangNoron

RA = "ket_qua"
os.makedirs(RA, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "figure.dpi": 150})
NHOM = ["Biển báo cấm", "Biển hiệu lệnh", "Biển báo nguy hiểm và cảnh báo", "Biển chỉ dẫn", "Biển phụ"]
TIEN_TO = {"P": 0, "DP": 0, "R": 1, "W": 2, "I": 3, "S": 4}
dong = []


def ghi(s=""):
    print(s)
    dong.append(s)


lop = json.load(open("lop.json", encoding="utf-8"))
MA = [l["ma"] for l in lop]
y_nghia = json.load(open("y_nghia_bien_bao.json", encoding="utf-8")) if os.path.exists("y_nghia_bien_bao.json") else {}
TEN = lambda m: y_nghia.get(m, {}).get("ten", m).split(" - ", 1)[-1]
NHOM_LOP = np.array([TIEN_TO.get(m.split(".")[0], 3) for m in MA])

d = np.load(os.path.join("data", "du_lieu.npz"))
X, y = d["X_test"], d["y_test"]
mang = MangNoron.nap(os.path.join("mo_hinh", "mlp.npz"))
P = np.concatenate([mang.du_doan_xac_suat(X[i:i + 2048]) for i in range(0, len(X), 2048)])
du = P.argmax(1)
diem = P.max(1)
dung = du == y
n = len(y)

ghi("ĐÁNH GIÁ TRÊN TẬP KIỂM THỬ ẢNH TỔNG HỢP (sinh từ hình vẽ chuẩn, cùng nguồn hình với tập huấn luyện)")
ghi(f"Số lớp: {len(MA)} | Số ảnh kiểm thử: {n} ({n // len(MA)} ảnh/lớp)")
ghi(f"\n1. KẾT QUẢ TỔNG THỂ")
ghi(f"   Số dự đoán đúng / tổng số ảnh : {int(dung.sum())}/{n}")
ghi(f"   Độ chính xác (accuracy)        : {dung.mean() * 100:.2f}%")
top5 = (np.argsort(-P, axis=1)[:, :5] == y[:, None]).any(1).mean()
ghi(f"   Độ chính xác top-5             : {top5 * 100:.2f}%")
p, r, f, _ = precision_recall_fscore_support(y, du, average="macro", zero_division=0)
ghi(f"   Macro-Precision / Recall / F1  : {p:.4f} / {r:.4f} / {f:.4f}")
pc, rc, fc, sc = precision_recall_fscore_support(y, du, labels=range(len(MA)), zero_division=0)

ghi(f"\n2. KẾT QUẢ THEO NHÓM BIỂN")
ghi(f"   {'Nhóm':32s} {'Số lớp':>6s} {'Đúng/Tổng':>12s} {'Accuracy':>9s} {'Macro-F1':>9s} {'Số lớp F1<0,9':>14s}")
for k, ten in enumerate(NHOM):
    lk = np.where(NHOM_LOP == k)[0]
    mk = np.isin(y, lk)
    if not mk.any():
        continue
    ghi(f"   {ten:32s} {len(lk):6d} {int(dung[mk].sum()):>5d}/{int(mk.sum()):<6d} {dung[mk].mean() * 100:8.2f}% "
        f"{fc[lk].mean():9.4f} {int((fc[lk] < 0.9).sum()):14d}")

ghi(f"\n3. MA TRẬN NHẦM LẪN THEO NHÓM (số ảnh; hàng = nhóm thực tế, cột = nhóm dự đoán)")
gt, gp = NHOM_LOP[y], NHOM_LOP[du]
cmg = confusion_matrix(gt, gp, labels=range(5))
ghi("   " + " " * 10 + "".join(f"{t:>10s}" for t in ["Cấm", "Hiệu lệnh", "Cảnh báo", "Chỉ dẫn", "Phụ"]))
for k, t in enumerate(["Cấm", "Hiệu lệnh", "Cảnh báo", "Chỉ dẫn", "Phụ"]):
    ghi(f"   {t:10s}" + "".join(f"{v:10d}" for v in cmg[k]))
cm = confusion_matrix(y, du, labels=range(len(MA)))
np.savetxt(os.path.join(RA, "ma_tran_nham_lan_day_du.csv"), cm, fmt="%d", delimiter=",")

ghi(f"\n4. CÁC BIỂN CÓ F1 < 0,9 (sắp xếp theo F1 tăng dần)")
yeu = [i for i in np.argsort(fc) if fc[i] < 0.9]
with open(os.path.join(RA, "lop_f1_thap.csv"), "w", encoding="utf-8-sig") as fo:
    fo.write("STT,Ký hiệu,Tên biển,Nhóm,Precision,Recall,F1,Hay bị nhầm thành,Số ảnh nhầm\n")
    ghi(f"   {'STT':>3s} {'Ký hiệu':10s} {'P':>6s} {'R':>6s} {'F1':>6s}  Hay bị nhầm thành")
    for k, i in enumerate(yeu, 1):
        hang = cm[i].copy(); hang[i] = 0
        j = int(hang.argmax())
        nham = f"{MA[j]} ({hang[j]} ảnh)" if hang[j] else "-"
        ghi(f"   {k:3d} {MA[i]:10s} {pc[i]:6.2f} {rc[i]:6.2f} {fc[i]:6.2f}  {nham}")
        fo.write(f'{k},{MA[i]},"{TEN(MA[i])}",{NHOM[NHOM_LOP[i]]},{pc[i]:.2f},{rc[i]:.2f},{fc[i]:.2f},'
                 f'{MA[j] if hang[j] else ""},{hang[j] if hang[j] else 0}\n')
ghi(f"   => {len(yeu)}/{len(MA)} lớp có F1 < 0,9; {int((fc >= 0.99).sum())} lớp có F1 ≥ 0,99")

ghi(f"\n5. PHÂN TÍCH ĐIỂM SOFTMAX (giá trị lớn nhất của lớp ra - mức tự tin của mô hình, CHƯA phải xác suất đã hiệu chuẩn)")
ghi(f"   Dự đoán đúng: trung vị {np.median(diem[dung]):.3f}, trung bình {diem[dung].mean():.3f}")
if (~dung).any():
    ghi(f"   Dự đoán sai : trung vị {np.median(diem[~dung]):.3f}, trung bình {diem[~dung].mean():.3f}")
bins = np.linspace(0, 1, 11)
ece = sum(abs(diem[(diem > a) & (diem <= b)].mean() - dung[(diem > a) & (diem <= b)].mean()) * ((diem > a) & (diem <= b)).mean()
          for a, b in zip(bins[:-1], bins[1:]) if ((diem > a) & (diem <= b)).any())
ghi(f"   Sai số hiệu chuẩn kỳ vọng (ECE, 10 khoảng): {ece:.4f}")
ghi(f"\n   {'Ngưỡng':>7s} {'Tỉ lệ ảnh được chấp nhận':>25s} {'Accuracy trên ảnh chấp nhận':>28s} {'Tỉ lệ dự đoán sai bị cảnh báo':>30s}")
bang_nguong = []
for t in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    nhan = diem >= t
    acc_t = dung[nhan].mean() if nhan.any() else float("nan")
    bat_loi = (~nhan & ~dung).sum() / max((~dung).sum(), 1)
    bang_nguong.append((t, nhan.mean(), acc_t, bat_loi))
    ghi(f"   {t:7.1f} {nhan.mean() * 100:24.2f}% {acc_t * 100:27.2f}% {bat_loi * 100:29.2f}%")
# Ngưỡng đề xuất: nhỏ nhất sao cho accuracy trên ảnh được chấp nhận >= 99%, nếu không có thì 0,5
de_xuat = next((t for t, cov, a, _ in bang_nguong if a >= 0.99), 0.5)
json.dump({"nguong": de_xuat, "nguon": "danh_gia.py - tập ảnh tổng hợp"}, open("nguong_tin_cay.json", "w"))
ghi(f"   => Ngưỡng cảnh báo đề xuất (nhỏ nhất đạt accuracy ≥ 99% trên ảnh được chấp nhận): {de_xuat}")
ghi("      Cần xác nhận lại ngưỡng trên ảnh chụp thực tế bằng danh_gia_anh_thuc.py.")

fig, ax = plt.subplots(figsize=(8, 3.6))
ax.hist(diem[dung], bins=40, range=(0, 1), alpha=.75, label=f"Dự đoán đúng ({int(dung.sum())})", color="#0B3D91")
ax.hist(diem[~dung], bins=40, range=(0, 1), alpha=.85, label=f"Dự đoán sai ({int((~dung).sum())})", color="#E03131")
ax.set_yscale("log"); ax.set_xlabel("Điểm Softmax lớn nhất"); ax.set_ylabel("Số ảnh (thang log)")
ax.axvline(de_xuat, color="#F5B800", ls="--", label=f"Ngưỡng đề xuất {de_xuat}"); ax.legend()
plt.tight_layout(); plt.savefig(os.path.join(RA, "bieu_do_diem_softmax.png"), facecolor="white"); plt.close()

# 6. Kiểm tra trên 340 hình chuẩn (chính là ảnh hiển thị trong Thư viện của ứng dụng)
from tien_xu_ly import tien_xu_ly, doc_anh
chuan = [tien_xu_ly(doc_anh(os.path.join("anh_mau", f"{i:03d}_0.png"))) for i in range(len(MA))]
dc = mang.du_doan(np.array(chuan))
ghi(f"\n6. NHẬN DẠNG 340 HÌNH CHUẨN TRONG THƯ VIỆN: đúng {int((dc == np.arange(len(MA))).sum())}/{len(MA)}")
sai_chuan = [f"{MA[i]}→{MA[dc[i]]}" for i in range(len(MA)) if dc[i] != i]
if sai_chuan:
    ghi("   Nhận dạng sai: " + ", ".join(sai_chuan))

# 7. Ví dụ ảnh nhận dạng sai (sinh lại đúng ảnh kiểm thử bằng cùng hạt giống ngẫu nhiên như tao_du_lieu.py)
try:
    import tao_du_lieu as tdl
    ds = json.load(open(os.path.join("bien_chuan", "danh_sach.json"), encoding="utf-8"))
    tep = {x["ma"]: x["tep"] for x in ds}
    so_moi_lop = n // len(MA)
    loi = np.where(~dung)[0]
    chon = loi[np.argsort(-diem[loi])][:12] if len(loi) else []
    if len(chon):
        nen = tdl.nap_anh_nen()
        fig, ax = plt.subplots(2, 6, figsize=(14, 5.4))
        for a in ax.ravel():
            a.axis("off")
        for a, idx in zip(ax.ravel(), chon):
            i, k = int(y[idx]), int(idx % so_moi_lop)
            rng = np.random.default_rng(900000 + i)
            goc = tdl.doc_anh_rgba(os.path.join("bien_chuan", tep[MA[i]]))
            for _ in range(k + 1):
                anh = tdl.tao_mau(goc, rng, nen)
            a.imshow(cv2.cvtColor(anh, cv2.COLOR_BGR2RGB))
            a.set_title(f"Thực tế: {MA[i]}\nDự đoán: {MA[du[idx]]} ({diem[idx]:.2f})", fontsize=9, color="#B91C1C")
        plt.tight_layout(); plt.savefig(os.path.join(RA, "vi_du_nhan_dang_sai.png"), facecolor="white"); plt.close()
except Exception as e:
    print("  (bỏ qua hình ví dụ nhận dạng sai:", e, ")")

open(os.path.join(RA, "danh_gia_chi_tiet.txt"), "w", encoding="utf-8").write("\n".join(dong))
print(f"\nĐã lưu kết quả vào thư mục {RA}/")
