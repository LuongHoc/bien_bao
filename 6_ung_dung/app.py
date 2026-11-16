# -*- coding: utf-8 -*-
"""
app.py - May chu ung dung "Hoc bien bao giao thong".
Chay:  python app.py     -> mo trinh duyet tai http://127.0.0.1:5000
Chi lang nghe 127.0.0.1 (chi may nay truy cap duoc, chua public).
"""
import os, re, sys, time, json, glob, threading, webbrowser
from urllib.parse import quote
import numpy as np
import cv2
from flask import Flask, Response, abort, jsonify, redirect, render_template_string, request, send_from_directory, session

from bo_nhan_dang import BoNhanDang
from dotenv import load_dotenv
from datetime import timedelta
from admin import cau_hinh_admin
from auth import cau_hinh_dang_nhap
from database import DUONG_DAN_DB
from quiz import cau_hinh_bai_tap, phien_ban_ngan_hang
from learning import cau_hinh_thong_ke
from survey import cau_hinh_khao_sat

GOC = os.path.dirname(os.path.abspath(__file__))
DUONG_DAN_ENV = os.path.join(GOC, ".env")
# Nạp biến môi trường từ đường dẫn tuyệt đối với override=True
load_dotenv(DUONG_DAN_ENV, override=True)
MO_HINH = os.environ.get("MO_HINH", os.path.join(GOC, "..", "3_mo_hinh"))
TINH = os.path.join(GOC, "static")
CONG = int(os.environ.get("CONG", "5000"))
VI_DU = os.environ.get("VI_DU", os.path.join(GOC, "..", "1_du_lieu", "anh_tu_chup"))   # anh thuc te tu chup
NGUONG_PHAT_HIEN = float(os.environ.get("NGUONG_PHAT_HIEN", "0.35"))
DUOI_ANH = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
ANH_NEN = os.path.join(GOC, "anh_nen")    # anh nen trang chu: bo anh vao day, tu chuyen moi 10 giay


app = Flask(
    __name__,
    static_folder=TINH,
    static_url_path=""
)

# Gioi han dung luong anh tai len
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

# Khoa bi mat cho Flask Session
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

# Cau hinh cookie dang nhap
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Chi de False khi chay localhost bang HTTP
# Khi trien khai HTTPS, phai doi thanh True
app.config["SESSION_COOKIE_SECURE"] = False

# Thoi han phien dang nhap
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# Dang ky Google Login va SQLite
cau_hinh_dang_nhap(app)


try:
    nd = BoNhanDang(MO_HINH, nguong_phat_hien=NGUONG_PHAT_HIEN)
except Exception as e:  # thieu file mo hinh -> bao ro rang
    sys.exit(f"Khong nap duoc mo hinh trong {os.path.abspath(MO_HINH)}: {e}")


def ten_file_anh(ma):
    return ma.replace("(", "_").replace(")", "").replace(",", "_") + ".png"


