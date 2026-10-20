# Ứng dụng trợ giúp người học nhận dạng biển báo giao thông (mạng nơron nhân tạo)

## Cài thư viện
    python -m pip install -r requirements.txt

## Quy trình (chạy lần lượt)
| Bước | Lệnh | Kết quả |
|---|---|---|
| 1. Tải hình biển chuẩn | `python tai_bien_chuan.py` | thư mục `bien_chuan/` |
| 2. Làm sạch bản trùng | `python lam_sach_danh_sach.py` | `bien_chuan/danh_sach.json` |
| 3. Sinh dữ liệu | `python tao_du_lieu.py` | `data/du_lieu.npz`, `anh_mau/`, `lop.json`, `bien_bao.json` |
| 4. Huấn luyện | `python huan_luyen.py` | `mo_hinh/mlp.npz`, `ket_qua/` |
| 5. Chạy ứng dụng web | `streamlit run app_web.py` | trình duyệt |
| (hoặc) ứng dụng máy tính | `python ung_dung.py` | cửa sổ Tkinter |
| 6. Đóng gói lên máy chủ | `python dong_goi_web.py` | thư mục `ban_web/` |

Sửa ý nghĩa biển báo: sửa `y_nghia_bien_bao.json` rồi chạy `python ghep_y_nghia.py`.

## Cấu trúc mã nguồn
| File | Vai trò | Chương báo cáo |
|---|---|---|
| tien_xu_ly.py | Tiền xử lý ảnh (LAB, CLAHE, chuẩn hóa), tăng cường dữ liệu | 1 |
| tao_du_lieu.py | Sinh ảnh biến thể từ hình chuẩn (nền, xoay, phối cảnh, sáng tối, mờ, nhiễu) | 1, 4 |
| mlp.py | Mạng nơron nhiều lớp + thuật toán lan truyền ngược (NumPy) | 2 |
| huan_luyen.py | Huấn luyện, đánh giá, vẽ biểu đồ | 4 |
| y_nghia_bien_bao.json | Tên, nhóm, đặc điểm, ý nghĩa theo QCVN 41:2024/BGTVT | 3 |
| app_web.py, ung_dung.py | Ứng dụng cho người học (web / máy tính) | 4 |
