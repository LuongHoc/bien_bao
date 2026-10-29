"""
Mạng nơron nhiều lớp (MLP) tự cài đặt bằng NumPy
và huấn luyện bằng THUẬT TOÁN LAN TRUYỀN NGƯỢC (Back Propagation).
(Liên hệ Chương 2 của báo cáo.)

Ký hiệu:
    z(l) = a(l-1) . W(l) + b(l)      (tổng có trọng số)
    a(l) = f(z(l))                   (f = ReLU ở lớp ẩn, Softmax ở lớp ra)
    Hàm mất mát: Cross-Entropy  E = -1/m * sum(y * log(y_hat))
"""
import numpy as np


class MangNoron:
    def __init__(self, cac_lop, ti_le_dropout=0.0, seed=42):
        """
        cac_lop: số nơron mỗi lớp, ví dụ [1024, 512, 256, 43].
        ti_le_dropout: tỉ lệ nơron lớp ẩn bị "tắt" ngẫu nhiên khi huấn luyện (chống quá khớp).
        """
        self.cac_lop = list(cac_lop)
        self.p_drop = ti_le_dropout
        rng = np.random.default_rng(seed)
        self.W, self.b = [], []
        for n_vao, n_ra in zip(cac_lop[:-1], cac_lop[1:]):
            # Khởi tạo He (phù hợp với ReLU)
            self.W.append(rng.normal(0, np.sqrt(2.0 / n_vao), (n_vao, n_ra)).astype(np.float32))
            self.b.append(np.zeros(n_ra, dtype=np.float32))
        self._khoi_tao_van_toc()

    def _khoi_tao_van_toc(self):
        self.vW = [np.zeros_like(w) for w in self.W]
        self.vb = [np.zeros_like(b) for b in self.b]

    # ---------- Hàm kích hoạt ----------
    @staticmethod
    def relu(z):
        return np.maximum(0, z)

    @staticmethod
    def softmax(z):
        z = z - z.max(axis=1, keepdims=True)  # ổn định số học
        e = np.exp(z)
        return e / e.sum(axis=1, keepdims=True)

    # ---------- Bước 1: Lan truyền xuôi ----------
    def lan_truyen_xuoi(self, X, huan_luyen=False):
        A, Z, M = [X], [], []
        so_lop = len(self.W)
        for l in range(so_lop):
            z = A[-1] @ self.W[l] + self.b[l]
            Z.append(z)
            if l == so_lop - 1:
                A.append(self.softmax(z))
            else:
                a = self.relu(z)
                mat_na = None
                if huan_luyen and self.p_drop > 0:
                    # Dropout: tắt ngẫu nhiên một số nơron, chia (1-p) để giữ nguyên kỳ vọng
                    mat_na = (np.random.rand(*a.shape) >= self.p_drop).astype(np.float32) / (1 - self.p_drop)
                    a = a * mat_na
                M.append(mat_na)
                A.append(a)
        return Z, A, M

    # ---------- Hàm mất mát ----------
    @staticmethod
    def ham_mat_mat(y_hat, Y):
        return float(-np.mean(np.sum(Y * np.log(y_hat + 1e-9), axis=1)))

    # ---------- Bước 2: Lan truyền ngược sai số ----------
    def lan_truyen_nguoc(self, Z, A, M, Y):
        m = Y.shape[0]
        L = len(self.W)
        dW, db = [None] * L, [None] * L
        # Sai số lớp ra (Softmax + Cross-Entropy): delta = y_hat - y
        delta = (A[-1] - Y) / m
        for l in reversed(range(L)):
            dW[l] = A[l].T @ delta           # dE/dW = a(l-1)^T . delta(l)
            db[l] = delta.sum(axis=0)        # dE/db = tổng delta
            if l > 0:
                # Truyền sai số về lớp trước theo quy tắc chuỗi, nhân đạo hàm ReLU
                delta = (delta @ self.W[l].T) * (Z[l - 1] > 0)
                if M[l - 1] is not None:
                    delta = delta * M[l - 1]  # nơron bị tắt thì không nhận sai số
        return dW, db

    # ---------- Bước 3: Cập nhật trọng số (Gradient Descent + momentum) ----------
    def cap_nhat(self, dW, db, toc_do_hoc, momentum=0.9, l2=1e-4):
        for l in range(len(self.W)):
            g = dW[l] + l2 * self.W[l]  # thêm chính quy hóa L2 chống quá khớp
            self.vW[l] = momentum * self.vW[l] - toc_do_hoc * g
            self.vb[l] = momentum * self.vb[l] - toc_do_hoc * db[l]
            self.W[l] += self.vW[l]
            self.b[l] += self.vb[l]

    # ---------- Huấn luyện ----------
    def huan_luyen(self, X, y, X_val, y_val, so_epoch=30, batch=64,
                   toc_do_hoc=0.01, momentum=0.9, l2=1e-4, giam_lr=0.95, tang_cuong=None, giu_tot_nhat=True,
                   chon_mau=None, kien_nhan=None):
        """
        giu_tot_nhat: lưu điểm kiểm tra (checkpoint) - giữ trọng số ở epoch có độ chính xác kiểm định cao nhất.
        kien_nhan: số epoch "kiên nhẫn" cho DỪNG SỚM (early stopping) thực sự: nếu độ chính xác kiểm định
                   không cải thiện sau `kien_nhan` epoch liên tiếp thì dừng huấn luyện. None = luôn chạy đủ so_epoch.
        chon_mau: hàm trả về danh sách chỉ số mẫu dùng cho mỗi epoch (để cân bằng số mẫu giữa các loại).
        """
        so_lop_ra = self.cac_lop[-1]
        Y = np.eye(so_lop_ra, dtype=np.float32)[y]  # mã hóa one-hot
        lich_su = {"loss": [], "acc_train": [], "acc_val": [], "lr": []}
        tot_nhat = (-1.0, None, None, 0)
        for ep in range(1, so_epoch + 1):
            thu_tu = np.random.permutation(chon_mau() if chon_mau else np.arange(len(X)))
            tong_loss = 0.0
            for s in range(0, len(thu_tu), batch):     # duyệt HẾT các mẫu đã chọn cho epoch này
                j = thu_tu[s:s + batch]
                Xb = tang_cuong(X[j]) if tang_cuong else X[j]
                Z, A, M = self.lan_truyen_xuoi(Xb, huan_luyen=True)
                tong_loss += self.ham_mat_mat(A[-1], Y[j]) * len(j)
                dW, db = self.lan_truyen_nguoc(Z, A, M, Y[j])
                self.cap_nhat(dW, db, toc_do_hoc, momentum, l2)
            lich_su["lr"].append(toc_do_hoc)
            toc_do_hoc *= giam_lr
            loss = tong_loss / len(thu_tu)
            acc_tr = self.do_chinh_xac(X, y)
            acc_va = self.do_chinh_xac(X_val, y_val)
            lich_su["loss"].append(loss)
            lich_su["acc_train"].append(acc_tr)
            lich_su["acc_val"].append(acc_va)
            print(f"Epoch {ep:3d}/{so_epoch} | loss={loss:.4f} | "
                  f"acc_train={acc_tr:.4f} | acc_val={acc_va:.4f}")
            if acc_va > tot_nhat[0]:
                tot_nhat = (acc_va, [w.copy() for w in self.W] if giu_tot_nhat else None,
                            [b.copy() for b in self.b] if giu_tot_nhat else None, ep)
            elif kien_nhan is not None and ep - tot_nhat[3] >= kien_nhan:
                print(f"-> Dừng sớm ở epoch {ep}: {kien_nhan} epoch liên tiếp không cải thiện độ chính xác kiểm định")
                break
        lich_su["epoch_tot_nhat"] = tot_nhat[3]
        lich_su["so_epoch_da_chay"] = len(lich_su["loss"])
        if giu_tot_nhat and tot_nhat[1] is not None:
            self.W, self.b = tot_nhat[1], tot_nhat[2]
            print(f"-> Dùng trọng số tốt nhất (checkpoint) ở epoch {tot_nhat[3]} (acc_val={tot_nhat[0]:.4f})")
        return lich_su

    # ---------- Dự đoán ----------
    def du_doan_xac_suat(self, X):
        return self.lan_truyen_xuoi(np.atleast_2d(X))[1][-1]

    def du_doan(self, X):
        return self.du_doan_xac_suat(X).argmax(axis=1)

    def do_chinh_xac(self, X, y, batch=2048):
        dung = 0
        for s in range(0, len(X), batch):
            dung += int((self.du_doan(X[s:s + batch]) == y[s:s + batch]).sum())
        return dung / len(X)

    # ---------- Lưu / nạp mô hình ----------
    def luu(self, duong_dan):
        tham_so = {"cac_lop": np.array(self.cac_lop)}
        for l in range(len(self.W)):
            tham_so[f"W{l}"], tham_so[f"b{l}"] = self.W[l], self.b[l]
        np.savez(duong_dan, **tham_so)

    @classmethod
    def nap(cls, duong_dan):
        d = np.load(duong_dan)
        mang = cls(d["cac_lop"].tolist())
        for l in range(len(mang.W)):
            mang.W[l], mang.b[l] = d[f"W{l}"], d[f"b{l}"]
        mang._khoi_tao_van_toc()
        return mang
