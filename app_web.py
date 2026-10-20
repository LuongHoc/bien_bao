"""
ỨNG DỤNG WEB TRỢ GIÚP NGƯỜI HỌC NHẬN DẠNG BIỂN BÁO GIAO THÔNG
Dùng chung mạng nơron (mlp.py), tiền xử lý (tien_xu_ly.py) và mô hình đã huấn luyện với bản máy tính.
Chạy trên máy:   streamlit run app_web.py
Mở được trên cả máy tính và điện thoại (trình duyệt).
"""
import os
import json
import glob
import random
import time
import streamlit.components.v1 as components
import numpy as np
import cv2
import streamlit as st
from PIL import Image, ImageOps
from mlp import MangNoron
from tien_xu_ly import tien_xu_ly

try:
    from streamlit_cropper import st_cropper
    CO_KHOANH_VUNG = True
except ImportError:
    CO_KHOANH_VUNG = False

GOC = os.path.dirname(os.path.abspath(__file__))
NGUONG_TIN_CAY = 0.5

st.set_page_config(page_title="Học biển báo giao thông", page_icon="🚦", layout="wide")

# ---------------- Giao diện: màu sắc lấy từ chính biển báo (đỏ cấm, xanh hiệu lệnh, vàng cảnh báo) ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
:root { --chinh:#0B3D91; --chinh-nhat:#E8EEF9; --do:#E03131; --vang:#F5B800; --xanh:#1C64F2;
        --chu:#1F2937; --phu:#6B7280; --nen:#F4F6FA; --the:#FFFFFF; --vien:#E5E9F0; }
html, body, .stApp, .stMarkdown, button, input, label, p, h1, h2, h3, h4, h5 {
  font-family: 'Be Vietnam Pro', 'Segoe UI', Arial, sans-serif !important; }
.stApp { background: var(--nen); color: var(--chu); }
header[data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none !important; }
.block-container { max-width: 1180px; padding-top: 1.4rem; padding-bottom: 3rem; }

/* ---------- Thanh đầu trang ---------- */
.dau-trang { background: var(--the); border: 1px solid var(--vien); border-radius: 18px; overflow: hidden;
             box-shadow: 0 8px 24px rgba(15, 35, 80, .06); margin-bottom: 1.2rem; }
.dau-trang .vach { height: 6px; background: linear-gradient(90deg, var(--do) 0 33.3%, var(--vang) 33.3% 66.6%, var(--xanh) 66.6% 100%); }
.dau-trang .noi-dung { display: flex; align-items: center; gap: 1.1rem; padding: 1.1rem 1.5rem; flex-wrap: wrap; }
.logo { width: 54px; height: 54px; border-radius: 50%; border: 7px solid var(--do); background: #fff;
        display: grid; place-items: center; font-weight: 800; color: var(--chu); font-size: 1.05rem; flex-shrink: 0; }
.dau-trang h1 { font-size: 1.75rem !important; font-weight: 800 !important; color: var(--chinh) !important;
                margin: 0 !important; padding: 0 !important; line-height: 1.2 !important; }
.dau-trang p { margin: .2rem 0 0; color: var(--phu); font-size: .95rem; }
.chip-tk { margin-left: auto; display: flex; gap: .5rem; flex-wrap: wrap; }
.chip-tk span { background: var(--chinh-nhat); color: var(--chinh); font-weight: 600; font-size: .85rem;
                padding: .35rem .75rem; border-radius: 999px; }

/* ---------- Thanh chuyển mục ---------- */
.stTabs [role="tablist"] { background: var(--the); border: 1px solid var(--vien); border-radius: 14px;
        padding: .35rem; gap: .3rem; display: flex; flex-wrap: wrap; box-shadow: none; }
.stTabs [data-testid="stTab"] { border-radius: 10px !important; padding: .55rem 1.2rem !important; cursor: pointer; }
.stTabs [data-testid="stTab"] p { font-weight: 600 !important; font-size: .98rem !important; color: var(--phu) !important; }
.stTabs [data-testid="stTab"]:hover p { color: var(--chinh) !important; }
.stTabs [data-testid="stTab"][aria-selected="true"] { background: var(--chinh) !important; }
.stTabs [data-testid="stTab"][aria-selected="true"] p { color: #fff !important; }
.stTabs .react-aria-SelectionIndicator, .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-testid="stTabPanel"], .stTabs [role="tabpanel"] { padding-top: 1rem; }

/* ---------- Nút, nút chọn nhanh, ô nhập ---------- */
[data-testid="stBaseButton-primary"] { background: var(--chinh) !important; border-color: var(--chinh) !important;
        color: #fff !important; border-radius: 10px !important; font-weight: 600 !important; }
[data-testid="stBaseButton-primary"]:hover { filter: brightness(1.12); }
[data-testid="stBaseButton-secondary"] { border-radius: 10px !important; border-color: var(--vien) !important; background: #fff !important; }
[data-testid="stBaseButton-secondary"]:hover { border-color: var(--chinh) !important; color: var(--chinh) !important; }
[data-testid="stButtonGroup"] button { border-radius: 999px !important; border-color: var(--vien) !important; background: #fff !important; }
[data-testid="stButtonGroup"] button[aria-checked="true"] { background: var(--chinh) !important; border-color: var(--chinh) !important; }
[data-testid="stButtonGroup"] button[aria-checked="true"] p, [data-testid="stButtonGroup"] button[aria-checked="true"] span { color: #fff !important; }
[data-testid="stTextInput"] input { border-radius: 10px; background: #fff; }
[data-testid="stTextInput"] > div > div { border-radius: 10px; border: 1px solid var(--vien); background: #fff; }
[data-testid="stProgress"] div[role="progressbar"] > div > div > div { background: var(--chinh) !important; }
button:focus-visible { outline: 3px solid var(--vang) !important; outline-offset: 2px; }

/* ---------- Lưới thư viện biển ---------- */
.st-key-luoi_bien [data-testid="stColumn"] { background: var(--the); border: 1px solid var(--vien); border-radius: 16px;
        padding: .75rem .75rem .8rem; box-shadow: 0 2px 8px rgba(15, 35, 80, .04); transition: transform .15s, box-shadow .15s; }
.st-key-luoi_bien [data-testid="stColumn"]:hover { transform: translateY(-3px); box-shadow: 0 10px 22px rgba(15, 35, 80, .10); }
.st-key-luoi_bien img { max-height: 112px; object-fit: contain; }
.nhan-nhom { display: inline-flex; align-items: center; gap: .35rem; font-size: .72rem; font-weight: 600;
             color: var(--phu); background: var(--nen); border-radius: 999px; padding: .15rem .55rem; margin-bottom: .45rem; }
.nhan-nhom i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.ten-bien { font-size: .9rem; font-weight: 600; line-height: 1.3; color: var(--chu); height: 3.9em; overflow: hidden;
            display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; margin: .5rem 0 .55rem; text-align: center; }
.st-key-luoi_bien [data-testid="stBaseButton-secondary"] { background: var(--chinh-nhat) !important; border: none !important;
        color: var(--chinh) !important; font-weight: 600 !important; }
.st-key-luoi_bien [data-testid="stBaseButton-secondary"]:hover { background: var(--chinh) !important; color: #fff !important; }
.so-luong { color: var(--phu); font-size: .93rem; margin: .2rem 0 .6rem; }
[class*="st-key-phan_trang"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .35rem; justify-content: center; }
[class*="st-key-phan_trang"] [data-testid="stColumn"] { flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }
[class*="st-key-phan_trang"] button { min-width: 2.6rem; padding: .25rem .7rem; font-weight: 600; }
.st-key-phan_trang_duoi { margin-top: 1rem; }
@media (max-width: 640px) {
  .dau-trang h1 { font-size: 1.35rem !important; } .chip-tk { margin-left: 0; }
  .st-key-luoi_bien [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .5rem; }
  .st-key-luoi_bien [data-testid="stColumn"] { flex: 1 1 calc(50% - .5rem) !important; min-width: calc(50% - .5rem) !important; }
}

/* ---------- Khung chi tiết biển ---------- */
[data-testid="stDialog"] h3 { font-weight: 700 !important; color: var(--chinh) !important; }
[data-testid="stDialog"] img { max-width: 240px; margin: 0 auto; display: block; }
.the-y-nghia { background: var(--nen); border-left: 5px solid var(--chinh); border-radius: 0 12px 12px 0; padding: .9rem 1.1rem; margin-top: .6rem; }

/* ---------- Luyện tập ---------- */
.st-key-cau_hoi { background: var(--the); border: 1px solid var(--vien); border-radius: 18px; padding: 1.2rem 1.4rem;
                  box-shadow: 0 8px 24px rgba(15, 35, 80, .06); }
.st-key-cau_hoi [data-testid="stBaseButton-secondary"] { justify-content: flex-start !important; text-align: left;
        padding: .7rem 1rem !important; font-size: 1rem; min-height: 3rem; }
.st-key-cau_hoi [data-testid="stBaseButton-secondary"] p { font-size: 1rem; }
[data-testid="stForm"] { padding: 0 !important; }
[data-testid="stBaseButton-primaryFormSubmit"] { background: var(--chinh) !important; border-color: var(--chinh) !important;
        color: #fff !important; border-radius: 10px !important; font-weight: 600 !important; min-height: 2.6rem; }
.st-key-cau_hoi [data-testid="stBaseButton-secondary"] > div { justify-content: flex-start !important; width: 100%; }
[data-testid="stElementToolbar"] { display: none !important; }
[data-testid="stMetric"] { background: var(--the); border: 1px solid var(--vien); border-radius: 14px; padding: .7rem 1rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def nap_du_lieu():
    mang = MangNoron.nap(os.path.join(GOC, "mo_hinh", "mlp.npz"))
    with open(os.path.join(GOC, "bien_bao.json"), encoding="utf-8") as f:
        bien_bao = json.load(f)
    anh_mau = {}
    for p in sorted(glob.glob(os.path.join(GOC, "anh_mau", "*"))):
        ma = os.path.basename(p).split("_")[0]
        if ma.isdigit():
            anh_mau.setdefault(str(int(ma)), []).append(p)
    ma = {}
    tep_lop = os.path.join(GOC, "lop.json")
    if os.path.exists(tep_lop):
        ma = {str(l["id"]): l["ma"] for l in json.load(open(tep_lop, encoding="utf-8"))}
    return mang, bien_bao, anh_mau, ma


mang, BIEN_BAO, ANH_MAU, MA_BIEN = nap_du_lieu()
CAC_LOP = sorted(ANH_MAU.keys(), key=int)  # chỉ các loại biển mạng đã được học


NHOM_THEO_MA = [("DP", "Biển báo cấm"), ("P", "Biển báo cấm"), ("R", "Biển hiệu lệnh"),
                ("W", "Biển báo nguy hiểm và cảnh báo"), ("I", "Biển chỉ dẫn"), ("S", "Biển phụ")]
MAU_NHOM = {"Biển báo cấm": "#E03131", "Biển hiệu lệnh": "#1C64F2", "Biển báo nguy hiểm và cảnh báo": "#F5B800",
            "Biển chỉ dẫn": "#0B3D91", "Biển phụ": "#9CA3AF"}
TEN_NGAN_NHOM = {"Biển báo cấm": "Biển cấm", "Biển hiệu lệnh": "Hiệu lệnh", "Biển báo nguy hiểm và cảnh báo": "Cảnh báo",
                 "Biển chỉ dẫn": "Chỉ dẫn", "Biển phụ": "Biển phụ"}
THU_TU_NHOM = ["Biển báo cấm", "Biển hiệu lệnh", "Biển báo nguy hiểm và cảnh báo", "Biển chỉ dẫn", "Biển phụ"]


def nhom_cua(m):
    """Nhóm biển theo QCVN 41 (xác định từ mã biển)."""
    ma = MA_BIEN.get(m, thong_tin(m)["ten"].split(" ")[0])
    for tien_to, ten in NHOM_THEO_MA:
        if ma.startswith(tien_to + "."):
            return ten
    return thong_tin(m)["nhom"]


def ten_bien(m):
    """Tên biển dễ hiểu cho người học (bỏ ký hiệu mã ở đầu)."""
    return thong_tin(m)["ten"].split(" - ", 1)[-1]


def ky_hieu(m):
    return MA_BIEN.get(m) or thong_tin(m)["ten"].split(" - ", 1)[0]


def thong_tin(ma):
    return BIEN_BAO.get(ma, {"ten": f"Loại {ma}", "nhom": "?", "dac_diem": "?", "y_nghia": "Chưa có mô tả."})


def nhan_dang(anh_pil):
    bgr = cv2.cvtColor(np.array(anh_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
    xac_suat = mang.du_doan_xac_suat(tien_xu_ly(bgr))[0]
    return xac_suat.argsort()[::-1], xac_suat


def hien_ket_qua(anh_pil):
    thu_tu, xac_suat = nhan_dang(anh_pil)
    ma, p = str(int(thu_tu[0])), float(xac_suat[thu_tu[0]])
    tt = thong_tin(ma)
    cot1, cot2 = st.columns([1, 2])
    with cot1:
        st.image(anh_pil, caption="Vùng được nhận dạng", width="stretch")
    with cot2:
        st.subheader(tt["ten"].split(" - ", 1)[-1])
        st.caption(f"Ký hiệu theo QCVN 41:2024: {tt['ten'].split(' - ', 1)[0]}")
        if p >= NGUONG_TIN_CAY:
            st.success(f"Độ tin cậy: {p * 100:.1f}%")
        else:
            st.warning(f"Độ tin cậy thấp ({p * 100:.1f}%). Hãy khoanh sát biển báo hơn, "
                       "hoặc biển này có thể chưa có trong dữ liệu đã học.")
    st.markdown(f"**Nhóm:** {nhom_cua(ma)}")
    st.markdown(f"**Đặc điểm:** {tt['dac_diem']}")
    st.markdown(f"**Ý nghĩa:** {tt['y_nghia']}")
    with st.expander("Các khả năng khác"):
        for k in thu_tu[1:4]:
            st.write(f"{thong_tin(str(int(k)))['ten']}: {xac_suat[k] * 100:.1f}%")


# ======================= GIAO DIỆN =======================
st.markdown(f"""
<div class="dau-trang"><div class="vach"></div><div class="noi-dung">
  <div class="logo">50</div>
  <div><h1>Học biển báo giao thông</h1></div>
</div></div>""", unsafe_allow_html=True)

tab_tv, tab_nd, tab_lt = st.tabs(["📚  Thư viện biển báo", "📷  Nhận dạng ảnh", "✏️  Luyện tập"])


@st.dialog("Thông tin biển báo", width="large")
def xem_bien(m):
    """Người học chọn một biển -> mạng nơron nhận dạng ảnh đó -> hiển thị ý nghĩa."""
    anh = Image.open(ANH_MAU[m][0]).convert("RGB")
    thu_tu, xac_suat = nhan_dang(anh)
    kq, p = str(int(thu_tu[0])), float(xac_suat[thu_tu[0]])
    tt = thong_tin(kq)
    c1, c2 = st.columns([1, 2])
    c1.image(anh, width="stretch")
    with c2:
        st.subheader(tt["ten"].split(" - ", 1)[-1])
        st.caption(f"Ký hiệu theo QCVN 41:2024: {tt['ten'].split(' - ', 1)[0]}")
        st.caption(f"🧠 Kết quả nhận dạng của mạng nơron — độ tin cậy {p * 100:.1f}%")
        if kq != m:
            st.warning(f"Mạng nơron nhận dạng chưa đúng. Biển đúng là: {ten_bien(m)}")
            tt = thong_tin(m)
    st.markdown(f"""<div class="the-y-nghia"><p><b>Nhóm:</b> {nhom_cua(m)}</p>
<p><b>Đặc điểm:</b> {tt['dac_diem']}</p><p style="margin-bottom:0"><b>Ý nghĩa:</b> {tt['y_nghia']}</p></div>""",
                unsafe_allow_html=True)


# ---------- Tab 1: Thư viện biển báo ----------
with tab_tv:
    BIEU_TUONG = {"Biển báo cấm": "🔴", "Biển hiệu lệnh": "🔵", "Biển báo nguy hiểm và cảnh báo": "🟡",
                  "Biển chỉ dẫn": "🟦", "Biển phụ": "⬜"}
    co_nhom = [n for n in THU_TU_NHOM if any(nhom_cua(m) == n for m in CAC_LOP)]
    nhom = st.pills("Nhóm biển báo", ["Tất cả"] + co_nhom, default="Tất cả",
                    format_func=lambda n: n if n == "Tất cả" else f"{BIEU_TUONG.get(n, '')} {n}")
    # Ô tìm kiếm + nút kính lúp (bấm nút hoặc nhấn Enter để tìm)
    with st.form("tim_kiem", border=False):
        o_tim, nut_tim = st.columns([6, 1], vertical_alignment="bottom")
        nhap = o_tim.text_input("Tìm biển", placeholder="Gõ tên hoặc mã biển, ví dụ: trẻ em, P.102",
                                label_visibility="collapsed")
        if nut_tim.form_submit_button("Tìm", icon=":material/search:", type="primary", width="stretch"):
            st.session_state.tu_khoa = nhap.strip().lower()
    tu_khoa = st.session_state.get("tu_khoa", "")
    if tu_khoa:
        c_kq, c_xoa = st.columns([6, 1], vertical_alignment="center")
        c_kq.markdown(f'<p class="so-luong">Kết quả tìm kiếm cho “<b>{tu_khoa}</b>”</p>', unsafe_allow_html=True)
        if c_xoa.button("Xóa tìm kiếm", icon=":material/close:", width="stretch"):
            st.session_state.tu_khoa = ""
            st.rerun()
    nhom = nhom or "Tất cả"
    ds = [m for m in CAC_LOP if (nhom == "Tất cả" or nhom_cua(m) == nhom)
          and (not tu_khoa or tu_khoa in thong_tin(m)["ten"].lower())]
    MOI_TRANG, SO_COT = 30, 6
    so_trang = max(1, (len(ds) + MOI_TRANG - 1) // MOI_TRANG)
    if not ds:
        st.info("Không có biển nào khớp. Thử gõ ít chữ hơn hoặc chọn nhóm khác.")
    else:
        st.markdown(f'<p class="so-luong">{len(ds)} biển. Bấm <b>Xem ý nghĩa</b> dưới một biển để mạng nơron nhận dạng và giải thích biển đó.</p>',
                    unsafe_allow_html=True)
    # ----- Phân trang dạng  ‹ 1 2 3 … 12 › -----
    khoa = f"trang_{nhom}_{tu_khoa}"
    trang = min(max(1, st.session_state.get(khoa, 1)), so_trang)

    def muc_trang(hien, tong):
        """Danh sách số trang cần hiện; None là dấu '…'."""
        if tong <= 7:
            return list(range(1, tong + 1))
        chon = {1, tong, hien - 1, hien, hien + 1}
        if hien <= 3:
            chon |= {2, 3, 4}
        if hien >= tong - 2:
            chon |= {tong - 3, tong - 2, tong - 1}
        ket_qua, truoc = [], 0
        for p in sorted(p for p in chon if 1 <= p <= tong):
            if p - truoc > 1:
                ket_qua.append(None)
            ket_qua.append(p)
            truoc = p
        return ket_qua

    def ve_phan_trang(vi_tri):
        if so_trang <= 1:
            return
        muc = ["‹"] + muc_trang(trang, so_trang) + ["›"]
        with st.container(key=f"phan_trang_{vi_tri}"):
            for i, (cot, m) in enumerate(zip(st.columns(len(muc)), muc)):
                k = f"{khoa}_{vi_tri}_{i}"
                if m is None:
                    cot.button("…", key=k, disabled=True)
                elif m in ("‹", "›"):
                    moi = trang - 1 if m == "‹" else trang + 1
                    if cot.button(m, key=k, disabled=not 1 <= moi <= so_trang,
                                  help="Trang trước" if m == "‹" else "Trang sau"):
                        st.session_state[khoa] = moi
                        st.rerun()
                elif cot.button(str(m), key=k, type="primary" if m == trang else "secondary"):
                    st.session_state[khoa] = m
                    st.rerun()

    ve_phan_trang("tren")
    with st.container(key="luoi_bien"):
        trang_nay = ds[(trang - 1) * MOI_TRANG: trang * MOI_TRANG]
        for hang in range(0, len(trang_nay), SO_COT):
            cot = st.columns(SO_COT)
            for k, m in enumerate(trang_nay[hang: hang + SO_COT]):
                with cot[k]:
                    st.image(ANH_MAU[m][0], width="stretch")
                    ten = ten_bien(m)
                    st.markdown(f'<div class="ten-bien" title="{ten}">{ten}</div>', unsafe_allow_html=True)
                    if st.button("Xem ý nghĩa", key=f"xem_{m}", width="stretch", help=f"Ký hiệu: {ky_hieu(m)}"):
                        xem_bien(m)
    ve_phan_trang("duoi")

# ---------- Tab 2: Nhận dạng ảnh ----------
with tab_nd:
    st.write("Tải lên hoặc chụp ảnh một biển báo để mạng nơron nhận dạng.")
    nguon = st.radio("Nguồn ảnh", ["Tải ảnh lên / chụp bằng điện thoại", "Dùng webcam"], horizontal=True)
    if nguon.startswith("Tải"):
        tep = st.file_uploader("Chọn ảnh biển báo (trên điện thoại có thể chọn Máy ảnh để chụp trực tiếp)",
                               type=["jpg", "jpeg", "png", "bmp", "webp"])
    else:
        tep = st.camera_input("Chụp ảnh biển báo")

    if tep is not None:
        anh = ImageOps.exif_transpose(Image.open(tep)).convert("RGB")  # xoay đúng chiều ảnh điện thoại
        if CO_KHOANH_VUNG:
            st.info("Kéo và chỉnh khung vàng cho sát quanh biển báo, kết quả sẽ tự cập nhật.")
            vung = st_cropper(anh, realtime_update=True, box_color="#FFCC00", aspect_ratio=None)
        else:
            vung = anh
        st.divider()
        hien_ket_qua(vung)

# ---------- Tab 3: Luyện tập ----------
SO_CAU_MOI_DE = 25
THOI_GIAN_DE = 15 * 60          # 15 phút cho mỗi bộ đề
NGUONG_DAT = 0.8                # đúng từ 80% trở lên là Đạt


def chon_dap_an_nhieu(dung, rng):
    """Chọn 3 đáp án nhiễu: ưu tiên cùng nhóm, KHÔNG trùng tên với nhau và với đáp án đúng."""
    ten_da_co = {ten_bien(dung)}
    nhieu = []
    cung_nhom = [m for m in CAC_LOP if m != dung and nhom_cua(m) == nhom_cua(dung)]
    khac = [m for m in CAC_LOP if m != dung and nhom_cua(m) != nhom_cua(dung)]
    rng.shuffle(cung_nhom)
    rng.shuffle(khac)
    for m in cung_nhom + khac:
        if len(nhieu) == 3:
            break
        if ten_bien(m) not in ten_da_co:
            nhieu.append(m)
            ten_da_co.add(ten_bien(m))
    return nhieu


def tao_cau(dung, rng, co_cau_chon_hinh):
    lua_chon = chon_dap_an_nhieu(dung, rng) + [dung]
    rng.shuffle(lua_chon)
    dang = "chon_hinh" if co_cau_chon_hinh and rng.random() < 0.35 else "chon_ten"
    return {"dung": dung, "lua_chon": lua_chon, "dang": dang, "tra_loi": None}


def danh_sach_de():
    """Chia toàn bộ biển thành các bộ đề cố định (cùng một cách chia cho mọi người dùng)."""
    ds = CAC_LOP[:]
    random.Random(2024).shuffle(ds)
    return [ds[i:i + SO_CAU_MOI_DE] for i in range(0, len(ds), SO_CAU_MOI_DE)]


def bat_dau_bai(ten, cac_bien, co_cau_chon_hinh, thoi_gian=None, la_de=False, seed=None):
    rng = random.Random(seed)
    st.session_state.bai = {
        "ten": ten, "la_de": la_de, "hien": 0, "xong": False,
        "han": time.time() + thoi_gian if thoi_gian else None,
        "cau": [tao_cau(m, rng, co_cau_chon_hinh) for m in cac_bien],
        "tham_so": (ten, cac_bien, co_cau_chon_hinh, thoi_gian, la_de, seed),
    }


def ghi_ket_qua(cau, chon):
    """Ghi câu trả lời (hoặc 'bo_qua'), cập nhật thống kê và danh sách câu sai."""
    ss = st.session_state
    if cau["tra_loi"] is not None:
        return
    cau["tra_loi"] = chon
    nhom = nhom_cua(cau["dung"])
    tk = ss.thong_ke.setdefault(nhom, [0, 0])
    tk[1] += 1
    if chon == cau["dung"]:
        tk[0] += 1
        ss.cau_sai.discard(cau["dung"])
    else:
        ss.cau_sai.add(cau["dung"])


def het_gio(bai):
    return bai["han"] is not None and time.time() > bai["han"]


def ket_thuc(bai):
    for c in bai["cau"]:
        ghi_ket_qua(c, "bo_qua")
    bai["xong"] = True


def dong_ho(han):
    con_lai_ms = int(max(0, han - time.time()) * 1000)
    html = f"""
    <div id="dh" style="font:700 18px 'Be Vietnam Pro', Arial, sans-serif;color:#1F2937;text-align:right"></div>
    <script>
      const het = Date.now() + {con_lai_ms};
      function ve() {{
        const s = Math.max(0, Math.round((het - Date.now()) / 1000));
        const el = document.getElementById('dh');
        el.textContent = '⏱ ' + String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
        el.style.color = s <= 60 ? '#E03131' : '#1F2937';
        if (s > 0) setTimeout(ve, 500); else el.textContent = '⏱ Hết giờ – bấm câu tiếp theo để xem kết quả';
      }}
      ve();
    </script>"""
    if hasattr(st, "iframe"):          # Streamlit bản mới
        st.iframe(html, height=34)
    else:                              # Streamlit bản cũ
        components.html(html, height=34)


def ve_ket_qua(bai):
    so_cau = len(bai["cau"])
    dung = sum(c["tra_loi"] == c["dung"] for c in bai["cau"])
    bo_qua = sum(c["tra_loi"] == "bo_qua" for c in bai["cau"])
    st.subheader(f"Kết quả: {bai['ten']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Số câu đúng", f"{dung} / {so_cau}")
    c2.metric("Số câu sai", so_cau - dung - bo_qua)
    c3.metric("Bỏ qua / hết giờ", bo_qua)
    if bai["la_de"]:
        if dung >= NGUONG_DAT * so_cau:
            st.success(f"🎉 ĐẠT – bạn trả lời đúng {dung}/{so_cau} câu (yêu cầu từ {int(NGUONG_DAT * 100)}%).")
        else:
            st.error(f"CHƯA ĐẠT – bạn trả lời đúng {dung}/{so_cau} câu (yêu cầu từ {int(NGUONG_DAT * 100)}%). Hãy ôn lại các câu sai bên dưới.")
    sai = [c for c in bai["cau"] if c["tra_loi"] != c["dung"]]
    if sai:
        st.markdown("#### Các câu chưa đúng")
        for c in sai:
            a, b = st.columns([1, 4])
            a.image(ANH_MAU[c["dung"]][0], width=90)
            ban_chon = "Bỏ qua" if c["tra_loi"] == "bo_qua" else ten_bien(c["tra_loi"])
            b.markdown(f"**Đáp án đúng:** {ten_bien(c['dung'])}  \nBạn chọn: {ban_chon}  \n"
                       f"<span style='color:#5B6168'>{thong_tin(c['dung'])['y_nghia']}</span>", unsafe_allow_html=True)
    k1, k2 = st.columns(2)
    if k1.button("🔁 Làm lại bài này", width="stretch"):
        t = bai["tham_so"]
        bat_dau_bai(*t[:5], seed=random.random())
        st.rerun()
    if k2.button("🏠 Về màn hình chọn bài", width="stretch"):
        st.session_state.bai = None
        st.rerun()


def ve_cau_hoi(bai):
    with st.container(key="cau_hoi"):
        _ve_cau_hoi(bai)


def _ve_cau_hoi(bai):
    i = bai["hien"]
    cau = bai["cau"][i]
    so_cau = len(bai["cau"])
    dung_tam = sum(c["tra_loi"] == c["dung"] for c in bai["cau"][:i + 1])
    t1, t2 = st.columns([3, 1])
    t1.markdown(f"**{bai['ten']}** · Câu {i + 1}/{so_cau} · Đúng: {dung_tam}")
    if bai["han"]:
        with t2:
            dong_ho(bai["han"])
    st.progress((i + (cau["tra_loi"] is not None)) / so_cau)
    da_tl = cau["tra_loi"] is not None
    nhan = "ABCD"

    if cau["dang"] == "chon_ten":
        st.image(ANH_MAU[cau["dung"]][0], width=200)
        st.markdown("##### Đây là biển báo gì?")
        for k, m in enumerate(cau["lua_chon"]):
            nhan_nut = f"{nhan[k]}.  {ten_bien(m)}"
            if not da_tl:
                if st.button(nhan_nut, key=f"tl_{id(bai)}_{i}_{k}", width="stretch"):
                    ghi_ket_qua(cau, m)
                    st.rerun()
            else:
                dau = "✅" if m == cau["dung"] else ("❌" if m == cau["tra_loi"] else "▫️")
                st.markdown(f"{dau} {nhan_nut}")
    else:
        st.markdown(f"##### Biển **“{ten_bien(cau['dung'])}”** là biển nào?")
        cot = st.columns(4)
        for k, m in enumerate(cau["lua_chon"]):
            with cot[k]:
                st.image(ANH_MAU[m][0], width="stretch")
                if not da_tl:
                    if st.button(nhan[k], key=f"tl_{id(bai)}_{i}_{k}", width="stretch"):
                        ghi_ket_qua(cau, m)
                        st.rerun()
                else:
                    st.markdown("✅ Đúng" if m == cau["dung"] else ("❌ Bạn chọn" if m == cau["tra_loi"] else "&nbsp;"),
                                unsafe_allow_html=True)

    if da_tl:
        tt = thong_tin(cau["dung"])
        if cau["tra_loi"] == cau["dung"]:
            st.success(f"Chính xác! {ten_bien(cau['dung'])} (ký hiệu {ky_hieu(cau['dung'])}).")
        elif cau["tra_loi"] == "bo_qua":
            st.warning(f"Bạn đã bỏ qua câu này. Đáp án: {ten_bien(cau['dung'])}.")
        else:
            st.error(f"Chưa đúng. Đáp án đúng là {nhan[cau['lua_chon'].index(cau['dung'])]}. {ten_bien(cau['dung'])}.")
        st.info(f"**Ý nghĩa:** {tt['y_nghia']}")

    n1, n2 = st.columns(2)
    cuoi = i == so_cau - 1
    if n1.button("Xem kết quả ✔" if cuoi else ("Câu tiếp theo ➜" if da_tl else "Bỏ qua câu này ➜"),
                 width="stretch", type="primary" if da_tl else "secondary"):
        ghi_ket_qua(cau, "bo_qua")
        if cuoi:
            ket_thuc(bai)
        else:
            bai["hien"] += 1
        st.rerun()
    if n2.button("Nộp bài / kết thúc", width="stretch"):
        ket_thuc(bai)
        st.rerun()


def ve_chon_bai():
    ss = st.session_state
    che_do = st.segmented_control("Chọn cách luyện tập", ["📝 Thi thử theo bộ đề", "🎯 Luyện theo nhóm biển", "🔁 Ôn lại câu sai"],
                                  default="📝 Thi thử theo bộ đề") or "📝 Thi thử theo bộ đề"
    co_chon_hinh = st.checkbox("Có cả câu hỏi dạng “cho tên biển, chọn hình đúng”", value=True)

    if che_do.startswith("📝"):
        de = danh_sach_de()
        st.write(f"Toàn bộ {len(CAC_LOP)} biển được chia thành **{len(de)} bộ đề**, mỗi đề tối đa "
                 f"{SO_CAU_MOI_DE} câu, làm trong **{THOI_GIAN_DE // 60} phút**. "
                 f"Đúng từ {int(NGUONG_DAT * 100)}% số câu trở lên là Đạt.")
        so = st.pills("Chọn đề", list(range(1, len(de) + 1)), default=1, format_func=lambda k: f"Đề {k}") or 1
        if st.button(f"Bắt đầu Đề {so}", type="primary"):
            bat_dau_bai(f"Đề {so}", de[so - 1], co_chon_hinh, THOI_GIAN_DE, la_de=True, seed=so)
            st.rerun()
    elif che_do.startswith("🎯"):
        co_nhom = [n for n in THU_TU_NHOM if any(nhom_cua(m) == n for m in CAC_LOP)]
        nhom = st.pills("Nhóm biển", ["Tất cả"] + co_nhom, default="Tất cả") or "Tất cả"
        so_cau = st.pills("Số câu", [10, 20, 30], default=10) or 10
        if st.button("Bắt đầu luyện tập", type="primary"):
            nguon = [m for m in CAC_LOP if nhom == "Tất cả" or nhom_cua(m) == nhom]
            chon = random.sample(nguon, min(so_cau, len(nguon)))
            bat_dau_bai(f"Luyện tập – {nhom}", chon, co_chon_hinh)
            st.rerun()
    else:
        if not ss.cau_sai:
            st.info("Chưa có câu sai nào để ôn. Hãy làm một bộ đề hoặc luyện theo nhóm trước nhé!")
        else:
            st.write(f"Bạn đang có **{len(ss.cau_sai)} biển** trả lời sai hoặc bỏ qua. "
                     "Trả lời đúng biển nào thì biển đó được xóa khỏi danh sách ôn.")
            if st.button("Bắt đầu ôn câu sai", type="primary"):
                bat_dau_bai("Ôn lại câu sai", random.sample(sorted(ss.cau_sai), len(ss.cau_sai)), co_chon_hinh)
                st.rerun()

    # ----- Thống kê kết quả học tập -----
    st.divider()
    st.markdown("#### 📊 Thống kê của bạn")
    if not ss.thong_ke:
        st.caption("Thống kê sẽ hiện sau khi bạn trả lời câu hỏi đầu tiên.")
    else:
        tong_dung = sum(v[0] for v in ss.thong_ke.values())
        tong = sum(v[1] for v in ss.thong_ke.values())
        st.write(f"Đã trả lời **{tong}** câu, đúng **{tong_dung}** câu ({tong_dung / tong * 100:.0f}%).")
        for nhom in THU_TU_NHOM:
            if nhom in ss.thong_ke:
                d, t = ss.thong_ke[nhom]
                st.progress(d / t, text=f"{nhom}: {d}/{t} câu đúng ({d / t * 100:.0f}%)")
    st.caption("Thống kê và danh sách câu sai được lưu trong phiên làm việc; tải lại trang sẽ bắt đầu lại từ đầu.")


with tab_lt:
    ss = st.session_state
    ss.setdefault("bai", None)
    ss.setdefault("cau_sai", set())
    ss.setdefault("thong_ke", {})
    bai = ss.bai
    if bai is None:
        ve_chon_bai()
    else:
        if not bai["xong"] and het_gio(bai):
            ket_thuc(bai)
        if bai["xong"]:
            ve_ket_qua(bai)
        else:
            ve_cau_hoi(bai)
