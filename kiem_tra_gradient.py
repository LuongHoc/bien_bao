"""
KIỂM CHỨNG THUẬT TOÁN LAN TRUYỀN NGƯỢC (gradient checking) VÀ KIỂM THỬ ĐƠN VỊ cho mlp.py.
So sánh gradient tính bằng lan truyền ngược (giải tích) với gradient tính bằng sai phân trung tâm (số):
    dE/dw ≈ [E(w + ε) − E(w − ε)] / (2ε)
Sai số tương đối (theo chuẩn vector trên các phần tử được kiểm tra):
    ‖g_lan_truyen_nguoc − g_so‖ / (‖g_lan_truyen_nguoc‖ + ‖g_so‖)
Thông thường: < 1e-6 là cài đặt đúng (với số thực 64 bit).
Cách dùng:  python kiem_tra_gradient.py      -> in kết quả và lưu ket_qua/kiem_tra_gradient.txt
"""
import os
import numpy as np
from mlp import MangNoron

np.random.seed(0)
dong = []


def ghi(s=""):
    print(s)
    dong.append(s)


def mang_64(cac_lop, seed=0):
    m = MangNoron(cac_lop, ti_le_dropout=0.0, seed=seed)
    m.W = [w.astype(np.float64) for w in m.W]
    m.b = [b.astype(np.float64) + np.random.default_rng(seed).normal(0, 0.1, b.shape) for b in m.b]
    return m


def _E(m, X, Y):
    y_hat = m.lan_truyen_xuoi(X)[1][-1]
    return float(-np.mean(np.sum(Y * np.log(y_hat), axis=1)))


def kiem_tra(cac_lop, m_mau=7, so_phan_tu=None, eps=1e-6, seed=0):
    rng = np.random.default_rng(seed)
    m = mang_64(cac_lop, seed)
    X = rng.normal(0, 1, (m_mau, cac_lop[0]))
    Y = np.eye(cac_lop[-1])[rng.integers(cac_lop[-1], size=m_mau)]
    Z, A, M = m.lan_truyen_xuoi(X)
    dW, db = m.lan_truyen_nguoc(Z, A, M, Y)
    ket_qua = []
    for ten, tham_so, grad in [("W", m.W, dW), ("b", m.b, db)]:
        for l in range(len(tham_so)):
            p = tham_so[l]
            chi_so = list(np.ndindex(p.shape))
            if so_phan_tu and len(chi_so) > so_phan_tu:
                chi_so = [chi_so[k] for k in rng.choice(len(chi_so), so_phan_tu, replace=False)]
            g1, g2 = [], []
            for idx in chi_so:
                goc = p[idx]
                p[idx] = goc + eps; e1 = _E(m, X, Y)
                p[idx] = goc - eps; e2 = _E(m, X, Y)
                p[idx] = goc
                g_so = (e1 - e2) / (2 * eps)
                g1.append(grad[l][idx]); g2.append(g_so)
            g1, g2 = np.array(g1), np.array(g2)
            sai = np.linalg.norm(g1 - g2) / max(np.linalg.norm(g1) + np.linalg.norm(g2), 1e-12)
            ket_qua.append((f"{ten}{l + 1}", p.shape, len(chi_so), sai))
    return ket_qua


ghi("=== 1. KIỂM CHỨNG GRADIENT (lan truyền ngược so với sai phân trung tâm, ε = 1e-6, số thực 64 bit) ===")
for cac_lop, so in [([8, 6, 5, 4], None), ([3072, 512, 256, 340], 30)]:
    ghi(f"\nMạng {cac_lop}" + (" - kiểm tra TOÀN BỘ tham số" if so is None else f" - kiểm tra ngẫu nhiên {so} phần tử mỗi ma trận"))
    ghi(f"{'Tham số':8s} {'Kích thước':14s} {'Số phần tử KT':>14s} {'Sai số tương đối':>18s}  Kết luận")
    for ten, kt, n, sai in kiem_tra(cac_lop, so_phan_tu=so):
        ghi(f"{ten:8s} {str(kt):14s} {n:14d} {sai:18.2e}  {'ĐẠT' if sai < 1e-6 else 'KHÔNG ĐẠT'}")

ghi("\n=== 2. KIỂM THỬ ĐƠN VỊ ===")
kq = []
m = MangNoron([10, 8, 5], seed=1)
X = np.random.default_rng(1).normal(0, 1, (6, 10)).astype(np.float32)
Z, A, M = m.lan_truyen_xuoi(X)
kq.append(("Kích thước đầu ra lan truyền xuôi = (6, 5)", A[-1].shape == (6, 5)))
kq.append(("Softmax: mỗi hàng có tổng bằng 1, giá trị trong (0, 1)",
           np.allclose(A[-1].sum(1), 1, atol=1e-6) and (A[-1] > 0).all() and (A[-1] < 1).all()))
