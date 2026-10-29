"""
Module tiền xử lý ảnh (liên hệ Chương 1 - Xử lý ảnh số).
Các bước: đổi kích thước -> chuyển sang không gian màu LAB
          -> kênh L (độ sáng): cân bằng histogram thích nghi (CLAHE) + chuẩn hóa theo từng ảnh
          -> kênh a, b (màu sắc): chuẩn hóa về quanh 0
          -> duỗi thành vector 32*32*3 = 3072 phần tử.
Giữ lại MÀU SẮC vì màu là đặc trưng quan trọng của biển báo
(ví dụ: biển cấm đỗ xe nền xanh khác biển tốc độ nền trắng, nhưng ảnh xám thì gần như giống nhau).
"""
import cv2
import numpy as np

KICH_THUOC = 32  # ảnh 32x32
SO_KENH = 3      # 3 kênh màu L, a, b -> vector 3072 phần tử = số nơron lớp vào
_clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))


def doc_anh(duong_dan):
    """Đọc ảnh (hỗ trợ đường dẫn có dấu tiếng Việt trên Windows)."""
    du_lieu = np.fromfile(duong_dan, dtype=np.uint8)
    return cv2.imdecode(du_lieu, cv2.IMREAD_COLOR)


def tien_xu_ly(anh_bgr):
    anh = cv2.resize(anh_bgr, (KICH_THUOC, KICH_THUOC), interpolation=cv2.INTER_AREA)
    # LAB: L = độ sáng, a = trục xanh lá <-> đỏ, b = trục xanh lam <-> vàng
    L, a, b = cv2.split(cv2.cvtColor(anh, cv2.COLOR_BGR2LAB))
    # Kênh độ sáng: CLAHE làm rõ ảnh tối/sáng, rồi chuẩn hóa theo từng ảnh
    L = _clahe.apply(L).astype(np.float32)
    L = (L - L.mean()) / (L.std() + 1e-6)
    # Kênh màu: giữ nguyên thông tin màu tuyệt đối (đỏ, xanh, vàng), chỉ đưa về quanh 0
    a = (a.astype(np.float32) - 128.0) / 25.0
    b = (b.astype(np.float32) - 128.0) / 25.0
    return np.dstack([L, a, b]).reshape(-1)


def tang_cuong(X_batch):
    """
    Tăng cường dữ liệu (data augmentation): xoay nhẹ, phóng to/thu nhỏ, dịch chuyển ngẫu nhiên.
    Giúp mạng nhận dạng tốt hơn khi biển báo bị nghiêng, lệch hoặc to/nhỏ khác nhau.
    Lưu ý: KHÔNG lật ảnh trái-phải vì sẽ làm đổi nghĩa biển (cấm rẽ trái <-> cấm rẽ phải).
    """
    tam = KICH_THUOC / 2
    ket_qua = np.empty_like(X_batch)
    for i, x in enumerate(X_batch):
        anh = x.reshape(KICH_THUOC, KICH_THUOC, SO_KENH)
        M = cv2.getRotationMatrix2D((tam, tam), np.random.uniform(-12, 12), np.random.uniform(0.85, 1.15))
        M[:, 2] += np.random.uniform(-2, 2, size=2)
        ket_qua[i] = cv2.warpAffine(anh, M, (KICH_THUOC, KICH_THUOC),
                                    borderMode=cv2.BORDER_REPLICATE).reshape(-1)
    return ket_qua
