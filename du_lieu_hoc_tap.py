"""
LƯU VÀ ĐỌC DỮ LIỆU ĐÁNH GIÁ CỦA ỨNG DỤNG (không lưu ảnh, không lưu thông tin cá nhân):
  lich_su_hoc.csv          kết quả từng bài luyện tập của người học (theo biệt danh do người học tự đặt)
  phan_hoi_nhan_dang.csv   người học xác nhận kết quả nhận dạng ảnh tải lên là đúng hay sai
  khao_sat.csv             câu trả lời khảo sát trải nghiệm (thang SUS + câu về học tập), cùng định dạng Google Forms
Thư mục lưu: biến môi trường BIEN_BAO_DU_LIEU, mặc định là thư mục du_lieu_ung_dung NẰM CẠNH thư mục dự án
(để khi chép đè bản ứng dụng mới lên máy chủ, dữ liệu không bị xóa).
"""
import os
import csv
import json
import threading
from datetime import datetime

GOC = os.path.dirname(os.path.abspath(__file__))
THU_MUC = os.environ.get("BIEN_BAO_DU_LIEU", os.path.join(os.path.dirname(GOC), "du_lieu_ung_dung"))
_khoa = threading.Lock()

CAU_SUS = [
    "Tôi nghĩ tôi sẽ muốn sử dụng ứng dụng này thường xuyên.",
    "Tôi thấy ứng dụng phức tạp một cách không cần thiết.",
    "Tôi thấy ứng dụng dễ sử dụng.",
    "Tôi nghĩ tôi cần người hỗ trợ kỹ thuật mới dùng được ứng dụng.",
    "Tôi thấy các chức năng của ứng dụng được kết hợp tốt với nhau.",
    "Tôi thấy ứng dụng có quá nhiều điểm không nhất quán.",
    "Tôi nghĩ hầu hết mọi người sẽ học cách dùng ứng dụng rất nhanh.",
    "Tôi thấy ứng dụng rườm rà, khó dùng.",
    "Tôi cảm thấy tự tin khi sử dụng ứng dụng.",
    "Tôi cần học nhiều thứ trước khi có thể sử dụng ứng dụng.",
]
CAU_HOC = [
    "Thư viện biển báo giúp tôi hiểu ý nghĩa các biển.",
    "Câu hỏi luyện tập sát với nội dung thi lý thuyết lái xe.",
    "Phần giải thích sau mỗi câu giúp tôi nhớ biển lâu hơn.",
    "Chức năng nhận dạng cho kết quả đúng với ảnh biển tôi chụp.",
    "Tôi muốn tiếp tục dùng ứng dụng để ôn thi.",
]
COT_KHAO_SAT = (["Dấu thời gian", "Đã có bằng lái"] + [f"[S{i + 1}] {c}" for i, c in enumerate(CAU_SUS)]
                + [f"[H{i + 1}] {c}" for i, c in enumerate(CAU_HOC)] + ["Điều bạn thích nhất", "Điều cần cải thiện"])
COT_LICH_SU = ["thoi_gian", "biet_danh", "loai_bai", "ten_bai", "so_cau", "dung", "sai", "bo_qua", "dat", "theo_nhom", "bien_sai"]
COT_PHAN_HOI = ["thoi_gian", "nguon_anh", "ma_du_doan", "diem_softmax", "top5", "danh_gia", "ma_dung"]


def _duong(ten):
    return os.path.join(THU_MUC, ten)


def ghi_dong(ten, cot, dong):
    os.makedirs(THU_MUC, exist_ok=True)
    with _khoa:
        moi = not os.path.exists(_duong(ten))
        with open(_duong(ten), "a", encoding="utf-8-sig" if moi else "utf-8", newline="") as f:
            w = csv.writer(f)
            if moi:
                w.writerow(cot)
            w.writerow([dong.get(c, "") for c in cot] if isinstance(dong, dict) else dong)


def doc_bang(ten):
    if not os.path.exists(_duong(ten)):
        return []
    with open(_duong(ten), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def bay_gio():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def luu_bai_lam(biet_danh, loai_bai, ten_bai, so_cau, dung, sai, bo_qua, dat, theo_nhom, bien_sai):
    ghi_dong("lich_su_hoc.csv", COT_LICH_SU, {
        "thoi_gian": bay_gio(), "biet_danh": biet_danh.strip().lower(), "loai_bai": loai_bai, "ten_bai": ten_bai,
        "so_cau": so_cau, "dung": dung, "sai": sai, "bo_qua": bo_qua, "dat": dat,
        "theo_nhom": json.dumps(theo_nhom, ensure_ascii=False), "bien_sai": " ".join(bien_sai)})


def lich_su_cua(biet_danh):
    b = biet_danh.strip().lower()
    return [r for r in doc_bang("lich_su_hoc.csv") if r["biet_danh"] == b]


def ghi_phan_hoi(nguon_anh, ma_du_doan, diem, top5, danh_gia, ma_dung=""):
    ghi_dong("phan_hoi_nhan_dang.csv", COT_PHAN_HOI, {
        "thoi_gian": bay_gio(), "nguon_anh": nguon_anh, "ma_du_doan": ma_du_doan, "diem_softmax": f"{diem:.4f}",
        "top5": " ".join(top5), "danh_gia": danh_gia, "ma_dung": ma_dung})


def ghi_khao_sat(bang_lai, sus, hoc, thich, cai_thien):
    ghi_dong("khao_sat.csv", COT_KHAO_SAT, [bay_gio(), bang_lai] + [str(v) for v in sus] + [str(v) for v in hoc] + [thich, cai_thien])


def diem_sus(sus):
    """10 câu thang 1-5 -> điểm SUS 0-100 (câu lẻ: điểm - 1, câu chẵn: 5 - điểm, tổng × 2,5)."""
    return sum((v - 1) if i % 2 == 0 else (5 - v) for i, v in enumerate(sus)) * 2.5
