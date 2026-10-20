"""
ỨNG DỤNG TRỢ GIÚP NGƯỜI HỌC NHẬN DẠNG BIỂN BÁO GIAO THÔNG
- Bên trái: thư viện ảnh biển báo -> người học bấm chọn ảnh bất kỳ.
- Bên phải: ảnh đã chọn + kết quả nhận dạng: tên biển, nhóm, đặc điểm, ý nghĩa, độ tin cậy.
- Với ảnh chụp ngoài đường (biển báo nhỏ, nhiều cây cối, nhà cửa), người học KÉO CHUỘT
  khoanh vùng quanh biển báo -> chương trình chỉ nhận dạng phần được khoanh.
Chạy: python ung_dung.py
"""
import os
import glob
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
from mlp import MangNoron
from tien_xu_ly import doc_anh, tien_xu_ly

GOC = os.path.dirname(os.path.abspath(__file__))
FILE_MO_HINH = os.path.join(GOC, "mo_hinh", "mlp.npz")
FILE_BIEN_BAO = os.path.join(GOC, "bien_bao.json")
THU_MUC_MAU = os.path.join(GOC, "anh_mau")
NGUONG_TIN_CAY = 0.5
KHUNG_ANH = 320   # kích thước ô hiển thị ảnh (pixel)

MAU_NEN, MAU_THE, MAU_CHINH, MAU_CHU = "#eef2f7", "#ffffff", "#1f4e8c", "#222222"
FONT = "Segoe UI"


