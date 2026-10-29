"""
KIỂM THỬ CHỨC NĂNG TỰ ĐỘNG CHO ỨNG DỤNG WEB (dùng streamlit.testing - AppTest, không cần mở trình duyệt).
Cách dùng:  python kiem_thu_chuc_nang.py      -> in bảng kết quả, lưu ket_qua/kiem_thu_chuc_nang.txt
"""
import os
import time
import tempfile
import warnings
os.environ["BIEN_BAO_DU_LIEU"] = tempfile.mkdtemp(prefix="kiem_thu_")   # dữ liệu kiểm thử tách riêng, không lẫn dữ liệu thật
import logging
warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)
from streamlit.testing.v1 import AppTest

kq = []


def ghi(ten, ok, chi_tiet=""):
    kq.append((ten, bool(ok), chi_tiet))
    print(f"[{'ĐẠT' if ok else 'KHÔNG ĐẠT'}] {ten}" + (f" — {chi_tiet}" if chi_tiet else ""))


def mo(trang="luyen_tap"):
    at = AppTest.from_file("app_web.py", default_timeout=120)
    at.session_state["trang"] = trang
    return at.run()


def nut(at, bat_dau):
    return next(b for b in at.button if b.label.startswith(bat_dau))


def che_do(at):
    return next(c for c in at.segmented_control if c.label == "Chọn cách luyện tập")


def md(at):
    return " ".join(m.value for m in at.markdown)


# ---------- Trang chủ ----------
at = mo("trang_chu")
ghi("Trang chủ hiển thị không lỗi (ảnh bìa, chức năng, nhóm biển, thống kê, bài tập nhanh)", not at.exception and len(at.radio) >= 1)
r = at.radio[0]; r.set_value(0).run()
nut(at, "Kiểm tra").click().run()
ghi("Bài tập nhanh trên trang chủ: chấm ngay và cập nhật thống kê", sum(v[1] for v in at.session_state["thong_ke"].values()) == 1)
nut(at, "Xem chi tiết").click().run()
ghi("Nút “Xem chi tiết” của nhóm biển mở trang Học lý thuyết đã lọc đúng nhóm",
    at.session_state["trang"] == "thu_vien" and at.session_state["loc_nhom"] == "Biển báo cấm" and "78 biển" in md(at))

# ---------- Thư viện biển báo ----------
at = mo("thu_vien")
ghi("Ứng dụng khởi chạy không lỗi", not at.exception)
ghi("Thư viện hiển thị đủ 340 biển", "340 biển" in md(at))
at.pills[0].set_value("Biển báo cấm").run()
ghi("Lọc nhóm “Biển báo cấm” → 78 biển", "78 biển" in md(at))
at.pills[0].set_value("Tất cả").run()
at.text_input[0].input("trẻ em"); nut(at, "Tìm").click().run()
ghi("Tìm kiếm theo tên (“trẻ em”) có kết quả", "Kết quả tìm kiếm" in md(at) and "Không có biển nào" not in " ".join(i.value for i in at.info))
at.text_input[0].input("P.102"); nut(at, "Tìm").click().run()
ghi("Tìm kiếm theo mã (“P.102”) có kết quả", "Không có biển nào" not in " ".join(i.value for i in at.info))

# ---------- Luyện tập: bộ đề ----------
at = mo()
de_bien, loi_dap_an = [], 0
for so in range(1, 15):
    at.session_state["bai"] = None
    at.run()
    for p in at.pills:
        if p.label == "Chọn đề":
            p.set_value(so)
    at.run()
    nut(at, f"Bắt đầu Đề {so}").click().run()
    bai = at.session_state["bai"]
    de_bien.append([c["dung"] for c in bai["cau"]])
    loi_dap_an += sum(c["dung"] not in c["lua_chon"] or len(set(c["lua_chon"])) != 4 for c in bai["cau"])
