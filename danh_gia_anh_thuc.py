"""
KIỂM THỬ TRÊN ẢNH CHỤP THỰC TẾ (nguồn ĐỘC LẬP với hình vẽ chuẩn dùng để sinh dữ liệu huấn luyện).
Hỗ trợ hai nguồn ảnh (dùng được cả hai cùng lúc):
  (1) Ảnh tự chụp/tự cắt: thư mục anh_thuc/<mã biển>/*.jpg   ví dụ anh_thuc/P.102/1.jpg, anh_thuc/W.224/a.png
      - Mỗi ảnh nên chứa MỘT biển, cắt sát quanh biển (giống thao tác khoanh vùng trong ứng dụng).
      - Thư mục tên "khac" (hoặc mã không có trong 340 biển) = biển NGOÀI danh sách, dùng để chọn ngưỡng cảnh báo.
  (2) Bộ dữ liệu ảnh đường phố có khung bao (định dạng YOLO, ví dụ tải từ Roboflow), có tệp data.yaml.
      Chỉ định thư mục bằng THU_MUC_YOLO bên dưới. Lần chạy đầu, chương trình tạo tệp anh_xa_nhan.json để
      bạn ghép TÊN LỚP của bộ dữ liệu với MÃ BIỂN theo QCVN 41:2024 (để null nếu biển không có trong 340 biển).
Kết quả: ket_qua/anh_thuc/ (bao_cao.txt, du_doan.csv, vi_du_sai.png, diem_softmax.png)
Cách dùng:  python danh_gia_anh_thuc.py
"""
import os
import re
import glob
import json
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mlp import MangNoron
from tien_xu_ly import tien_xu_ly, doc_anh

THU_MUC_ANH = "anh_thuc"
THU_MUC_YOLO = next((d for d in ["du_lieu_vn56", os.path.join("..", "luu_tru", "du_lieu_vn56"),
                                  "du_lieu_vn", os.path.join("..", "luu_tru", "du_lieu_vn")] if os.path.isdir(d)), None)
TEP_ANH_XA = "anh_xa_nhan.json"
LE = 0.10          # nới khung bao thêm 10% mỗi phía (giống người dùng khoanh vùng hơi rộng)
KT_TOI_THIEU = 16  # bỏ biển quá nhỏ (< 16 điểm ảnh)
RA = os.path.join("ket_qua", "anh_thuc")
os.makedirs(RA, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "figure.dpi": 150})
TIEN_TO = {"P": 0, "DP": 0, "R": 1, "W": 2, "I": 3, "S": 4}
NHOM = ["Biển báo cấm", "Biển hiệu lệnh", "Biển báo nguy hiểm và cảnh báo", "Biển chỉ dẫn", "Biển phụ"]

lop = json.load(open("lop.json", encoding="utf-8"))
MA = [l["ma"] for l in lop]
CHI_SO = {m: i for i, m in enumerate(MA)}
mang = MangNoron.nap(os.path.join("mo_hinh", "mlp.npz"))
mau = []   # (ảnh BGR, mã thật hoặc None nếu ngoài danh sách, nguồn)


def doan_ma(ten):
    """Đoán mã QCVN từ tên lớp, ví dụ 'P102', 'p.127-50', 'W_224' -> 'P.102', 'P.127-50', 'W.224'."""
    t = ten.strip().replace(" ", "")
    m = re.match(r"^(DP|P|R|W|I|S)[._-]?(\d{3}[a-z]?\d?(?:-\d+)?)$", t, re.I)   # nhận cả P.102, P102, P-102, P_102
    if m:
        ma = f"{m.group(1).upper()}.{m.group(2).lower()}"
        return ma if ma in CHI_SO else None
    return None


def doc_ten_lop(yaml_path):
    txt = open(yaml_path, encoding="utf-8").read()
    try:
        import yaml
        names = yaml.safe_load(txt)["names"]
    except Exception:
        m = re.search(r"names:\s*\[(.*?)\]", txt, re.S)
        names = [x.strip().strip("'\"") for x in m.group(1).split(",")] if m else \
            [v.strip().strip("'\"") for k, v in re.findall(r"^\s*(\d+):\s*(.+)$", txt, re.M)]
    return list(names.values()) if isinstance(names, dict) else list(names)


# ---------- Nguồn (1): ảnh tự chụp ----------
if os.path.isdir(THU_MUC_ANH):
    for thu_muc in sorted(os.listdir(THU_MUC_ANH)):
        for p in glob.glob(os.path.join(THU_MUC_ANH, thu_muc, "*")):
            a = doc_anh(p)
            if a is not None:
                mau.append((a, thu_muc if thu_muc in CHI_SO else None, "tự chụp"))

