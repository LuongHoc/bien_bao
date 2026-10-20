"""
BƯỚC 1 - TẢI ẢNH BIỂN BÁO CHUẨN (hình vẽ chuẩn theo QCVN 41) từ Wikimedia Commons.
Mỗi biển báo có 1 ảnh vẽ chuẩn, nền trong suốt, tên tệp dạng "Vietnam road sign P102.svg".
Kết quả: thư mục bien_chuan/ chứa các ảnh PNG đặt tên theo mã biển (P.102.png, W.207a.png, ...).

Cách dùng:  python tai_bien_chuan.py
"""
import os
import re
import json
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
TIEN_TO = "Vietnam road sign "
THU_MUC = "bien_chuan"
NHOM_LAY = {"P", "DP", "R", "W", "I", "S"}   # P: cấm, DP: hết cấm, R: hiệu lệnh, W: cảnh báo, I: chỉ dẫn, S: biển phụ
KICH_THUOC = 256                     # chiều rộng ảnh PNG tải về (pixel)
UA = {"User-Agent": "BienBaoDoAnTotNghiep/1.0 (student graduation project)"}


def goi_api(tham_so):
    url = API + "?" + urllib.parse.urlencode({**tham_so, "format": "json"})
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def ma_bien(tieu_de):
    """'File:Vietnam road sign P102.svg' -> ('P', 'P.102');  'W207a' -> ('W', 'W.207a')."""
    ten = tieu_de.split(":", 1)[-1][len(TIEN_TO):]
    ten = os.path.splitext(ten)[0].strip()
    goc = ten.replace(".", "").replace(" ", "")
    m = re.match(r"^([A-Z]+)(\d.*)$", goc)
    if not m:
        return None, None
    return m.group(1), f"{m.group(1)}.{m.group(2)}"


def main():
    os.makedirs(THU_MUC, exist_ok=True)
    tham_so = {"action": "query", "generator": "allpages", "gapnamespace": 6, "gapprefix": TIEN_TO,
               "gaplimit": 50, "prop": "imageinfo", "iiprop": "url", "iiurlwidth": KICH_THUOC}
    danh_sach, so_tai = [], 0
    while True:
        kq = goi_api(tham_so)
        for trang in kq.get("query", {}).get("pages", {}).values():
            nhom, ma = ma_bien(trang["title"])
            if nhom not in NHOM_LAY or "imageinfo" not in trang:
                continue
            url = trang["imageinfo"][0].get("thumburl") or trang["imageinfo"][0]["url"]
            ten_tep = re.sub(r"[^\w.\-]", "_", ma) + ".png"
            duong_dan = os.path.join(THU_MUC, ten_tep)
            if not os.path.exists(duong_dan):
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                        open(duong_dan, "wb").write(r.read())
                    so_tai += 1
                    time.sleep(0.1)
                except Exception as e:
                    print(f"  Lỗi tải {ma}: {e}")
                    continue
            danh_sach.append({"ma": ma, "tep": ten_tep, "nguon": trang["title"]})
            print(f"  {ma:12s} <- {trang['title']}")
        if "continue" not in kq:
            break
        tham_so.update(kq["continue"])
    with open(os.path.join(THU_MUC, "danh_sach.json"), "w", encoding="utf-8") as f:
        json.dump(sorted(danh_sach, key=lambda d: d["ma"]), f, ensure_ascii=False, indent=1)
    tep_goc = os.path.join(THU_MUC, "danh_sach_goc.json")
    if os.path.exists(tep_goc):
        os.remove(tep_goc)   # danh sách mới -> để lam_sach_danh_sach.py làm sạch lại từ đầu
    print(f"\nXong: {len(danh_sach)} biển báo (tải mới {so_tai}) trong thư mục {THU_MUC}/")


if __name__ == "__main__":
    main()