THU_VIEN = os.path.join(GOC, "du_lieu", "thu_vien_bien.json")   # du bo bien bao QCVN 41:2024
CHI_TIET = os.path.join(GOC, "du_lieu", "chi_tiet_bien.json")      # cam doi tuong / pham vi / loai tru / luu y
BO_SUNG = os.path.join(GOC, "bo_sung_bien")   # anh nguoi dung them: dat ten file theo ma bien (vd R.E,9a.png)
# Bien co trong QCVN 41:2024 nhung bo anh mac dinh chua co: chi can them anh vao thu muc bo_sung_bien
BIEN_BO_SUNG = {
    "R.E,9a": ("Cấm đỗ xe trong khu vực", "Cấm đỗ xe trong toàn bộ khu vực kể từ vị trí đặt biển, đến biển hết khu vực R.E,10a."),
    "R.E,9b": ("Cấm đỗ xe theo giờ trong khu vực", "Cấm đỗ xe trong khu vực vào thời gian ghi trên biển, đến biển hết khu vực R.E,10b."),
    "R.E,9c": ("Khu vực đỗ xe", "Báo bắt đầu khu vực được phép đỗ xe, đến biển hết khu vực R.E,10c."),
    "R.E,9d": ("Tốc độ tối đa trong khu vực", "Các xe không được chạy quá tốc độ ghi trên biển trong toàn khu vực, đến biển hết khu vực R.E,10d."),
    "R.E,10a": ("Hết cấm đỗ xe trong khu vực", "Báo hết khu vực cấm đỗ xe đã đặt bằng biển R.E,9a."),
    "R.E,10b": ("Hết cấm đỗ xe theo giờ trong khu vực", "Báo hết khu vực cấm đỗ xe theo giờ đã đặt bằng biển R.E,9b."),
    "R.E,10c": ("Hết khu vực đỗ xe", "Báo hết khu vực được phép đỗ xe đã đặt bằng biển R.E,9c."),
    "R.E,10d": ("Hết tốc độ tối đa trong khu vực", "Báo hết khu vực hạn chế tốc độ tối đa đã đặt bằng biển R.E,9d."),
    "R.E,11a": ("Đường hầm", "Báo bắt đầu đoạn đường hầm; người lái xe phải tuân thủ các quy định khi đi trong hầm."),
    "R.E,11b": ("Kết thúc đường hầm", "Báo hết đoạn đường hầm."),
    "DP.127": ("Biển hết tốc độ tối đa cho phép theo biển ghép", "Báo hết hiệu lực của biển ghép tốc độ tối đa theo làn đường hoặc theo phương tiện (P.127b, P.127c)."),
    "R.301h": ("Hướng đi phải theo", "Các xe chỉ được đi theo hướng mũi tên vẽ trên biển."),
    "W.211": ("Giao nhau với đường sắt không có rào chắn", "Báo trước sắp đến chỗ giao nhau với đường sắt không có rào chắn; giảm tốc độ, quan sát kỹ hai phía trước khi qua."),
    "R.415": ("Biển gộp làn đường theo phương tiện", "Chỉ dẫn các làn đường được gộp lại theo loại phương tiện; người lái xe phải đi đúng làn quy định."),
}


# Ma theo quy chuan cu (khong con trong QCVN 41:2024) hoac ma gop: van hien trong thu vien, khong dua vao bai tap
MA_CU = {"I.428b", "I.428c", "I.437", "P.111", "P.127d", "P.127e", "R.301i", "R.415a", "R.415b", "S.510", "S.510b",
         "W.207j", "W.207m", "W.211a", "W.211b", "W.239"}


def ma_tu_ten_file(ten):
    """'R.E,9a.png', 'RE9a.png', 'R.E_9a.jpg', 'W.211.png', 'p102.png' -> ma bien chuan; khong doan duoc -> None."""
    goc = os.path.splitext(ten)[0].strip().replace(" ", "")
    m = re.fullmatch(r"(?i)R\.?E[,._]?(\d{1,2})([a-d])", goc)
    if m:
        return f"R.E,{int(m.group(1))}{m.group(2).lower()}"
    m = re.fullmatch(r"(?i)(DP|[PWRIS])[._]?(\d{3})([a-z]?)(?:[_(](\d{2,3})\)?)?", goc)
    if m:
        ma = f"{m.group(1).upper()}.{m.group(2)}{m.group(3).lower()}"
        return f"{ma}({int(m.group(4))})" if m.group(4) else ma
    return None


def anh_bo_sung():
    """{ma: url} cho anh trong thu muc bo_sung_bien (ghi de anh mac dinh neu trung ma)."""
    if not os.path.isdir(BO_SUNG):
        return {}
    kq = {}
    for f in sorted(os.listdir(BO_SUNG)):
        ma = ma_tu_ten_file(f) if f.lower().endswith(DUOI_ANH) else None
        if ma:
            kq[ma] = f"/anh-bo-sung/{quote(f)}?v={int(os.path.getmtime(os.path.join(BO_SUNG, f)))}"
    return kq


def khoa_sap_xep(ma):
    if ma.startswith("R.E,"):
        m = re.match(r"R\.E,(\d+)([a-z]?)", ma)
        return (2, 900 + int(m.group(1)), m.group(2), 0, ma)
    m = re.match(r"(DP|[PWRIS])\.(\d+)([a-z]?)(?:\((\d+)\))?", ma)
    thu = {"P": 0, "DP": 0, "W": 1, "R": 2, "I": 3, "S": 4}
    return (thu[m.group(1)], int(m.group(2)), m.group(3) or "", int(m.group(4) or 0), ma) if m else (9, 0, "", 0, ma)


