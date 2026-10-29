"""
THỰC NGHIỆM ĐỐI CHỨNG (ablation) CHO CÁC LỰA CHỌN TIỀN XỬ LÝ.
Mọi phương án dùng CÙNG tập lớp (340 biển), CÙNG ảnh huấn luyện/kiểm thử, CÙNG kiến trúc và tham số huấn luyện;
chỉ khác bước tiền xử lý -> so sánh được ảnh hưởng riêng của từng lựa chọn:
  V1  LAB + CLAHE, a,b chuẩn hóa hệ số cố định (−128)/25      <- phương án của đề tài
  V2  LAB, KHÔNG CLAHE (chỉ chuẩn hóa kênh L theo từng ảnh)
  V3  LAB + CLAHE, a,b chuẩn hóa Z-score theo TỪNG ẢNH
  V4  LAB + CLAHE, a,b chuẩn hóa hệ số cố định (−128)/128
  V5  Ảnh xám + CLAHE (1.024 đầu vào)
  V6  RGB chia 255 (không cân bằng sáng)
Ảnh kiểm thử được đánh giá ở 4 điều kiện: bình thường, tối (thiếu sáng), chói/tương phản thấp, chiếu sáng không đều.
Để chạy nhanh, dùng cấu hình RÚT GỌN: 50 ảnh huấn luyện + 20 ảnh kiểm thử mỗi lớp, 25 epoch.
Cách dùng:  python thuc_nghiem_doi_chung.py   (khoảng 15-40 phút tùy máy)
Kết quả: ket_qua/thuc_nghiem_doi_chung.txt, .csv, .png
"""
import os
import json
import time
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tao_du_lieu as tdl
from mlp import MangNoron

N_TR, N_TE, SO_EPOCH = 50, 20, 25
RA = "ket_qua"
os.makedirs(RA, exist_ok=True)
_clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))


# ---------- Bốn điều kiện chiếu sáng của ảnh kiểm thử (áp dụng trên ảnh 96×96 trước khi thu nhỏ) ----------
def dk_toi(a):
    return np.clip((a.astype(np.float32) / 255) ** 1.8 * 255 * 0.55, 0, 255).astype(np.uint8)


def dk_choi(a):
    return np.clip((a.astype(np.float32) - 128) * 0.45 + 128 + 70, 0, 255).astype(np.uint8)


def dk_khong_deu(a):
    h, w = a.shape[:2]
    g = np.linspace(0.25, 1.25, w)[None, :, None]
    return np.clip(a.astype(np.float32) * g, 0, 255).astype(np.uint8)


DIEU_KIEN = {"Bình thường": lambda a: a, "Tối": dk_toi, "Chói, tương phản thấp": dk_choi,
             "Chiếu sáng không đều": dk_khong_deu}


# ---------- Các phương án tiền xử lý (đầu vào: ảnh BGR 32×32) ----------
def lab(a):
    return cv2.split(cv2.cvtColor(a, cv2.COLOR_BGR2LAB))


def zs(x):
    x = x.astype(np.float32)
    return (x - x.mean()) / (x.std() + 1e-6)


def v1(a):
    L, A, B = lab(a)
    return np.dstack([zs(_clahe.apply(L)), (A - 128.0) / 25, (B - 128.0) / 25]).astype(np.float32)


def v2(a):
    L, A, B = lab(a)
    return np.dstack([zs(L), (A - 128.0) / 25, (B - 128.0) / 25]).astype(np.float32)


def v3(a):
    L, A, B = lab(a)
    return np.dstack([zs(_clahe.apply(L)), zs(A), zs(B)]).astype(np.float32)


def v4(a):
    L, A, B = lab(a)
    return np.dstack([zs(_clahe.apply(L)), (A - 128.0) / 128, (B - 128.0) / 128]).astype(np.float32)


def v5(a):
    return zs(_clahe.apply(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)))[:, :, None]


def v6(a):
    return (a[:, :, ::-1].astype(np.float32) / 255)


PHUONG_AN = {"V1 LAB + CLAHE, a,b/25 (đề tài)": v1, "V2 LAB không CLAHE": v2, "V3 LAB + CLAHE, a,b Z-score từng ảnh": v3,
             "V4 LAB + CLAHE, a,b/128": v4, "V5 Ảnh xám + CLAHE": v5, "V6 RGB/255": v6}


def tang_cuong(Xb, so_kenh):
    ra = np.empty_like(Xb)
    for i, x in enumerate(Xb):
        anh = x.reshape(32, 32, so_kenh)
        M = cv2.getRotationMatrix2D((16, 16), np.random.uniform(-12, 12), np.random.uniform(0.85, 1.15))
        M[:, 2] += np.random.uniform(-2, 2, size=2)
        ra[i] = cv2.warpAffine(anh, M, (32, 32), borderMode=cv2.BORDER_REPLICATE).reshape(-1)
    return ra