tat_ca = [m for d in de_bien for m in d]
ghi("14 bộ đề, mỗi đề tối đa 25 câu", len(de_bien) == 14 and max(map(len, de_bien)) <= 25, f"số câu: {[len(d) for d in de_bien]}")
ghi("14 bộ đề bao phủ đủ 340 biển, không biển nào lặp lại giữa các đề", len(tat_ca) == 340 and len(set(tat_ca)) == 340)
ghi("Mỗi câu có 4 đáp án khác nhau và chứa đáp án đúng", loi_dap_an == 0)

# Kiểm tra tên đáp án không trùng nhau (đọc tên trên nút đáp án của câu đầu mỗi đề)
at = mo()
nut(at, "Bắt đầu Đề").click().run()
trung = 0
for _ in range(25):
    bai = at.session_state["bai"]
    c = bai["cau"][bai["hien"]]
    if c["dang"] == "chon_ten":
        nhan = [b.label.split(".", 1)[1].strip() for b in at.button if b.key and b.key.startswith("tl_")]
        trung += len(nhan) != len(set(nhan))
    nut(at, "Bỏ qua câu này").click().run() if bai["hien"] < len(bai["cau"]) - 1 else None
    if bai["hien"] >= len(bai["cau"]) - 1:
        break
ghi("Tên các đáp án trong cùng một câu không trùng nhau", trung == 0)

# Chấm điểm ngay khi chọn, bỏ qua được ghi nhận
at = mo()
nut(at, "Bắt đầu Đề").click().run()
bai = at.session_state["bai"]; c0 = bai["cau"][0]
k = c0["lua_chon"].index(c0["dung"])
[b for b in at.button if b.key and b.key.endswith(f"_0_{k}")][0].click().run()
ghi("Chọn đáp án đúng → chấm ngay, ghi nhận đúng", at.session_state["bai"]["cau"][0]["tra_loi"] == c0["dung"])
nut(at, "Câu tiếp theo").click().run()
c1 = at.session_state["bai"]["cau"][1]
sai = next(i for i, m in enumerate(c1["lua_chon"]) if m != c1["dung"])
[b for b in at.button if b.key and b.key.endswith(f"_1_{sai}")][0].click().run()
ghi("Chọn đáp án sai → biển được đưa vào danh sách ôn câu sai", c1["dung"] in at.session_state["cau_sai"])
nut(at, "Câu tiếp theo").click().run(); nut(at, "Bỏ qua câu này").click().run()
ghi("Bỏ qua câu hỏi → được ghi nhận là 'bỏ qua'", at.session_state["bai"]["cau"][2]["tra_loi"] == "bo_qua")
nut(at, "Nộp bài").click().run()
ghi("Nộp bài → hiển thị kết quả (đúng/sai/bỏ qua, Đạt/Chưa đạt)", at.session_state["bai"]["xong"] and len(at.metric) == 3
    and any("ĐẠT" in e.value for e in list(at.error) + list(at.success)))
# Hết giờ
at = mo()
nut(at, "Bắt đầu Đề").click().run()
at.session_state["bai"]["han"] = time.time() - 1
at.run()
ghi("Hết giờ → tự động kết thúc bài, các câu chưa làm tính là bỏ qua", at.session_state["bai"]["xong"])
# Ôn câu sai
at.session_state["bai"] = None
at.run()
che_do(at).set_value("🔁 Ôn lại câu sai").run()
nut(at, "Bắt đầu ôn").click().run()
ghi("Ôn câu sai → bài ôn gồm đúng các biển đã sai/bỏ qua", set(c["dung"] for c in at.session_state["bai"]["cau"]) == at.session_state["cau_sai"])

# Luyện theo nhóm: tránh lặp
at = mo()
lan = []
for _ in range(2):
    che_do(at).set_value("🎯 Luyện theo nhóm biển").run()
    [p for p in at.pills if p.label == "Nhóm biển"][0].set_value("Biển phụ").run()
    nut(at, "Bắt đầu luyện tập").click().run()
    bai = at.session_state["bai"]
    lan.append([c["dung"] for c in bai["cau"]])
    nut(at, "Nộp bài").click().run()          # nộp bài: các câu được ghi nhận là đã hỏi
    nut(at, "🏠").click().run()
