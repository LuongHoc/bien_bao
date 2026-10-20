# 🚦 Ứng dụng trợ giúp người học nhận dạng biển báo giao thông sử dụng mạng nơron nhân tạo

Đồ án tốt nghiệp – **Lương Văn Học** (K225480106025)
Giảng viên hướng dẫn: **ThS. Lê Thị Lương**

🌐 **Dùng thử trực tuyến:** https://bienbao.luongvanhoc.io.vn

---

## Giới thiệu

Ứng dụng giúp người học (đặc biệt là người ôn thi giấy phép lái xe) tra cứu và ghi nhớ **340 biển báo giao thông** thuộc 5 nhóm theo **QCVN 41:2024/BGTVT**. Khi người học chọn một hình ảnh biển báo, **mạng nơron nhân tạo** nhận dạng biển và ứng dụng hiển thị tên, nhóm, đặc điểm và ý nghĩa của biển đó.

Mạng nơron nhiều lớp (MLP) và **thuật toán lan truyền ngược (Back Propagation)** được **tự cài đặt bằng NumPy**, không sử dụng thư viện học sâu có sẵn.

## Tính năng

- **📚 Thư viện biển báo:** xem 340 biển, lọc theo nhóm, tìm kiếm; bấm "Xem ý nghĩa" để mạng nơron nhận dạng và giải thích biển.
- **📷 Nhận dạng ảnh:** tải ảnh hoặc chụp bằng điện thoại, khoanh vùng biển báo rồi nhận dạng.
- **✏️ Luyện tập:** thi thử 14 bộ đề có đếm giờ, luyện theo nhóm biển, ôn lại câu sai, thống kê kết quả.

## Mô hình

| Thành phần | Mô tả |
|---|---|
| Tiền xử lý ảnh | Thu nhỏ 32 × 32, không gian màu LAB, cân bằng CLAHE, chuẩn hóa |
| Kiến trúc mạng | 3.072 – 512 – 256 – 340 (ReLU, Softmax) |
| Huấn luyện | Lan truyền ngược, mini-batch, momentum, L2, Dropout, dừng sớm |
| Dữ liệu | Hình biển báo chuẩn + tăng cường dữ liệu (180 ảnh/biển) |
| Kết quả | Độ chính xác khoảng 97% trên tập kiểm thử |

## Cấu trúc mã nguồn

| Tệp | Chức năng |
|---|---|
| `tai_bien_chuan.py` | Tải hình vẽ biển báo chuẩn |
| `lam_sach_danh_sach.py` | Loại bỏ hình trùng, chuẩn hóa mã biển theo QCVN 41:2024 |
| `tao_du_lieu.py` | Sinh dữ liệu huấn luyện bằng tăng cường dữ liệu |
| `tien_xu_ly.py` | Tiền xử lý ảnh |
| `mlp.py` | Mạng nơron nhiều lớp và thuật toán lan truyền ngược |
| `huan_luyen.py` | Huấn luyện và đánh giá mô hình |
| `ghep_y_nghia.py` | Ghép nội dung ý nghĩa biển báo với các lớp của mạng |
| `app_web.py` | Ứng dụng web (Streamlit) |
| `ung_dung.py` | Ứng dụng chạy trên máy tính (Tkinter) |
| `dong_goi_web.py` | Đóng gói ứng dụng để triển khai lên máy chủ |
| `y_nghia_bien_bao.json` | Tên, nhóm, đặc điểm, ý nghĩa của từng biển |
| `mo_hinh/mlp.npz` | Trọng số mạng nơron đã huấn luyện |

## Cài đặt và chạy

Yêu cầu: **Python 3.11**

```bash
git clone https://github.com/LuongHoc/bien_bao.git
cd bien_bao
pip install -r requirements.txt
streamlit run app_web.py
```

Hoặc chạy phiên bản máy tính: `python ung_dung.py`

## Huấn luyện lại từ đầu

```bash
python tai_bien_chuan.py        # 1. Tải hình biển báo chuẩn
python lam_sach_danh_sach.py    # 2. Làm sạch danh sách
python tao_du_lieu.py           # 3. Sinh dữ liệu huấn luyện
python huan_luyen.py            # 4. Huấn luyện và đánh giá
```

## Nguồn dữ liệu

- Hình vẽ biển báo: **Wikimedia Commons** (bộ hình *Vietnam road sign*).
- Nội dung, ý nghĩa biển báo: **QCVN 41:2024/BGTVT** – Quy chuẩn kỹ thuật quốc gia về báo hiệu đường bộ.