def danh_sach_bien():
    """Thu vien = toan bo bien trong du_lieu/thu_vien_bien.json; bien AI nhan dang duoc lay noi dung tu 3_mo_hinh/y_nghia.json."""
    thu_vien = json.load(open(THU_VIEN, encoding="utf-8")) if os.path.isfile(THU_VIEN) else []
    theo_ma = {b["ma"]: dict(b) for b in thu_vien}
    ma_ai = [m for m in nd.lop if m != nd.lop_nen]
    them = anh_bo_sung()
    NHOM_THEO_KY = {"p": "Biển báo cấm", "w": "Biển báo nguy hiểm và cảnh báo", "r": "Biển hiệu lệnh", "i": "Biển chỉ dẫn", "s": "Biển phụ"}
    CAN_CU = {"p": "Điều 22, Phụ lục B", "w": "Điều 28, Phụ lục C", "r": "Điều 32, Phụ lục D", "i": "Điều 36, Phụ lục E", "s": "Điều 41, Phụ lục F"}
    for ma, url in them.items():
        if ma not in theo_ma:
            if ma not in BIEN_BO_SUNG:
                continue                                   # ten file khong khop ma nao da biet
            k = "p" if ma.startswith("DP") else ma[0].lower()
            ten, yn = BIEN_BO_SUNG[ma]
            theo_ma[ma] = {"ma": ma, "ten": ten, "y_nghia": yn, "nhom": NHOM_THEO_KY[k], "can_cu": f"QCVN 41:2024/BGTVT, {CAN_CU[k]}"}
        theo_ma[ma]["anh_url"] = url
    for ma in ma_ai:
        v = nd.y_nghia.get(ma, {})
        b = theo_ma.setdefault(ma, {"ma": ma, "ten": ma, "nhom": "Khác"})
        for k in ("ten", "nhom", "y_nghia", "dac_diem_nhom", "can_cu", "ghi_chu"):
            if v.get(k):
                b[k] = v[k]
        if v.get("y_nghia"):
            b.pop("y_nghia_tom_tat", None)
        if v.get("can_kiem_tra"):
            b["can_kiem_tra"] = True
    chi_tiet = json.load(open(CHI_TIET, encoding="utf-8")) if os.path.isfile(CHI_TIET) else {}
    for ma, ct in chi_tiet.items():
        b = theo_ma.get(ma)
        if not b:
            continue
        if ct.get("y_nghia") and (b.get("y_nghia_tom_tat") or not b.get("y_nghia")):
            b["y_nghia"] = ct["y_nghia"]
        b.pop("y_nghia_tom_tat", None)
        if ct.get("xac_minh"):                      # da doi chieu QCVN: bo canh bao can kiem tra
            b.pop("ghi_chu", None); b["can_kiem_tra"] = False
        b["chi_tiet"] = {k: v for k, v in ct.items() if k not in ("y_nghia", "xac_minh")}
    ds = []
    for ma in sorted(theo_ma, key=khoa_sap_xep):
        b = theo_ma[ma]
        f = b.get("anh_file") or ten_file_anh(ma)
        ds.append({"ma": ma, "ten": b.get("ten", ma), "nhom": b.get("nhom", "Khác"), "y_nghia": b.get("y_nghia", ""),
                   "dac_diem_nhom": b.get("dac_diem_nhom", ""), "can_cu": b.get("can_cu", ""), "ghi_chu": b.get("ghi_chu", ""),
                   "can_kiem_tra": bool(b.get("can_kiem_tra")), "y_nghia_tom_tat": bool(b.get("y_nghia_tom_tat")),
                   "nhan_dang": ma in ma_ai, "chi_tiet": b.get("chi_tiet"), "ma_cu": ma in MA_CU,
                   "anh": b.get("anh_url") or (f"/bien_chuan/{quote(f)}" if os.path.isfile(os.path.join(TINH, "bien_chuan", f)) else None)})
    return ds


BIEN = danh_sach_bien()
MA_HOP_LE = {b["ma"] for b in BIEN}

# Cùng nguồn dữ liệu chuẩn với /api/bien; không thay đổi tạo đề phía trình duyệt.
cau_hinh_bai_tap(app, danh_sach_bien)
cau_hinh_thong_ke(app, danh_sach_bien)
cau_hinh_khao_sat(app)
cau_hinh_admin(app, lay_danh_sach_bien_func=danh_sach_bien, ma_ai_classes=nd.lop)


