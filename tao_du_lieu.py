"""
BƯỚC 2 - TẠO DỮ LIỆU HUẤN LUYỆN TỪ ẢNH BIỂN BÁO CHUẨN.
Mỗi biển chỉ có 1 ảnh vẽ chuẩn, nên chương trình TỰ SINH nhiều ảnh biến thể bằng các kỹ thuật
xử lý ảnh số: đặt lên nền khác nhau, thay đổi kích thước, xoay nhẹ, biến đổi phối cảnh nhẹ,
thay đổi độ sáng/tương phản, làm mờ nhẹ, thêm nhiễu, nén JPEG.
(Chỉ biến đổi NHẸ - biển vẫn còn nguyên vẹn, rõ ràng, đúng hình dạng và màu sắc chuẩn.)

Kết quả:
  data/du_lieu.npz      dữ liệu đã tiền xử lý cho huan_luyen.py
  anh_mau/              ảnh chuẩn của từng biển (người học bấm chọn trong ứng dụng)
  lop.json              bảng số thứ tự lớp <-> mã biển
  bien_bao.json         tên, ý nghĩa từng lớp (lấy từ y_nghia_bien_bao.json theo mã biển)
  vi_du_tao_du_lieu/    một số ảnh sinh ra để minh họa trong báo cáo

Cách dùng:  python tao_du_lieu.py
"""
import os
import json
import shutil
import numpy as np
import cv2
from tien_xu_ly import tien_xu_ly

THU_MUC_CHUAN = "bien_chuan"
SO_ANH_HUAN_LUYEN = 150   # số ảnh sinh ra cho mỗi biển để huấn luyện
SO_ANH_KIEM_THU = 30      # số ảnh sinh ra cho mỗi biển để kiểm thử (sinh riêng, mạng chưa thấy)
KHUNG = 96                # kích thước ảnh sinh ra (pixel)
THU_MUC_NEN = "nen"       # (không bắt buộc) đặt ảnh chụp đường phố/cây cối vào đây để làm nền