kq.append(("Softmax ổn định số học với đầu vào rất lớn (z = 1000)",
           np.isfinite(MangNoron.softmax(np.array([[1000.0, 999.0, 0.0]]))).all()))
# dE/dz lớp ra = y_hat - y
m64 = mang_64([4, 3]); Xs = np.random.default_rng(2).normal(0, 1, (5, 4)); Ys = np.eye(3)[[0, 2, 1, 1, 0]]
Z, A, M = m64.lan_truyen_xuoi(Xs); dW, db = m64.lan_truyen_nguoc(Z, A, M, Ys)
kq.append(("Sai số lớp ra Softmax + Cross-Entropy: dE/db = tổng (ŷ − y)/m", np.allclose(db[0], (A[-1] - Ys).sum(0) / 5)))
# Dropout
md = MangNoron([200, 400, 5], ti_le_dropout=0.3, seed=3)
Z, A, M = md.lan_truyen_xuoi(np.ones((50, 200), np.float32), huan_luyen=True)
kq.append(("Dropout: tỉ lệ nơron bị tắt ≈ 30%", abs((M[0] == 0).mean() - 0.3) < 0.02))
kq.append(("Dropout: kỳ vọng mặt nạ ≈ 1 (chia cho 1 − p)", abs(M[0].mean() - 1) < 0.03))
dW, db = md.lan_truyen_nguoc(Z, A, M, np.eye(5)[np.zeros(50, int)])
kq.append(("Dropout: nơron bị tắt không nhận gradient", np.allclose(dW[0][:, (M[0] == 0).all(0)], 0)))
kq.append(("Khi nhận dạng (huan_luyen=False) không áp dụng Dropout", md.lan_truyen_xuoi(np.ones((2, 200)))[2][0] is None))
# Học được bài toán XOR (phi tuyến)
Xx = np.array([[0, 0], [0, 1], [1, 0], [1, 1]] * 25, np.float32); yx = np.array([0, 1, 1, 0] * 25)
mx = MangNoron([2, 16, 2], seed=4)
ls = mx.huan_luyen(Xx, yx, Xx, yx, so_epoch=300, batch=20, toc_do_hoc=0.1, l2=0, giam_lr=1.0)
kq.append(("Học được bài toán XOR (phi tuyến): độ chính xác 100%", mx.do_chinh_xac(Xx, yx) == 1.0))
kq.append(("Hàm mất mát giảm sau huấn luyện (XOR)", ls["loss"][-1] < ls["loss"][0]))
# Lưu / nạp
mx.luu("/tmp/_kt.npz") if os.name != "nt" else mx.luu(os.path.join(os.environ.get("TEMP", "."), "_kt.npz"))
duong = "/tmp/_kt.npz" if os.name != "nt" else os.path.join(os.environ.get("TEMP", "."), "_kt.npz")
kq.append(("Lưu rồi nạp lại mô hình cho kết quả dự đoán giống hệt", np.allclose(MangNoron.nap(duong).du_doan_xac_suat(Xx), mx.du_doan_xac_suat(Xx))))
# Tái hiện ví dụ tính tay ở mục 2.4 của báo cáo
mv = MangNoron([2, 2, 2])
mv.W = [np.array([[0.2, -0.1], [0.4, 0.3]]), np.array([[0.5, -0.3], [0.2, 0.6]])]
mv.b = [np.array([0.0, 0.1]), np.array([0.0, 0.0])]; mv._khoi_tao_van_toc()
xv, yv = np.array([[1.0, 0.5]]), np.array([[1.0, 0.0]])
Z, A, M = mv.lan_truyen_xuoi(xv); E0 = _E(mv, xv, yv)
dW, db = mv.lan_truyen_nguoc(Z, A, M, yv); mv.cap_nhat(dW, db, 0.1, momentum=0.0, l2=0.0); E1 = _E(mv, xv, yv)
kq.append((f"Tái hiện ví dụ tính tay mục 2.4: E giảm 0,5716 → 0,4958 (chương trình: {E0:.4f} → {E1:.4f})",
           abs(E0 - 0.5716) < 1e-4 and abs(E1 - 0.4958) < 1e-4))
for ten, ok in kq:
    ghi(f"[{'ĐẠT' if ok else 'KHÔNG ĐẠT'}] {ten}")
ghi(f"\nTổng: {sum(o for _, o in kq)}/{len(kq)} kiểm thử đạt.")
os.makedirs("ket_qua", exist_ok=True)
open(os.path.join("ket_qua", "kiem_tra_gradient.txt"), "w", encoding="utf-8").write("\n".join(dong))