def doc_ket_qua_mo_hinh():
    """Doc so lieu kiem thu cua mo hinh (neu co) de hien o trang Gioi thieu."""
    goc_kq = os.path.join(GOC, "..")
    tt = sorted(glob.glob(os.path.join(goc_kq, "4_ket_qua*", "**", "tom_tat.json"), recursive=True), key=os.path.getmtime)
    det = sorted(glob.glob(os.path.join(goc_kq, "4_ket_qua*", "**", "phat_hien_kiem_thu.json"), recursive=True), key=os.path.getmtime)
    kq = {}
    try:
        if tt:
            t = json.load(open(tt[-1], encoding="utf-8")); te = t.get("test") or {}
            kq["phan_loai"] = {"so_mau": te.get("so_mau"), "so_dung": te.get("so_dung"), "accuracy": te.get("accuracy"),
                               "macro_f1": te.get("macro_f1"), "tong_tham_so": t.get("tong_tham_so")}
        if det:
            kq["phat_hien"] = json.load(open(det[-1], encoding="utf-8"))
    except Exception:
        pass
    return kq


@app.get("/")
def trang_chu():
    return send_from_directory(TINH, "landing.html")


@app.get("/app")
@app.get("/app/")
def ung_dung():
    return send_from_directory(TINH, "index.html")