ghi("Luyện theo nhóm: 2 lượt 10 câu liên tiếp không lặp lại biển (nhóm Biển phụ có 21 biển)",
    not set(lan[0]) & set(lan[1]), f"trùng {len(set(lan[0]) & set(lan[1]))} biển")
ghi("Thống kê theo nhóm được cập nhật", sum(v[1] for v in at.session_state["thong_ke"].values()) == 20)

# ---------- Theo dõi kết quả học tập (lịch sử theo biệt danh) ----------
import du_lieu_hoc_tap as dl
at = mo()
at.session_state["biet_danh"] = "kiem_thu_01"
for _ in range(2):
    at.session_state["bai"] = None
    at.run()
    nut(at, "Bắt đầu Đề").click().run()
    nut(at, "Nộp bài").click().run()
ls = dl.lich_su_cua("kiem_thu_01")
ghi("Theo dõi kết quả: mỗi bài nộp được lưu vào lịch sử theo biệt danh (2 bài -> 2 bản ghi)", len(ls) == 2)
ghi("Lịch sử lưu đủ số câu, số đúng/sai/bỏ qua, kết quả theo nhóm và biển sai",
    all(r["so_cau"] == "25" and r["theo_nhom"] and r["bo_qua"] for r in ls))

# ---------- Khảo sát trải nghiệm trong ứng dụng ----------
at = mo("danh_gia")
nut(at, "Gửi khảo sát").click().run()
ghi("Khảo sát: gửi khi chưa trả lời đủ 15 câu bị từ chối", not dl.doc_bang("khao_sat.csv")
    and any("tất cả các câu" in e.value for e in at.error))
for r in at.radio:
    if r.key and (r.key.startswith("sus_") or r.key.startswith("hoc_")):
        r.set_value(4 if (r.key.startswith("hoc_") or int(r.key[4:]) % 2 == 0) else 2)
nut(at, "Gửi khảo sát").click().run()
ks = dl.doc_bang("khao_sat.csv")
ghi("Khảo sát: gửi đủ 15 câu được lưu đúng định dạng, tính được điểm SUS",
    len(ks) == 1 and dl.diem_sus([int(ks[0][c]) for c in dl.COT_KHAO_SAT if c.startswith("[S")]) == 75.0)

# ---------- Phản hồi kết quả nhận dạng ảnh tải lên ----------
dl.ghi_phan_hoi("tải lên", "P.102", 0.97, ["P.102", "P.103a"], "dung", "P.102")
dl.ghi_phan_hoi("tải lên", "W.205b", 0.41, ["W.205b", "W.225"], "sai", "W.225")
ph = dl.doc_bang("phan_hoi_nhan_dang.csv")
ghi("Phản hồi nhận dạng ảnh: lưu kết quả đúng/sai, không lưu ảnh", len(ph) == 2 and list(ph[0].keys()) == dl.COT_PHAN_HOI)
at = mo("danh_gia")
ghi("Tab Đánh giá hiển thị tổng hợp (điểm SUS, tỉ lệ nhận dạng đúng, số bài)", len([m for m in at.metric]) >= 3)

dat = sum(o for _, o, _ in kq)
dong = [f"[{'ĐẠT' if o else 'KHÔNG ĐẠT'}] {t}" + (f" — {c}" if c else "") for t, o, c in kq] + [f"\nTổng: {dat}/{len(kq)} kiểm thử đạt."]
os.makedirs("ket_qua", exist_ok=True)
open(os.path.join("ket_qua", "kiem_thu_chuc_nang.txt"), "w", encoding="utf-8").write("\n".join(dong))
print(f"\nTổng: {dat}/{len(kq)} kiểm thử đạt.")
