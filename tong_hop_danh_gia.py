"""
TỔNG HỢP ĐÁNH GIÁ CHỨC NĂNG GIÁO DỤC TỪ DỮ LIỆU THỰC TẾ CỦA ỨNG DỤNG:
  (1) Nhận dạng ảnh tải lên: tỉ lệ kết quả được người học xác nhận đúng, theo mức điểm Softmax
  (2) Luyện tập: số bài, số người học, tỉ lệ đúng, tiến bộ giữa lần đầu và lần gần nhất của mỗi người học
  (3) Khảo sát trải nghiệm: chạy tong_hop_khao_sat.py
Cách dùng:  python tong_hop_danh_gia.py   -> ket_qua/danh_gia_su_dung.txt
"""
import os
import numpy as np
import du_lieu_hoc_tap as dl

dong = [f"ĐÁNH GIÁ TỪ DỮ LIỆU SỬ DỤNG ỨNG DỤNG (thư mục dữ liệu: {dl.THU_MUC})", ""]
ph = dl.doc_bang("phan_hoi_nhan_dang.csv")
dong.append("1. NHẬN DẠNG ẢNH TẢI LÊN (người học tự xác nhận kết quả)")
if ph:
    d = np.array([r["danh_gia"] == "dung" for r in ph]); p = np.array([float(r["diem_softmax"]) for r in ph])
    top5 = np.array([bool(r["ma_dung"]) and r["ma_dung"] in r["top5"].split() for r in ph])
    co_ma = np.array([bool(r["ma_dung"]) for r in ph])
    dong += [f"   Số ảnh được phản hồi: {len(ph)} | xác nhận đúng: {d.sum()} ({d.mean() * 100:.1f}%)",
             f"   Ảnh tải lên: {sum(r['nguon_anh'] == 'tải lên' for r in ph)} | chụp webcam: {sum(r['nguon_anh'] == 'webcam' for r in ph)}"]
    if co_ma.any():
        dong.append(f"   Trong {co_ma.sum()} ảnh người học cho biết biển đúng: đáp án nằm trong top-5 ở {top5[co_ma].mean() * 100:.1f}% số ảnh")
    for a, b in [(0, .5), (.5, .9), (.9, 1.01)]:
        m = (p >= a) & (p < b)
        if m.any():
            dong.append(f"   Điểm Softmax {a:.1f}–{min(b, 1):.1f}: {m.sum()} ảnh, đúng {d[m].mean() * 100:.1f}%")
else:
    dong.append("   Chưa có phản hồi.")
ls = dl.doc_bang("lich_su_hoc.csv")
dong += ["", "2. LUYỆN TẬP (theo dõi kết quả theo biệt danh)"]
if ls:
    tl = np.array([int(r["dung"]) / max(int(r["so_cau"]), 1) for r in ls])
    nguoi = {}
    for r in ls:
        nguoi.setdefault(r["biet_danh"], []).append(int(r["dung"]) / max(int(r["so_cau"]), 1))
    nhieu = {k: v for k, v in nguoi.items() if len(v) >= 2}
    de = [r for r in ls if r["loai_bai"] == "Bộ đề"]
    dong += [f"   Số bài: {len(ls)} | số người học: {len(nguoi)} | tỉ lệ đúng trung bình: {tl.mean() * 100:.1f}%",
             f"   Số câu đã trả lời: {sum(int(r['so_cau']) for r in ls)}"]
    if de:
        dong.append(f"   Bộ đề thi thử: {len(de)} lượt, Đạt {sum(r['dat'] == 'Đạt' for r in de)} lượt ({sum(r['dat'] == 'Đạt' for r in de) / len(de) * 100:.0f}%)")
    if nhieu:
        dau = np.array([v[0] for v in nhieu.values()]); cuoi = np.array([v[-1] for v in nhieu.values()])
        dong.append(f"   {len(nhieu)} người học làm từ 2 bài trở lên: tỉ lệ đúng lần đầu {dau.mean() * 100:.1f}% -> lần gần nhất "
                    f"{cuoi.mean() * 100:.1f}% (thay đổi {(cuoi - dau).mean() * 100:+.1f} điểm phần trăm)")
    dem = {}
    for r in ls:
        for m in r["bien_sai"].split():
            dem[m] = dem.get(m, 0) + 1
    dong.append("   Biển bị trả lời sai nhiều nhất: " + ", ".join(f"{m} ({n})" for m, n in sorted(dem.items(), key=lambda x: -x[1])[:10]))
else:
    dong.append("   Chưa có bài nào được lưu (người học cần đặt biệt danh ở tab Luyện tập).")
ks = dl.doc_bang("khao_sat.csv")
dong += ["", f"3. KHẢO SÁT: {len(ks)} người trả lời -> chạy python tong_hop_khao_sat.py để xem chi tiết."]
os.makedirs("ket_qua", exist_ok=True)
open(os.path.join("ket_qua", "danh_gia_su_dung.txt"), "w", encoding="utf-8").write("\n".join(dong))
print("\n".join(dong))