HTML_403_FORBIDDEN = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>403 - Quyền truy cập bị từ chối | Biển Báo AI</title>
    <link rel="icon" type="image/png" href="/anh/icon_bien_bao.png">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #F8FAFC;
            color: #0F172A;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 24px;
        }
        .error-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08);
            max-width: 520px;
            width: 100%;
            padding: 40px 32px;
            text-align: center;
        }
        .icon-shield {
            width: 72px;
            height: 72px;
            margin: 0 auto 20px;
            background: #FEE2E2;
            color: #DC2626;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
        }
        h1 { font-size: 24px; font-weight: 700; color: #0F172A; margin-bottom: 12px; }
        p { color: #64748B; font-size: 15px; line-height: 1.6; margin-bottom: 24px; }
        .user-tag {
            background: #F1F5F9;
            padding: 6px 14px;
            border-radius: 8px;
            font-weight: 600;
            color: #334155;
            display: inline-block;
            margin-bottom: 24px;
            font-size: 14px;
        }
        .actions {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px 20px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s ease;
            border: none;
        }
        .btn-primary { background: #2563EB; color: #FFFFFF; }
        .btn-primary:hover { background: #1D4ED8; }
        .btn-secondary { background: #F1F5F9; color: #334155; }
        .btn-secondary:hover { background: #E2E8F0; }
    </style>
</head>
<body>
    <div class="error-card">
        <div class="icon-shield">🛡️</div>
        <h1>403 - Quyền truy cập bị từ chối</h1>
        <p>Bảng điều khiển này được bảo vệ nghiêm ngặt và chỉ dành riêng cho tài khoản Quản trị viên (Admin).</p>
        <div class="user-tag">👤 Tài khoản: {{ user_email_or_name }} (Vai trò: Học viên)</div>
        <div class="actions">
            <a href="/app" class="btn btn-primary">Quay về ứng dụng học tập</a>
            <a href="/login?next=/admin" class="btn btn-secondary">Đăng nhập tài khoản Quản trị khác</a>
            <a href="/" class="btn btn-secondary">Về trang chủ</a>
        </div>
    </div>
</body>
</html>
"""


@app.get("/admin")
@app.get("/admin/")
def trang_admin():
    """Giao diện Bảng điều khiển Quản trị viên (Admin Dashboard)."""
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login?next=/admin")
    import database
    user = database.lay_nguoi_dung(user_id)
    if not user or user.get("status") != "active":
        return redirect("/login?next=/admin")
    if user.get("role") != "admin":
        return render_template_string(HTML_403_FORBIDDEN, user_email_or_name=user.get("email") or user.get("ten") or "Người học"), 403
    return send_from_directory(TINH, "admin.html")


@app.get("/landing")
def landing():
    return send_from_directory(TINH, "landing.html")


@app.get("/anh-bo-sung/<path:ten>")
def anh_bo_sung_file(ten):
    return send_from_directory(BO_SUNG, ten)


@app.get("/api/bien")
def api_bien():
    global BIEN, MA_HOP_LE
    BIEN = danh_sach_bien()                    # doc lai moi lan: them anh vao bo_sung_bien chi can F5
    MA_HOP_LE = {b["ma"] for b in BIEN}
    return jsonify({"bien": BIEN, "nhom": list(dict.fromkeys(b["nhom"] for b in BIEN)),
                    "nguong": nd.nguong, "quiz_bank_version": phien_ban_ngan_hang(BIEN)})


@app.get("/api/gioi_thieu")
def api_gioi_thieu():
    return jsonify({"so_bien": len(BIEN), "nguong": nd.nguong, "nguong_phat_hien": NGUONG_PHAT_HIEN,
                    "co_anh_phan_loai": nd.co, "co_anh_phat_hien": nd.det_sz, "ket_qua": doc_ket_qua_mo_hinh()})


@app.get("/api/anh_nen")
def api_anh_nen():
    """Danh sach anh nen trang chu (sap theo ten file). ?v= giup trinh duyet tai lai khi thay anh cung ten."""
    if not os.path.isdir(ANH_NEN):
        return jsonify([])
    fs = sorted(f for f in os.listdir(ANH_NEN) if f.lower().endswith(DUOI_ANH))[:10]
    return jsonify([f"/anh-nen/{quote(f)}?v={int(os.path.getmtime(os.path.join(ANH_NEN, f)))}" for f in fs])


_ANH_NEN_DA_THU_NHO = {}


@app.get("/anh-nen/<path:ten>")
def anh_nen(ten):
    """Tra anh nen da thu nho toi da 1920 px: anh dien thoai 4000 px rat nang, lam chuyen anh bi giat."""
    p = os.path.join(ANH_NEN, ten)
    if os.path.dirname(os.path.normpath(ten)) or not ten.lower().endswith(DUOI_ANH) or not os.path.isfile(p):
        abort(404)
    khoa = (ten, os.path.getmtime(p))
    if khoa not in _ANH_NEN_DA_THU_NHO:
        img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            abort(404)
        if img.shape[1] > 1920:
            img = cv2.resize(img, (1920, round(img.shape[0] * 1920 / img.shape[1])), interpolation=cv2.INTER_AREA)
        _ANH_NEN_DA_THU_NHO[khoa] = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 88])[1].tobytes()
    return Response(_ANH_NEN_DA_THU_NHO[khoa], mimetype="image/jpeg", headers={"Cache-Control": "max-age=86400"})


@app.get("/api/vi_du/<path:ma>")
def api_vi_du(ma):
    """Anh thuc te cua bien lay tu thu muc anh tu chup (1_du_lieu/anh_tu_chup/<ma>/)."""
    d = os.path.join(VI_DU, ma)
    if ma not in MA_HOP_LE or not os.path.isdir(d):
        return jsonify([])
    fs = sorted(f for f in os.listdir(d) if f.lower().endswith(DUOI_ANH))[:4]
    return jsonify([f"/anh-vi-du/{quote(ma)}/{quote(f)}" for f in fs])


@app.get("/anh-vi-du/<path:ma>/<path:ten>")
def anh_vi_du(ma, ten):
    if ma not in MA_HOP_LE:
        abort(404)
    return send_from_directory(os.path.join(VI_DU, ma), ten)


@app.post("/api/nhan_dang")
def api_nhan_dang():
    f = request.files.get("anh")
    du_lieu = f.read() if f else request.get_data()
    if not du_lieu:
        return jsonify({"loi": "Chưa có ảnh gửi lên."}), 400
    img = cv2.imdecode(np.frombuffer(du_lieu, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"loi": "Không đọc được ảnh. Hãy dùng ảnh JPG hoặc PNG."}), 400
    t0 = time.perf_counter()
    kq = nd.xu_ly(img)
    return jsonify({"rong": img.shape[1], "cao": img.shape[0], "ket_qua": kq,
                    "thoi_gian_ms": round((time.perf_counter() - t0) * 1000, 1)})


@app.errorhandler(413)
def qua_lon(_):
    return jsonify({"loi": "Ảnh lớn hơn 25 MB. Hãy chọn ảnh nhỏ hơn."}), 413


if __name__ == "__main__":
    dia_chi = f"http://localhost:{CONG}"
    print(f"Mo hinh: {os.path.abspath(MO_HINH)} | {len(BIEN)} bien | nguong {nd.nguong}")
    print(f"SQLite: {DUONG_DAN_DB} | Luu bai tap: POST /api/quiz/submit")
    print(f"Mo trinh duyet tai {dia_chi}  (Ctrl+C de tat)")
    if "--khong_mo" not in sys.argv:
        threading.Timer(1.2, lambda: webbrowser.open(dia_chi)).start()
    app.run(host="127.0.0.1", port=CONG, threaded=True, debug=False)
