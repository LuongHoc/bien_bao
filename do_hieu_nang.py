"""
ĐO HIỆU NĂNG NHẬN DẠNG (độ trễ p50/p95) trên máy đang chạy.
  (a) Tiền xử lý + lan truyền xuôi cho 1 ảnh đã cắt (ảnh 160×160)
  (b) Toàn bộ quy trình với ảnh chụp điện thoại 12 MP: giải mã JPEG -> cắt vùng -> tiền xử lý -> mạng nơron
  (c) (tùy chọn) Thời gian tải trang web qua Internet:  python do_hieu_nang.py https://bienbao.luongvanhoc.io.vn
Kết quả lưu ket_qua/hieu_nang.txt
"""
import os
import sys
import time
import glob
import platform
import numpy as np
import cv2
from mlp import MangNoron
from tien_xu_ly import tien_xu_ly, doc_anh

N = 300
mang = MangNoron.nap(os.path.join("mo_hinh", "mlp.npz"))
anh = [doc_anh(p) for p in sorted(glob.glob(os.path.join("anh_mau", "*.png")))[:50]]
dong = [f"Máy đo: {platform.system()} {platform.release()} | CPU: {platform.processor() or platform.machine()} | "
        f"số luồng: {os.cpu_count()} | Python {platform.python_version()} | NumPy {np.__version__}", ""]


def do(ten, ham):
    for _ in range(10):
        ham(0)                           # chạy khởi động
    t = []
    for i in range(N):
        s = time.perf_counter(); ham(i); t.append((time.perf_counter() - s) * 1000)
    t = np.array(t)
    dong.append(f"{ten:58s} p50 = {np.percentile(t, 50):7.2f} ms | p95 = {np.percentile(t, 95):7.2f} ms | max = {t.max():7.2f} ms")


do("(a) Tiền xử lý + mạng nơron (1 ảnh đã cắt)", lambda i: mang.du_doan_xac_suat(tien_xu_ly(anh[i % len(anh)])))
lon = cv2.resize(anh[0], (4000, 3000))
ok, jpg = cv2.imencode(".jpg", lon, [cv2.IMWRITE_JPEG_QUALITY, 90])
buf = jpg.tobytes()


def toan_bo(i):
    a = cv2.imdecode(np.frombuffer(buf, np.uint8), cv2.IMREAD_COLOR)
    vung = a[500:2500, 1000:3000]
    return mang.du_doan_xac_suat(tien_xu_ly(vung))


do(f"(b) Ảnh điện thoại 12 MP ({len(buf) / 1e6:.1f} MB): giải mã + cắt + nhận dạng", toan_bo)
if len(sys.argv) > 1:
    import urllib.request
    t = []
    for _ in range(20):
        s = time.perf_counter(); urllib.request.urlopen(sys.argv[1], timeout=20).read(); t.append((time.perf_counter() - s) * 1000)
    dong.append(f"{'(c) Tải trang ' + sys.argv[1]:58s} p50 = {np.percentile(t, 50):7.1f} ms | p95 = {np.percentile(t, 95):7.1f} ms (20 lần)")
dong.append(f"\nSố lần đo mỗi mục: {N} (sau 10 lần chạy khởi động).")
os.makedirs("ket_qua", exist_ok=True)
open(os.path.join("ket_qua", "hieu_nang.txt"), "w", encoding="utf-8").write("\n".join(dong))
print("\n".join(dong))