def doc_anh_rgba(duong_dan):
    anh = cv2.imdecode(np.fromfile(duong_dan, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if anh is None:
        return None
    if anh.ndim == 2:
        anh = cv2.cvtColor(anh, cv2.COLOR_GRAY2BGRA)
    elif anh.shape[2] == 3:
        anh = cv2.cvtColor(anh, cv2.COLOR_BGR2BGRA)
    ys, xs = np.where(anh[:, :, 3] > 10)          # cắt sát phần biển báo (bỏ viền trong suốt)
    if len(xs) == 0:
        return None
    return anh[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def nap_anh_nen():
    ds = []
    if os.path.isdir(THU_MUC_NEN):
        for f in os.listdir(THU_MUC_NEN):
            a = cv2.imdecode(np.fromfile(os.path.join(THU_MUC_NEN, f), dtype=np.uint8), cv2.IMREAD_COLOR)
            if a is not None and min(a.shape[:2]) >= KHUNG:
                ds.append(a)
    return ds


def tao_nen(rng, anh_nen):
    loai = rng.integers(4) if not anh_nen else rng.integers(5)
    if loai == 0:   # màu trơn (trời, tường, cây...)
        return np.full((KHUNG, KHUNG, 3), rng.integers(40, 230, 3), np.uint8)
    if loai == 1:   # chuyển màu
        a, b = rng.integers(40, 230, 3), rng.integers(40, 230, 3)
        t = np.linspace(0, 1, KHUNG)[:, None, None]
        return (a * (1 - t) + b * t).repeat(KHUNG, axis=1).astype(np.uint8)
    if loai in (2, 3):  # các mảng màu loang (giống tán cây, nhà cửa)
        nho = rng.integers(40, 230, (6, 6, 3)).astype(np.float32)
        nho = (0.5 * nho + 0.5 * nho.mean(axis=2, keepdims=True)).astype(np.uint8)  # giảm độ rực, giống nền thật hơn
        return cv2.GaussianBlur(cv2.resize(nho, (KHUNG, KHUNG), interpolation=cv2.INTER_CUBIC), (0, 0), 3)
    nen = anh_nen[rng.integers(len(anh_nen))]   # cắt ngẫu nhiên từ ảnh nền thật
    y, x = rng.integers(nen.shape[0] - KHUNG + 1), rng.integers(nen.shape[1] - KHUNG + 1)
    return nen[y:y + KHUNG, x:x + KHUNG].copy()


def tao_mau(bien, rng, anh_nen):
    """Sinh 1 ảnh biến thể của biển báo chuẩn."""
    h, w = bien.shape[:2]
    ti_le = rng.uniform(0.72, 0.92) * KHUNG / max(h, w)          # biển chiếm 72-92% khung
    bw, bh = max(8, int(w * ti_le)), max(8, int(h * ti_le))
    bien_nho = cv2.resize(bien, (bw, bh), interpolation=cv2.INTER_AREA)

    # Đặt vào giữa khung + dịch chuyển nhẹ
    lop = np.zeros((KHUNG, KHUNG, 4), np.uint8)
    x0 = (KHUNG - bw) // 2 + int(rng.integers(-3, 4))
    y0 = (KHUNG - bh) // 2 + int(rng.integers(-3, 4))
    x0, y0 = min(max(x0, 0), KHUNG - bw), min(max(y0, 0), KHUNG - bh)
    lop[y0:y0 + bh, x0:x0 + bw] = bien_nho

    # Xoay nhẹ + biến đổi phối cảnh nhẹ (như nhìn hơi nghiêng)
    goc = np.float32([[0, 0], [KHUNG, 0], [KHUNG, KHUNG], [0, KHUNG]])
    lech = rng.uniform(-0.05, 0.05, (4, 2)).astype(np.float32) * KHUNG
    M = cv2.getPerspectiveTransform(goc, goc + lech)
    R = np.vstack([cv2.getRotationMatrix2D((KHUNG / 2, KHUNG / 2), rng.uniform(-8, 8), 1.0), [0, 0, 1]])
    lop = cv2.warpPerspective(lop, (R @ M).astype(np.float32), (KHUNG, KHUNG), flags=cv2.INTER_LINEAR)

    # Ghép biển lên nền theo kênh alpha
    nen = tao_nen(rng, anh_nen).astype(np.float32)
    alpha = lop[:, :, 3:4].astype(np.float32) / 255.0
    anh = lop[:, :, :3].astype(np.float32) * alpha + nen * (1 - alpha)

    # Thay đổi nhẹ độ sáng / tương phản (điều kiện ánh sáng khác nhau)
    anh = (anh - 128) * rng.uniform(0.85, 1.15) + 128 + rng.uniform(-30, 30)
    anh = np.clip(anh, 0, 255).astype(np.uint8)
    if rng.random() < 0.4:   # làm mờ nhẹ (ảnh chụp hơi nhòe)
        anh = cv2.GaussianBlur(anh, (0, 0), rng.uniform(0.3, 1.0))
    if rng.random() < 0.4:   # nhiễu nhẹ
        anh = np.clip(anh + rng.normal(0, rng.uniform(2, 6), anh.shape), 0, 255).astype(np.uint8)
    if rng.random() < 0.5:   # nén JPEG (ảnh tải từ mạng, điện thoại)
        ok, buf = cv2.imencode(".jpg", anh, [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(50, 95))])
        anh = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    return anh


def anh_chuan_nen_trang(bien, kich_thuoc=160):
    h, w = bien.shape[:2]
    s = 0.85 * kich_thuoc / max(h, w)
    bien = cv2.resize(bien, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    nen = np.full((kich_thuoc, kich_thuoc, 3), 255, np.float32)
    y0, x0 = (kich_thuoc - bien.shape[0]) // 2, (kich_thuoc - bien.shape[1]) // 2
    a = bien[:, :, 3:4].astype(np.float32) / 255
    vung = nen[y0:y0 + bien.shape[0], x0:x0 + bien.shape[1]]
    nen[y0:y0 + bien.shape[0], x0:x0 + bien.shape[1]] = bien[:, :, :3] * a + vung * (1 - a)
    return nen.astype(np.uint8)


def main():
    with open(os.path.join(THU_MUC_CHUAN, "danh_sach.json"), encoding="utf-8") as f:
        danh_sach = json.load(f)
    bien_list = []
    for d in danh_sach:
        b = doc_anh_rgba(os.path.join(THU_MUC_CHUAN, d["tep"]))
        if b is not None:
            bien_list.append((d["ma"], b))
    so_lop = len(bien_list)
    n = SO_ANH_HUAN_LUYEN + SO_ANH_KIEM_THU
    print(f"{so_lop} biển báo, sinh {n} ảnh/biển. Bộ nhớ cần khoảng "
          f"{so_lop * n * 3072 * 4 / 1e9:.2f} GB")

    anh_nen = nap_anh_nen()
    X_tr = np.empty((so_lop * SO_ANH_HUAN_LUYEN, 3072), np.float32)
    X_te = np.empty((so_lop * SO_ANH_KIEM_THU, 3072), np.float32)
    y_tr = np.repeat(np.arange(so_lop), SO_ANH_HUAN_LUYEN)
    y_te = np.repeat(np.arange(so_lop), SO_ANH_KIEM_THU)

    for d in ["anh_mau", "vi_du_tao_du_lieu"]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)
    os.makedirs("data", exist_ok=True)

    lop = []
    for i, (ma, bien) in enumerate(bien_list):
        rng_tr, rng_te = np.random.default_rng(1000 + i), np.random.default_rng(900000 + i)  # 2 nguồn ngẫu nhiên khác nhau
        for k in range(SO_ANH_HUAN_LUYEN):
            X_tr[i * SO_ANH_HUAN_LUYEN + k] = tien_xu_ly(tao_mau(bien, rng_tr, anh_nen))
        for k in range(SO_ANH_KIEM_THU):
            anh = tao_mau(bien, rng_te, anh_nen)
            X_te[i * SO_ANH_KIEM_THU + k] = tien_xu_ly(anh)
            if i < 6 and k < 8:
                cv2.imencode(".png", anh)[1].tofile(f"vi_du_tao_du_lieu/{i:03d}_{k}.png")
        cv2.imencode(".png", anh_chuan_nen_trang(bien))[1].tofile(f"anh_mau/{i:03d}_0.png")
        lop.append({"id": i, "ma": ma})
        if i % 20 == 0:
            print(f"  đã tạo {i + 1}/{so_lop} biển")

    np.savez(os.path.join("data", "du_lieu.npz"), X_train=X_tr, y_train=y_tr, X_test=X_te, y_test=y_te)
    with open("lop.json", "w", encoding="utf-8") as f:
        json.dump(lop, f, ensure_ascii=False, indent=1)

    # Tạo bien_bao.json cho ứng dụng từ y_nghia_bien_bao.json (ý nghĩa lưu theo MÃ biển)
    y_nghia = json.load(open("y_nghia_bien_bao.json", encoding="utf-8")) if os.path.exists("y_nghia_bien_bao.json") else {}
    bien_bao = {str(l["id"]): y_nghia.get(l["ma"], {"ten": f"{l['ma']} - (cần bổ sung tên)", "nhom": "(cần bổ sung)",
                                                    "dac_diem": "(cần bổ sung)", "y_nghia": "(cần bổ sung)"})
                for l in lop}
    with open("bien_bao.json", "w", encoding="utf-8") as f:
        json.dump(bien_bao, f, ensure_ascii=False, indent=2)
    thieu = [l["ma"] for l in lop if l["ma"] not in y_nghia]

    print(f"\nXong! Train: {X_tr.shape}, Test: {X_te.shape}, số loại biển: {so_lop}")
    print("Biển chưa có mô tả trong y_nghia_bien_bao.json:", ", ".join(thieu) if thieu else "không có")


if __name__ == "__main__":
    main()