# ---------- Nguồn (2): bộ dữ liệu YOLO ----------
if THU_MUC_YOLO:
    yaml_path = next(iter(glob.glob(os.path.join(THU_MUC_YOLO, "*.yaml"))), None)
    if yaml_path:
        ten_lop = doc_ten_lop(yaml_path)
        if not os.path.exists(TEP_ANH_XA):
            anh_xa = {t: doan_ma(t) for t in ten_lop}
            json.dump(anh_xa, open(TEP_ANH_XA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            khong = [t for t, m in anh_xa.items() if m is None]
            print(f"Đã tạo {TEP_ANH_XA}: tự ghép được {len(anh_xa) - len(khong)}/{len(anh_xa)} tên lớp với mã biển.")
            if khong:
                print("Chưa ghép được (sẽ coi là biển NGOÀI danh sách 340 biển):", ", ".join(khong))
            print("Hãy mở tệp kiểm tra lại (sửa nếu cần), rồi chạy lại chương trình để đánh giá.")
            raise SystemExit
        anh_xa = json.load(open(TEP_ANH_XA, encoding="utf-8"))
        for anh_p in glob.glob(os.path.join(THU_MUC_YOLO, "*", "images", "*")):
            nhan_p = os.path.join(os.path.dirname(os.path.dirname(anh_p)), "labels", os.path.splitext(os.path.basename(anh_p))[0] + ".txt")
            if not os.path.exists(nhan_p):
                continue
            a = doc_anh(anh_p)
            if a is None:
                continue
            H, W = a.shape[:2]
            for d in open(nhan_p).read().split("\n"):
                d = d.split()
                if len(d) < 5:
                    continue
                k, cx, cy, w, h = int(d[0]), *map(float, d[1:5])
                if k >= len(ten_lop) or (w * W < KT_TOI_THIEU or h * H < KT_TOI_THIEU):
                    continue
                w, h = w * (1 + 2 * LE), h * (1 + 2 * LE)
                x1, y1 = max(0, int((cx - w / 2) * W)), max(0, int((cy - h / 2) * H))
                x2, y2 = min(W, int((cx + w / 2) * W)), min(H, int((cy + h / 2) * H))
                ma = anh_xa.get(ten_lop[k])
                mau.append((a[y1:y2, x1:x2].copy(), ma if ma in CHI_SO else None, "bộ dữ liệu ảnh đường phố"))

if not mau:
    raise SystemExit("Không có ảnh để kiểm thử. Tạo thư mục anh_thuc/<mã biển>/ chứa ảnh chụp, "
                     "hoặc đặt bộ dữ liệu YOLO (có data.yaml) vào thư mục du_lieu_vn56.")

X = np.array([tien_xu_ly(a) for a, _, _ in mau], np.float32)
P = mang.du_doan_xac_suat(X)
du, diem = P.argmax(1), P.max(1)
trong = np.array([m is not None for _, m, _ in mau])
y = np.array([CHI_SO[m] if m else -1 for _, m, _ in mau])
dung = (du == y) & trong
dong = [f"KIỂM THỬ TRÊN ẢNH CHỤP THỰC TẾ (nguồn độc lập với hình vẽ chuẩn)",
        f"Tổng số ảnh biển: {len(mau)} | thuộc 340 biển: {int(trong.sum())} ({len(set(y[trong]))} loại biển) | "
        f"ngoài danh sách: {int((~trong).sum())}",
        f"Nguồn: " + ", ".join(f"{s}: {sum(1 for _, _, x in mau if x == s)} ảnh" for s in sorted({x for _, _, x in mau}))]
if trong.any():
    top5 = (np.argsort(-P[trong], 1)[:, :5] == y[trong][:, None]).any(1).mean()
    dong += ["", f"1. Trên các biển THUỘC danh sách 340 biển:",
             f"   Đúng / tổng          : {int(dung.sum())}/{int(trong.sum())}",
             f"   Độ chính xác top-1   : {dung[trong].mean() * 100:.2f}%",
             f"   Độ chính xác top-5   : {top5 * 100:.2f}%",
             f"   Nhận đúng NHÓM biển  : {(np.array([TIEN_TO.get(MA[i].split('.')[0], 3) for i in du[trong]]) == np.array([TIEN_TO.get(MA[i].split('.')[0], 3) for i in y[trong]])).mean() * 100:.2f}%",
             "", "   Theo nhóm biển:"]
    gy = np.array([TIEN_TO.get(MA[i].split(".")[0], 3) if i >= 0 else -1 for i in y])
    for k, t in enumerate(NHOM):
        mk = trong & (gy == k)
        if mk.any():
            dong.append(f"   {t:32s} {int(dung[mk].sum()):5d}/{int(mk.sum()):<5d} = {dung[mk].mean() * 100:6.2f}%")
    dong += ["", "2. Điểm Softmax lớn nhất (mức tự tin):",
             f"   dự đoán đúng: trung vị {np.median(diem[dung]):.3f}" if dung.any() else "   (không có dự đoán đúng)",
             f"   dự đoán sai : trung vị {np.median(diem[trong & ~dung]):.3f}" if (trong & ~dung).any() else "   (không có dự đoán sai)"]
if (~trong).any():
    dong.append(f"   biển ngoài danh sách: trung vị {np.median(diem[~trong]):.3f}")
dong += ["", f"3. LỰA CHỌN NGƯỠNG CẢNH BÁO",
         f"   {'Ngưỡng':>7s} {'Chấp nhận (biển thuộc DS)':>27s} {'Accuracy khi chấp nhận':>24s} {'Bắt được dự đoán sai':>22s} {'Từ chối biển ngoài DS':>23s}"]
tot = None
for t in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    nhan = diem >= t
    cov = nhan[trong].mean() if trong.any() else float("nan")
    acc = dung[trong & nhan].mean() if (trong & nhan).any() else float("nan")
    bat = (~nhan & trong & ~dung).sum() / max((trong & ~dung).sum(), 1)
    ood = (~nhan[~trong]).mean() if (~trong).any() else float("nan")
    dong.append(f"   {t:7.1f} {cov * 100:26.2f}% {acc * 100:23.2f}% {bat * 100:21.2f}% {ood * 100:22.2f}%")
    diem_can_bang = (0 if np.isnan(acc) else acc) + (0 if np.isnan(bat) else bat) + (0 if np.isnan(ood) else ood)
    if tot is None or diem_can_bang > tot[1]:
        tot = (t, diem_can_bang)
dong.append(f"   => Ngưỡng cân bằng nhất trên ảnh thực tế (tổng accuracy + tỉ lệ bắt lỗi + tỉ lệ từ chối lớn nhất): {tot[0]}")
json.dump({"nguong": tot[0], "nguon": "danh_gia_anh_thuc.py - ảnh chụp thực tế"}, open("nguong_tin_cay.json", "w"))
dong.append("      (đã ghi vào nguong_tin_cay.json, ứng dụng web sẽ dùng ngưỡng này)")

with open(os.path.join(RA, "du_doan.csv"), "w", encoding="utf-8-sig") as f:
    f.write("STT,Nguồn,Mã thật,Dự đoán,Điểm Softmax,Đúng\n")
    for i, (_, m, s) in enumerate(mau):
        f.write(f"{i + 1},{s},{m or 'ngoài danh sách'},{MA[du[i]]},{diem[i]:.3f},{int(dung[i])}\n")
sai = np.where(trong & ~dung)[0][:24]
if len(sai):
    fig, ax = plt.subplots(4, 6, figsize=(13, 9.5))
    for a in ax.ravel():
        a.axis("off")
    for a, i in zip(ax.ravel(), sai):
        a.imshow(cv2.cvtColor(mau[i][0], cv2.COLOR_BGR2RGB))
        a.set_title(f"Thực tế: {mau[i][1]}\nDự đoán: {MA[du[i]]} ({diem[i]:.2f})", fontsize=8, color="#B91C1C")
    plt.tight_layout(); plt.savefig(os.path.join(RA, "vi_du_sai.png"), facecolor="white"); plt.close()
fig, ax = plt.subplots(figsize=(8, 3.5))
for m_, t_, c_ in [(dung, "Đúng", "#0B3D91"), (trong & ~dung, "Sai", "#E03131"), (~trong, "Ngoài danh sách", "#9CA3AF")]:
    if m_.any():
        ax.hist(diem[m_], bins=20, range=(0, 1), alpha=.6, label=f"{t_} ({int(m_.sum())})", color=c_)
ax.set_xlabel("Điểm Softmax lớn nhất"); ax.set_ylabel("Số ảnh"); ax.legend()
plt.tight_layout(); plt.savefig(os.path.join(RA, "diem_softmax.png"), facecolor="white"); plt.close()
open(os.path.join(RA, "bao_cao.txt"), "w", encoding="utf-8").write("\n".join(dong))
print("\n".join(dong)); print(f"\nĐã lưu kết quả vào {RA}/")
