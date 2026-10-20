"""
BƯỚC 1b - LÀM SẠCH DANH SÁCH BIỂN CHUẨN (chạy sau tai_bien_chuan.py, trước tao_du_lieu.py).
Wikimedia Commons có nhiều PHIÊN BẢN của cùng một biển (mẫu QCVN 2016, 2019, 2024, bản V2, -2,
chữ hoa/chữ thường...). Nếu để nguyên, mạng nơron phải phân biệt các hình gần như giống hệt nhau
-> nhầm lẫn, độ chính xác giảm. Chương trình này:
  1. Giữ bản theo QCVN 41:2024 nếu có, bỏ các bản cũ (2016, 2019) và bản trùng (V2, -2, (50), (blue)...).
  2. Tìm các cặp hình còn lại giống nhau bất thường, in ra và lưu ảnh so sánh để kiểm tra bằng mắt.
Cách dùng:  python lam_sach_danh_sach.py
"""
import os
import re
import json
import shutil
import numpy as np
import cv2

THU_MUC = "bien_chuan"
TEP = os.path.join(THU_MUC, "danh_sach.json")
TEP_GOC = os.path.join(THU_MUC, "danh_sach_goc.json")
# Các cặp hình GIỐNG HỆT nhau đã kiểm tra bằng mắt (bỏ mã cũ, giữ mã theo QCVN 41:2024)
BO_THEM = {"DP.127a": "trùng hình P.127e", "DP.127b": "trùng hình P.127d",
           "DP.135": "trùng hình P.135", "W.239": "trùng hình W.239a",
           "DP.134": "trùng biển hết tốc độ tối đa mẫu QCVN 41:2024"}
# Đổi về đúng mã hiệu theo QCVN 41:2024 (Commons đặt tên khác với quy chuẩn)
DOI_MA = {"P.133": "DP.133", "P.134": "DP.134", "P.135": "DP.135",
          "P.127e": "DP.127a", "P.127d": "DP.127b"}
NGUONG_GIONG = 0.015     # sai khác trung bình < 1,5% -> coi là gần như trùng nhau


def anh_so_sanh(tep, kt=64):
    a = cv2.imdecode(np.fromfile(os.path.join(THU_MUC, tep), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if a.ndim == 2:
        a = cv2.cvtColor(a, cv2.COLOR_GRAY2BGRA)
    elif a.shape[2] == 3:
        a = cv2.cvtColor(a, cv2.COLOR_BGR2BGRA)
    ys, xs = np.where(a[:, :, 3] > 10)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    al = a[:, :, 3:4] / 255.0
    a = (a[:, :, :3] * al + 255 * (1 - al)).astype(np.uint8)
    return cv2.resize(a, (kt, kt), interpolation=cv2.INTER_AREA)


def main():
    if not os.path.exists(TEP_GOC):
        shutil.copy(TEP, TEP_GOC)          # giữ bản gốc, chạy lại nhiều lần vẫn cho cùng kết quả
    ds = json.load(open(TEP_GOC, encoding="utf-8"))
    tat_ca = {d["ma"] for d in ds}
    bo, giu = [], {}

    # Ưu tiên bản QCVN 41:2024 -> đổi tên về mã gốc
    ban_2024 = {re.sub(r"\(QCVN41-2024-BGTVT\)", "", d["ma"]) for d in ds if "QCVN41-2024" in d["ma"]}
    for d in ds:
        ma = d["ma"]
        if "QCVN41-2024" in ma:
            giu[re.sub(r"\(QCVN41-2024-BGTVT\)", "", ma)] = {**d, "ma": re.sub(r"\(QCVN41-2024-BGTVT\)", "", ma)}
            continue
        ly_do = BO_THEM.get(ma)
        if ly_do:
            pass
        elif re.search(r"\(QCVN41-20(16|19)", ma):
            ly_do = "mẫu QCVN cũ"
        elif ma in ban_2024:
            ly_do = "đã có bản QCVN 41:2024"
        elif re.search(r"V\d+$", ma) or re.search(r"[a-z]-2$", ma):
            ly_do = "bản vẽ trùng (V2/-2)"
        elif "(" in ma:
            ly_do = "bản vẽ trùng"
        elif ma[-1].isupper() and ma[:-1] + ma[-1].lower() in tat_ca:
            ly_do = "trùng chữ hoa/thường"
        if ly_do:
            bo.append((ma, ly_do))
        else:
            giu.setdefault(ma, d)

    for cu, moi in DOI_MA.items():
        if cu in giu:
            giu[moi] = {**giu.pop(cu), "ma": moi}
            print(f"   đổi mã {cu} -> {moi} (theo QCVN 41:2024)")
    ds_moi = sorted(giu.values(), key=lambda d: d["ma"])
    print(f"Ban đầu {len(ds)} hình -> giữ {len(ds_moi)}, bỏ {len(bo)}:")
    for ma, ly_do in bo:
        print(f"   bỏ {ma:28s} ({ly_do})")

    # Tìm các cặp hình còn lại giống nhau bất thường
    anh = np.stack([anh_so_sanh(d["tep"]) for d in ds_moi]).astype(np.float32) / 255
    phang = anh.reshape(len(anh), -1)
    cap = []
    for i in range(len(phang)):
        sai_khac = np.abs(phang[i + 1:] - phang[i]).mean(axis=1)
        for j in np.where(sai_khac < NGUONG_GIONG)[0]:
            cap.append((ds_moi[i]["ma"], ds_moi[i + 1 + j]["ma"], float(sai_khac[j]), i, i + 1 + j))
    if cap:
        print(f"\nCó {len(cap)} cặp hình rất giống nhau (xem anh_cap_giong_nhau.png):")
        hang = []
        for a, b, s, i, j in cap:
            print(f"   {a:12s} ~ {b:12s} (sai khác {s * 100:.1f}%)")
            hang.append(np.hstack([(anh[i] * 255).astype(np.uint8), np.full((64, 8, 3), 255, np.uint8),
                                   (anh[j] * 255).astype(np.uint8)]))
        cv2.imencode(".png", np.vstack(hang))[1].tofile("anh_cap_giong_nhau.png")
        print("   -> Nếu 2 hình là CÙNG một biển, xóa dòng của một mã trong bien_chuan/danh_sach.json")
    else:
        print("\nKhông còn cặp hình nào giống nhau bất thường.")

    with open(TEP, "w", encoding="utf-8") as f:
        json.dump(ds_moi, f, ensure_ascii=False, indent=1)
    print(f"\nĐã lưu danh sách mới ({len(ds_moi)} biển) vào {TEP}")


if __name__ == "__main__":
    main()
