"""
Gom các file cần thiết của bản web vào thư mục ban_web/ để chép lên máy chủ.
Chạy SAU KHI đã huấn luyện xong:  python dong_goi_web.py
"""
import os
import shutil

DICH = "ban_web"
if os.path.exists(DICH):
    shutil.rmtree(DICH)
os.makedirs(os.path.join(DICH, "mo_hinh"))
for f in ["app_web.py", "mlp.py", "tien_xu_ly.py", "du_lieu_hoc_tap.py", "bien_bao.json", "lop.json", "nguong_tin_cay.json"]:
    if not os.path.exists(f):
        continue
    shutil.copy(f, DICH)
shutil.copy(os.path.join("mo_hinh", "mlp.npz"), os.path.join(DICH, "mo_hinh"))
shutil.copytree("anh_mau", os.path.join(DICH, "anh_mau"))
if os.path.isdir("giao_dien"):
    shutil.copytree("giao_dien", os.path.join(DICH, "giao_dien"))       # ảnh bìa trang chủ
if os.path.isdir(".streamlit"):
    shutil.copytree(".streamlit", os.path.join(DICH, ".streamlit"))   # màu giao diện
with open(os.path.join(DICH, "requirements.txt"), "w") as f:
    f.write("numpy\nopencv-python-headless\npillow\nstreamlit\nstreamlit-cropper\n")
print("Đã tạo thư mục ban_web/ - chép thư mục này lên máy chủ (xem hướng dẫn giai đoạn 7).")
