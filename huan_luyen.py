"""
Huấn luyện mạng nơron, vẽ biểu đồ và đánh giá (dùng cho Chương 4 của báo cáo).
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
from mlp import MangNoron
from tien_xu_ly import tang_cuong

# ---- Tham số (có thể thay đổi để thử nghiệm và so sánh trong báo cáo) ----
LOP_AN = [512, 256]
DROPOUT = 0.3
TANG_CUONG_DU_LIEU = True
SO_EPOCH = 100
BATCH = 64
TOC_DO_HOC = 0.01
GIAM_LR = 0.97      # sau mỗi epoch, tốc độ học nhân với hệ số này
L2 = 5e-4           # hệ số chính quy hóa L2 (chống quá khớp khi dữ liệu ít)
# Cân bằng dữ liệu: mỗi epoch, loại nhiều ảnh chỉ lấy ngẫu nhiên tối đa TOI_DA ảnh,
# loại ít ảnh được lặp lại (kết hợp tăng cường dữ liệu) cho đủ TOI_THIEU ảnh.
CAN_BANG = True
TOI_DA_MOI_LOP = 600
TOI_THIEU_MOI_LOP = 200

os.makedirs("mo_hinh", exist_ok=True)
os.makedirs("ket_qua", exist_ok=True)

d = np.load("data/du_lieu.npz")
X, y, X_test, y_test = d["X_train"], d["y_train"], d["X_test"], d["y_test"]

# Tách 10% dữ liệu huấn luyện làm tập kiểm định (validation)
rng = np.random.default_rng(1)
val_idx, tr_idx = [], []
for lop in np.unique(y):  # lấy 10% mỗi loại làm tập kiểm định
    i = rng.permutation(np.where(y == lop)[0])
    k = max(1, int(round(0.1 * len(i))))
    val_idx.extend(i[:k]); tr_idx.extend(i[k:])
X_val, y_val = X[val_idx], y[val_idx]
X_tr, y_tr = X[tr_idx], y[tr_idx]

so_lop = int(max(y.max(), y_test.max())) + 1
kien_truc = [X.shape[1]] + LOP_AN + [so_lop]
print("Kiến trúc mạng:", kien_truc)

mang = MangNoron(kien_truc, ti_le_dropout=DROPOUT)
def chon_mau_can_bang():
    chi_so = []
    for lop in np.unique(y_tr):
        i = np.where(y_tr == lop)[0]
        if len(i) > TOI_DA_MOI_LOP:
            i = rng.choice(i, TOI_DA_MOI_LOP, replace=False)
        elif len(i) < TOI_THIEU_MOI_LOP:
            i = rng.choice(i, TOI_THIEU_MOI_LOP, replace=True)
        chi_so.extend(i)
    return np.array(chi_so)


lich_su = mang.huan_luyen(X_tr, y_tr, X_val, y_val, SO_EPOCH, BATCH, TOC_DO_HOC,
                          l2=L2, giam_lr=GIAM_LR,
                          tang_cuong=tang_cuong if TANG_CUONG_DU_LIEU else None,
                          chon_mau=chon_mau_can_bang if CAN_BANG else None)
mang.luu("mo_hinh/mlp.npz")

# ---- Biểu đồ quá trình huấn luyện ----
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].plot(lich_su["loss"]); ax[0].set_title("Hàm mất mát"); ax[0].set_xlabel("Epoch")
ax[1].plot(lich_su["acc_train"], label="Huấn luyện")
ax[1].plot(lich_su["acc_val"], label="Kiểm định")
ax[1].set_title("Độ chính xác"); ax[1].set_xlabel("Epoch"); ax[1].legend()
plt.tight_layout(); plt.savefig("ket_qua/bieu_do_huan_luyen.png", dpi=150)

# ---- Đánh giá trên tập kiểm thử ----
y_du_doan = mang.du_doan(X_test)
acc = float((y_du_doan == y_test).mean())
print(f"\nĐộ chính xác trên tập kiểm thử: {acc:.4f}")

cm = confusion_matrix(y_test, y_du_doan)
plt.figure(figsize=(10, 9))
plt.imshow(cm, cmap="Blues"); plt.colorbar()
plt.title("Ma trận nhầm lẫn"); plt.xlabel("Dự đoán"); plt.ylabel("Thực tế")
plt.tight_layout(); plt.savefig("ket_qua/ma_tran_nham_lan.png", dpi=150)

with open("ket_qua/bao_cao_danh_gia.txt", "w", encoding="utf-8") as f:
    f.write(f"Kiến trúc: {kien_truc}\nEpoch: {SO_EPOCH}, batch: {BATCH}, lr: {TOC_DO_HOC}, "
            f"dropout: {DROPOUT}, L2: {L2}, tăng cường dữ liệu: {TANG_CUONG_DU_LIEU}, ảnh màu LAB, cân bằng dữ liệu: {CAN_BANG}\n")
    f.write(f"Độ chính xác tập kiểm thử: {acc:.4f}\n\n")
    f.write(classification_report(y_test, y_du_doan, digits=4, zero_division=0))
with open("ket_qua/lich_su.json", "w") as f:
    json.dump(lich_su, f)
print("Đã lưu mô hình vào mo_hinh/ và biểu đồ, báo cáo vào ket_qua/")