def main():
    ds = json.load(open(os.path.join("bien_chuan", "danh_sach.json"), encoding="utf-8"))
    nen = tdl.nap_anh_nen()
    so_lop = len(ds)
    print(f"Sinh dữ liệu rút gọn: {so_lop} lớp × ({N_TR} huấn luyện + {N_TE} kiểm thử)...")
    tr, te = [], {k: [] for k in DIEU_KIEN}
    thong_ke_ab = []
    for i, d in enumerate(ds):
        goc = tdl.doc_anh_rgba(os.path.join("bien_chuan", d["tep"]))
        r1, r2 = np.random.default_rng(1000 + i), np.random.default_rng(900000 + i)   # cùng hạt giống với tao_du_lieu.py
        for _ in range(N_TR):
            a = cv2.resize(tdl.tao_mau(goc, r1, nen), (32, 32), interpolation=cv2.INTER_AREA)
            tr.append(a)
            if _ < 10:
                L, A, B = lab(a); thong_ke_ab.append((A.astype(np.float32) - 128, B.astype(np.float32) - 128))
        for _ in range(N_TE):
            a = tdl.tao_mau(goc, r2, nen)
            for k, f in DIEU_KIEN.items():
                te[k].append(cv2.resize(f(a), (32, 32), interpolation=cv2.INTER_AREA))
    y_tr = np.repeat(np.arange(so_lop), N_TR)
    y_te = np.repeat(np.arange(so_lop), N_TE)

    A_ = np.concatenate([a.ravel() for a, _ in thong_ke_ab]); B_ = np.concatenate([b.ravel() for _, b in thong_ke_ab])
    dong = ["THỐNG KÊ KÊNH MÀU a, b CỦA OPENCV (ảnh 8 bit: a, b được lưu dưới dạng a+128, b+128, khoảng 0–255)",
            f"  a − 128: trung bình {A_.mean():.2f}, độ lệch chuẩn {A_.std():.2f}, phân vị 1%–99%: {np.percentile(A_, 1):.1f} … {np.percentile(A_, 99):.1f}",
            f"  b − 128: trung bình {B_.mean():.2f}, độ lệch chuẩn {B_.std():.2f}, phân vị 1%–99%: {np.percentile(B_, 1):.1f} … {np.percentile(B_, 99):.1f}",
            f"  => chia 25 đưa phần lớn giá trị về khoảng {np.percentile(A_, 1) / 25:.1f} … {np.percentile(A_, 99) / 25:.1f}, cùng cỡ với kênh L đã chuẩn hóa Z-score", ""]
    print("\n".join(dong))

    rng = np.random.default_rng(1)
    val = np.concatenate([rng.permutation(np.where(y_tr == c)[0])[:5] for c in range(so_lop)])
    tr_i = np.setdiff1d(np.arange(len(y_tr)), val)
    ket_qua = {}
    for ten, f in PHUONG_AN.items():
        t0 = time.time()
        Xtr = np.array([f(a).reshape(-1) for a in tr], np.float32)
        so_kenh = Xtr.shape[1] // 1024
        Xte = {k: np.array([f(a).reshape(-1) for a in v], np.float32) for k, v in te.items()}
        np.random.seed(0)
        mang = MangNoron([Xtr.shape[1], 512, 256, so_lop], ti_le_dropout=0.3, seed=42)
        mang.huan_luyen(Xtr[tr_i], y_tr[tr_i], Xtr[val], y_tr[val], SO_EPOCH, 64, 0.01, l2=5e-4, giam_lr=0.97,
                        tang_cuong=lambda b: tang_cuong(b, so_kenh))
        ket_qua[ten] = {k: mang.do_chinh_xac(x, y_te) for k, x in Xte.items()}
        print(f"==> {ten}: " + ", ".join(f"{k} {v * 100:.2f}%" for k, v in ket_qua[ten].items()) + f"  ({time.time() - t0:.0f}s)")

    dong.append(f"ĐỘ CHÍNH XÁC (%) TRÊN TẬP KIỂM THỬ RÚT GỌN ({so_lop} lớp × {N_TE} ảnh = {so_lop * N_TE} ảnh mỗi điều kiện; "
                f"huấn luyện {N_TR} ảnh/lớp, {SO_EPOCH} epoch)")
    dong.append(f"{'Phương án':42s}" + "".join(f"{k:>24s}" for k in DIEU_KIEN))
    with open(os.path.join(RA, "thuc_nghiem_doi_chung.csv"), "w", encoding="utf-8-sig") as fo:
        fo.write("Phương án," + ",".join(DIEU_KIEN) + "\n")
        for ten, kq in ket_qua.items():
            dong.append(f"{ten:42s}" + "".join(f"{kq[k] * 100:23.2f}%" for k in DIEU_KIEN))
            fo.write(f'"{ten}",' + ",".join(f"{kq[k] * 100:.2f}" for k in DIEU_KIEN) + "\n")
    open(os.path.join(RA, "thuc_nghiem_doi_chung.txt"), "w", encoding="utf-8").write("\n".join(dong))
    print("\n".join(dong[-len(ket_qua) - 2:]))

    fig, ax = plt.subplots(figsize=(12, 4.6))
    w = 0.13
    for j, (ten, kq) in enumerate(ket_qua.items()):
        ax.bar(np.arange(len(DIEU_KIEN)) + (j - 2.5) * w, [kq[k] * 100 for k in DIEU_KIEN], w, label=ten.split(" ", 1)[1] if False else ten)
    ax.set_xticks(range(len(DIEU_KIEN)), list(DIEU_KIEN)); ax.set_ylabel("Độ chính xác (%)")
    ax.set_ylim(max(0, min(min(v.values()) for v in ket_qua.values()) * 100 - 5), 100)
    ax.legend(fontsize=8, ncol=2); ax.grid(axis="y", alpha=.3)
    plt.tight_layout(); plt.savefig(os.path.join(RA, "thuc_nghiem_doi_chung.png"), dpi=150, facecolor="white")


if __name__ == "__main__":
    main()
