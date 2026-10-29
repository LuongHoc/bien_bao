# 🚦 Ứng dụng trợ giúp người học nhận dạng biển báo giao thông sử dụng mạng nơron nhân tạo

Đồ án tốt nghiệp – **Lương Văn Học** (K225480106025) – GVHD: **ThS. Lê Thị Lương**
Ứng dụng trực tuyến: https://bienbao.luongvanhoc.io.vn

Ứng dụng giúp người học tra cứu, nhận dạng và luyện tập **340 biển báo** theo **QCVN 41:2024/BGTVT**.
Mạng nơron nhiều lớp (3.072 – 512 – 256 – 340) và thuật toán **lan truyền ngược** được tự cài đặt bằng NumPy.

## Quy trình chạy (theo thứ tự)

| Bước | Lệnh | Kết quả |
|---|---|---|
| 1 | `pip install -r requirements.txt` | Cài thư viện |
| 2 | `python tai_bien_chuan.py` | 378 tệp hình chuẩn từ Wikimedia Commons |
| 3 | `python lam_sach_danh_sach.py` | 340 biển, bảng đối chiếu `bang_anh_xa_ma.csv` |
| 4 | `python tao_du_lieu.py` | 51.000 ảnh huấn luyện, 10.200 ảnh kiểm thử (ảnh tổng hợp) |
| 5 | `python kiem_tra_gradient.py` | Kiểm chứng lan truyền ngược |
| 6 | `python huan_luyen.py` | Mô hình `mo_hinh/mlp.npz` |
| 7 | `python danh_gia.py` | Đánh giá chi tiết trên ảnh tổng hợp |
| 8 | `python thuc_nghiem_doi_chung.py` | Thực nghiệm đối chứng tiền xử lý |
| 9 | `python danh_gia_anh_thuc.py` | Đánh giá trên ảnh chụp thực tế (`anh_thuc/`) |
| 10 | `python do_hieu_nang.py` | Độ trễ p50/p95 |
| 11 | `python kiem_thu_chuc_nang.py` | Kiểm thử chức năng tự động |
| 12 | `streamlit run app_web.py` | Chạy ứng dụng web |
| 13 | `python tong_hop_khao_sat.py` | Tổng hợp khảo sát người học (`khao_sat.csv`) |
| 14 | `python dong_goi_web.py` | Đóng gói `ban_web/` để đưa lên máy chủ |

Kết quả số liệu nằm trong thư mục `ket_qua/`. Lưu ý phạm vi: kết quả trên **ảnh tổng hợp** (sinh từ hình chuẩn) và trên
**ảnh chụp thực tế** được báo cáo tách riêng.

## Nguồn dữ liệu
- Hình vẽ biển báo: Wikimedia Commons (bộ hình *Vietnam road sign*).
- Nội dung, ý nghĩa: QCVN 41:2024/BGTVT, do sinh viên biên soạn và đối chiếu (`y_nghia_bien_bao.json`).