class UngDung(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trợ giúp học biển báo giao thông - Mạng nơron nhân tạo")
        self.geometry("1100x760")
        self.configure(bg=MAU_NEN)
        try:
            self.mang = MangNoron.nap(FILE_MO_HINH)
        except Exception:
            messagebox.showerror("Lỗi", "Chưa có mô hình. Hãy chạy huan_luyen.py trước.")
            self.destroy(); return
        with open(FILE_BIEN_BAO, encoding="utf-8") as f:
            self.bien_bao = json.load(f)
        self.anh_nho = []
        self._tao_giao_dien()
        self._nap_thu_vien()

    # ---------------- Giao diện ----------------
    def _tao_giao_dien(self):
        tk.Label(self, text="NHẬN DẠNG BIỂN BÁO GIAO THÔNG", bg=MAU_CHINH, fg="white",
                 font=(FONT, 16, "bold"), pady=10).pack(fill="x")

        than = tk.Frame(self, bg=MAU_NEN)
        than.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Cột trái: thư viện ảnh ---
        trai = tk.Frame(than, bg=MAU_THE, bd=1, relief="solid")
        trai.pack(side="left", fill="y")
        tk.Label(trai, text="Thư viện biển báo (bấm để nhận dạng)", bg=MAU_THE,
                 fg=MAU_CHINH, font=(FONT, 11, "bold")).pack(pady=(8, 4))
        tk.Button(trai, text="📂  Chọn ảnh từ máy tính", command=self.chon_tu_may,
                  bg=MAU_CHINH, fg="white", font=(FONT, 10, "bold"), relief="flat",
                  padx=10, pady=4, cursor="hand2").pack(pady=(0, 8))

        khung = tk.Frame(trai, bg=MAU_THE)
        khung.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(khung, width=330, bg=MAU_THE, highlightthickness=0)
        cuon = tk.Scrollbar(khung, orient="vertical", command=self.canvas.yview)
        self.luoi = tk.Frame(self.canvas, bg=MAU_THE)
        self.luoi.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.luoi, anchor="nw")
        self.canvas.configure(yscrollcommand=cuon.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        cuon.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 120), "units"))

        # --- Cột phải: kết quả ---
        phai = tk.Frame(than, bg=MAU_THE, bd=1, relief="solid")
        phai.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.o_anh = tk.Canvas(phai, width=KHUNG_ANH, height=KHUNG_ANH, bg="#f5f5f5",
                               highlightthickness=1, highlightbackground="#ccc", cursor="crosshair")
        self.o_anh.pack(pady=(14, 4))
        self.o_anh.create_text(KHUNG_ANH // 2, KHUNG_ANH // 2, text="Chưa chọn ảnh", fill="#888", font=(FONT, 11))
        self.o_anh.bind("<ButtonPress-1>", self._bat_dau_khoanh)
        self.o_anh.bind("<B1-Motion>", self._dang_khoanh)
        self.o_anh.bind("<ButtonRelease-1>", self._ket_thuc_khoanh)

        hang = tk.Frame(phai, bg=MAU_THE)
        hang.pack()
        tk.Label(hang, text="Mẹo: kéo chuột khoanh vùng quanh biển báo để nhận dạng chính xác hơn",
                 bg=MAU_THE, fg="#777", font=(FONT, 9, "italic")).pack(side="left")
        tk.Button(hang, text="Nhận dạng toàn ảnh", command=self._bo_khoanh, relief="flat",
                  bg="#dbe6f5", fg=MAU_CHINH, font=(FONT, 9), cursor="hand2", padx=6).pack(side="left", padx=8)
        self.anh_goc = None
        self.khung_chon = None

        self.lbl_ten = tk.Label(phai, text="", bg=MAU_THE, fg=MAU_CHINH, font=(FONT, 16, "bold"), wraplength=620)
        self.lbl_ten.pack()
        self.lbl_tin_cay = tk.Label(phai, text="", bg=MAU_THE, font=(FONT, 11))
        self.lbl_tin_cay.pack(pady=(2, 8))

        self.lbl_chi_tiet = tk.Label(phai, text="", bg=MAU_THE, fg=MAU_CHU, font=(FONT, 11),
                                     justify="left", anchor="w", wraplength=620)
        self.lbl_chi_tiet.pack(fill="x", padx=20)
        self.lbl_top3 = tk.Label(phai, text="", bg=MAU_THE, fg="#555", font=(FONT, 10),
                                 justify="left", anchor="w", wraplength=620)
        self.lbl_top3.pack(fill="x", padx=20, pady=(10, 0))

    def _nap_thu_vien(self):
        ds = sorted(p for p in glob.glob(os.path.join(THU_MUC_MAU, "*"))
                    if p.lower().endswith((".png", ".jpg", ".jpeg", ".ppm", ".bmp")))
        if not ds:
            tk.Label(self.luoi, text="Thư mục anh_mau/ trống.\nChạy chuan_bi_du_lieu.py\nhoặc chép ảnh vào đó.",
                     bg=MAU_THE, fg="#888").grid(padx=20, pady=20)
        for i, p in enumerate(ds):
            anh = Image.open(p).convert("RGB").resize((88, 88))
            tk_anh = ImageTk.PhotoImage(anh)
            self.anh_nho.append(tk_anh)  # giữ tham chiếu để ảnh không bị mất
            nut = tk.Button(self.luoi, image=tk_anh, relief="flat", bg=MAU_THE, cursor="hand2",
                            activebackground="#dbe6f5", command=lambda duong_dan=p: self.nhan_dang(duong_dan))
            nut.grid(row=i // 3, column=i % 3, padx=6, pady=6)

    # ---------------- Xử lý ----------------
    def chon_tu_may(self):
        p = filedialog.askopenfilename(title="Chọn ảnh biển báo",
                                       filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.ppm *.bmp")])
        if p:
            self.nhan_dang(p)

    def nhan_dang(self, duong_dan):
        anh_cv = doc_anh(duong_dan)
        if anh_cv is None:
            messagebox.showerror("Lỗi", "Không đọc được ảnh."); return
        self.anh_goc = anh_cv
        self._hien_thi_anh(anh_cv)
        self._nhan_dang_anh(anh_cv)

    # ---------------- Hiển thị ảnh và khoanh vùng ----------------
    def _hien_thi_anh(self, anh_cv):
        h, w = anh_cv.shape[:2]
        self.ti_le = min(KHUNG_ANH / w, KHUNG_ANH / h)
        rong, cao = max(1, int(w * self.ti_le)), max(1, int(h * self.ti_le))
        self.lech_x, self.lech_y = (KHUNG_ANH - rong) // 2, (KHUNG_ANH - cao) // 2
        anh = Image.fromarray(cv2.cvtColor(anh_cv, cv2.COLOR_BGR2RGB)).resize((rong, cao))
        self.anh_lon = ImageTk.PhotoImage(anh)
        self.o_anh.delete("all")
        self.o_anh.create_image(self.lech_x, self.lech_y, image=self.anh_lon, anchor="nw")
        self.khung_chon = None

    def _bat_dau_khoanh(self, e):
        if self.anh_goc is None:
            return
        self.diem_dau = (e.x, e.y)
        if self.khung_chon:
            self.o_anh.delete(self.khung_chon)
        self.khung_chon = self.o_anh.create_rectangle(e.x, e.y, e.x, e.y, outline="#ffcc00", width=3)

    def _dang_khoanh(self, e):
        if self.khung_chon:
            self.o_anh.coords(self.khung_chon, self.diem_dau[0], self.diem_dau[1], e.x, e.y)

    def _ket_thuc_khoanh(self, e):
        if not self.khung_chon:
            return
        x1, y1, x2, y2 = self.o_anh.coords(self.khung_chon)
        x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2))
        if x2 - x1 < 10 or y2 - y1 < 10:   # khoanh quá nhỏ (bấm nhầm) -> bỏ qua
            self.o_anh.delete(self.khung_chon); self.khung_chon = None
            return
        # Đổi tọa độ trên màn hình -> tọa độ trên ảnh gốc
        h, w = self.anh_goc.shape[:2]
        X1 = int(min(max((x1 - self.lech_x) / self.ti_le, 0), w))
        X2 = int(min(max((x2 - self.lech_x) / self.ti_le, 0), w))
        Y1 = int(min(max((y1 - self.lech_y) / self.ti_le, 0), h))
        Y2 = int(min(max((y2 - self.lech_y) / self.ti_le, 0), h))
        if X2 - X1 < 5 or Y2 - Y1 < 5:
            return
        self._nhan_dang_anh(self.anh_goc[Y1:Y2, X1:X2])

    def _bo_khoanh(self):
        if self.anh_goc is None:
            return
        if self.khung_chon:
            self.o_anh.delete(self.khung_chon); self.khung_chon = None
        self._nhan_dang_anh(self.anh_goc)

    # ---------------- Nhận dạng bằng mạng nơron ----------------
    def _nhan_dang_anh(self, anh_cv):
        # Tiền xử lý -> đưa vào mạng nơron -> lấy xác suất
        xac_suat = self.mang.du_doan_xac_suat(tien_xu_ly(anh_cv))[0]
        thu_tu = xac_suat.argsort()[::-1]
        lop, p_max = int(thu_tu[0]), float(xac_suat[thu_tu[0]])
        tt = self.bien_bao.get(str(lop), {"ten": f"Lớp {lop}", "nhom": "?", "dac_diem": "?", "y_nghia": "Chưa có mô tả."})

        self.lbl_ten.configure(text=tt["ten"])
        if p_max >= NGUONG_TIN_CAY:
            self.lbl_tin_cay.configure(text=f"Độ tin cậy: {p_max * 100:.1f}%", fg="#1a7f37")
        else:
            self.lbl_tin_cay.configure(text=f"Độ tin cậy thấp ({p_max * 100:.1f}%) - hãy khoanh vùng sát biển báo và thử lại", fg="#c0392b")
        self.lbl_chi_tiet.configure(text=f"Nhóm:  {tt['nhom']}\n\nĐặc điểm:  {tt['dac_diem']}\n\nÝ nghĩa:  {tt['y_nghia']}")

        dong = ["Các khả năng khác:"]
        for k in thu_tu[1:3]:
            ten = self.bien_bao.get(str(int(k)), {}).get("ten", f"Lớp {int(k)}")
            dong.append(f"   • {ten}: {xac_suat[k] * 100:.1f}%")
        self.lbl_top3.configure(text="\n".join(dong))

if __name__ == "__main__":
    UngDung().mainloop()
