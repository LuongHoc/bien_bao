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
import io
import html
import base64
import hashlib
import json as _json
import du_lieu_hoc_tap as dl
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
# Ngưỡng cảnh báo điểm tự tin: đọc từ kết quả đánh giá (danh_gia.py / danh_gia_anh_thuc.py), mặc định 0,5
try:
    NGUONG_TIN_CAY = float(json.load(open(os.path.join(GOC, "nguong_tin_cay.json")))["nguong"])
except Exception:
    NGUONG_TIN_CAY = 0.5
KICH_THUOC_TOI_DA_MB = 5       # giới hạn dung lượng ảnh tải lên (khớp server.maxUploadSize trong .streamlit/config.toml)
CANH_TOI_DA = 1600             # thu nhỏ ảnh lớn trước khi xử lý (giảm thời gian, bộ nhớ)
Image.MAX_IMAGE_PIXELS = 40_000_000   # chặn ảnh quá lớn bất thường (chống "bom giải nén")

st.set_page_config(page_title="Học biển báo giao thông", page_icon="🚦", layout="wide")

# ---------------- Giao diện ----------------
# Ý tưởng: "đọc biển như đọc đường". Bảng màu lấy từ sơn biển báo theo QCVN 41 (đỏ cấm, xanh hiệu lệnh,
# vàng cảnh báo) trên nền bê tông sáng; chữ tiêu đề Barlow Condensed (dáng chữ hẹp giống chữ trên biển chỉ dẫn),
# chữ nội dung Be Vietnam Pro (hiển thị dấu tiếng Việt rõ). Điểm nhấn duy nhất: dải "mặt đường" ở đầu trang.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap');
:root {
  --duong: #1B2559;      /* chữ chính */
  --xanh: #1F6FEB;       /* xanh chủ đạo – hành động chính */
  --xanh-nhat: #E8F0FE;
  --do: #E5484D; --vang: #F5A524;
  --be-tong: #F4F6FB;    /* nền trang */
  --trang: #FFFFFF;
  --phu: #6B7489;
  --vien: #E4E8F1;
  --dung: #16A34A; --dung-nhat: #E8F7EE;
  --sai: #E5484D;  --sai-nhat: #FDECEC;
  --ben: #10264A;        /* thanh bên */
  --bong: 0 1px 2px rgba(16,38,74,.04), 0 6px 18px rgba(16,38,74,.06);
}
html, body, .stApp, .stMarkdown, button, input, label, p, li, textarea {
  font-family: 'Be Vietnam Pro', 'Segoe UI', Arial, sans-serif !important; }
h1, h2, h3, h4, .chu-bien { font-family: 'Be Vietnam Pro', 'Segoe UI', Arial, sans-serif !important; font-weight: 700 !important; }
.stApp { background: var(--be-tong); color: var(--duong); }
header[data-testid="stHeader"] { background: transparent !important; height: 3rem; }
[data-testid="stToolbar"] [data-testid="stToolbarActions"], [data-testid="stMainMenu"], [data-testid="stDecoration"], footer,
[data-testid="stElementToolbar"], [data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] { display: flex !important; visibility: visible !important;
  background: var(--ben) !important; border-radius: 10px !important; color: #fff !important; }
[data-testid="stExpandSidebarButton"] *, [data-testid="stSidebarCollapsedControl"] * { color: #fff !important; }
.block-container { max-width: 1320px; padding-top: 1rem; padding-bottom: 3rem; }
button:focus-visible, input:focus-visible, [role="tab"]:focus-visible { outline: 3px solid var(--vang) !important; outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }

/* ---------- Dải mặt đường ở đầu trang ---------- */
.mat-duong { position: relative; background: var(--duong); border-radius: 16px; padding: 1.4rem 1.6rem 1.9rem;
  color: #fff; overflow: hidden; margin-bottom: 1.1rem; }
.mat-duong::after { content: ""; position: absolute; left: 1.6rem; right: 1.6rem; bottom: .85rem; height: 4px;
  background: repeating-linear-gradient(90deg, var(--vang) 0 34px, transparent 34px 58px); opacity: .9; }
.mat-duong .noi-dung { display: flex; align-items: flex-end; justify-content: space-between; gap: 1.5rem; flex-wrap: wrap; }
.mat-duong h1 { color: #fff !important; font-size: 2.6rem !important; font-weight: 700 !important; line-height: 1 !important;
  margin: 0 !important; padding: 0 !important; }
.mat-duong p { color: #C9D2DE; margin: .45rem 0 0; font-size: .98rem; max-width: 34rem; }
.hang-bien { display: flex; gap: .9rem; align-items: flex-end; }
.hang-bien figure { margin: 0; text-align: center; }
.hang-bien img { height: 58px; width: auto; display: block; margin: 0 auto .35rem; background: #fff; padding: 4px; border-radius: 7px;
  box-shadow: 0 4px 0 #0F141F; }
.hang-bien figcaption { font: 600 .95rem 'Barlow Condensed', sans-serif; color: #fff; }
.hang-bien figcaption span { display: block; font: 500 .72rem 'Be Vietnam Pro', sans-serif; color: #AEB9C7; }
@media (max-width: 720px) { .mat-duong h1 { font-size: 2rem !important; } .hang-bien { width: 100%; justify-content: space-between; gap: .3rem; }
  .hang-bien img { height: 38px; } .hang-bien figcaption { font-size: .8rem; white-space: nowrap; } .hang-bien figcaption span { display: none; } }

/* ---------- Thanh chuyển mục ---------- */
.stTabs [role="tablist"] { gap: .35rem; border-bottom: 2px solid var(--vien); flex-wrap: wrap; }
.stTabs [data-testid="stTab"] { padding: .6rem 1.1rem !important; border-radius: 10px 10px 0 0 !important; }
.stTabs [data-testid="stTab"] p { font: 600 1.15rem 'Barlow Condensed', sans-serif !important; color: var(--phu) !important; }
.stTabs [data-testid="stTab"][aria-selected="true"] { background: var(--trang) !important; box-shadow: inset 0 -3px 0 var(--xanh); }
.stTabs [data-testid="stTab"][aria-selected="true"] p { color: var(--duong) !important; }
.stTabs .react-aria-SelectionIndicator, .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [role="tabpanel"] { padding-top: 1.1rem; }

/* ---------- Nút và điều khiển ---------- */
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  background: var(--xanh) !important; border-color: var(--xanh) !important; color: #fff !important;
  border-radius: 10px !important; font-weight: 600 !important; }
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover { background: #084A8E !important; }
[data-testid="stBaseButton-secondary"] { border-radius: 10px !important; border: 1px solid var(--vien) !important; background: var(--trang) !important; color: var(--duong) !important; }
[data-testid="stBaseButton-secondary"]:hover { border-color: var(--xanh) !important; color: var(--xanh) !important; }
[data-testid="stButtonGroup"] button { border-radius: 999px !important; border-color: var(--vien) !important; background: var(--trang) !important; }
[data-testid="stButtonGroup"] button[aria-checked="true"] { background: var(--duong) !important; border-color: var(--duong) !important; }
[data-testid="stButtonGroup"] button[aria-checked="true"] p, [data-testid="stButtonGroup"] button[aria-checked="true"] span { color: #fff !important; }
[data-testid="stTextInput"] > div > div { border-radius: 10px; border: 1px solid var(--vien); background: var(--trang); }
[data-testid="stForm"] { padding: 0 !important; border: none !important; }
[data-testid="stProgress"] div[role="progressbar"] > div > div > div { background: var(--xanh) !important; }
[data-testid="stFileUploaderDropzone"] { background: var(--trang); border: 2px dashed var(--vien); border-radius: 14px; }
.chu-phu { color: var(--phu); font-size: .93rem; margin: .1rem 0 .7rem; }

/* ---------- Thư viện biển ---------- */
[class*="st-key-the_"] { background: var(--trang); border-radius: 14px; padding: .8rem .75rem .75rem; border: 1px solid var(--vien);
  border-top: 4px solid var(--mau, var(--vien)); height: 100%; }
[class*="st-key-the_cam_"] { --mau: var(--do); }  [class*="st-key-the_lenh_"] { --mau: var(--xanh); }
[class*="st-key-the_canh_"] { --mau: var(--vang); } [class*="st-key-the_chi_"] { --mau: #2E6FB7; }
[class*="st-key-the_phu_"] { --mau: #8A94A3; }
[class*="st-key-the_"] img { max-height: 104px; object-fit: contain; }
[class*="st-key-the_"] [data-testid="stBaseButton-secondary"] { background: var(--xanh-nhat) !important; border: none !important;
  color: var(--xanh) !important; font-weight: 600 !important; }
[class*="st-key-the_"] [data-testid="stBaseButton-secondary"]:hover { background: var(--xanh) !important; color: #fff !important; }
.ten-bien { font-size: .9rem; font-weight: 600; line-height: 1.3; height: 3.9em; overflow: hidden; text-align: center;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; margin: .45rem 0 .5rem; }
[class*="st-key-phan_trang"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .35rem; justify-content: center; }
[class*="st-key-phan_trang"] [data-testid="stColumn"] { flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }
[class*="st-key-phan_trang"] button { min-width: 2.6rem; font-weight: 600; }
.st-key-phan_trang_duoi { margin-top: 1rem; }
@media (max-width: 640px) {
  .st-key-luoi_bien [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .5rem; }
  .st-key-luoi_bien [data-testid="stColumn"] { flex: 1 1 calc(50% - .5rem) !important; min-width: calc(50% - .5rem) !important; }
}

/* ---------- Thông tin biển (hộp thoại) và kết quả nhận dạng ---------- */
.nen-bien { background: var(--be-tong); border-radius: 14px; padding: 1rem; }
.bien-so { display: inline-block; background: var(--duong); color: #fff; font: 700 1.05rem 'Barlow Condensed', sans-serif;
  padding: .15rem .6rem; border-radius: 6px; letter-spacing: .5px; }
.nhan-nhom { display: inline-flex; align-items: center; gap: .4rem; font-size: .85rem; color: var(--phu); margin-left: .5rem; }
.nhan-nhom i { width: 10px; height: 10px; border-radius: 50%; display: inline-block; background: var(--mau); }
.ten-lon { font: 700 2rem/1.1 'Barlow Condensed', sans-serif; margin: .5rem 0 .9rem; color: var(--duong); }
.muc { margin: 0 0 .9rem; }
.muc b { display: block; font: 600 1.05rem 'Barlow Condensed', sans-serif; color: var(--phu); margin-bottom: .15rem; }
.muc.y-nghia p { font-size: 1.05rem; line-height: 1.6; }
.minh-hoa { border-radius: 12px; padding: .7rem .9rem; font-size: .92rem; line-height: 1.5; }
.minh-hoa.khop { background: var(--dung-nhat); color: #0B5C42; }
.minh-hoa.lech { background: #FFF6D9; color: #6B5200; }
.diem { margin: .25rem 0; }
.diem .hang { display: flex; justify-content: space-between; font-size: .9rem; gap: .8rem; }
.diem .thanh { height: 8px; background: var(--be-tong); border-radius: 99px; overflow: hidden; margin-top: .25rem; position: relative; }
.diem .thanh span { display: block; height: 100%; background: var(--xanh); border-radius: 99px; }
.diem.dau .thanh span { background: var(--duong); }
.diem .thanh em { position: absolute; top: -2px; bottom: -2px; width: 2px; background: var(--do); }
.st-key-ket_qua_nd { background: var(--trang); border: 1px solid var(--vien); border-radius: 16px; padding: 1.1rem 1.2rem; }
.the-trang { background: var(--trang); border: 1px solid var(--vien); border-radius: 16px; padding: 1.2rem 1.3rem; }

/* ---------- Luyện tập ---------- */
.st-key-cau_hoi { background: var(--trang); border: 1px solid var(--vien); border-radius: 18px; padding: 1.3rem 1.4rem; }
[class*="st-key-tl_"] button { justify-content: flex-start !important; padding: .75rem 1rem !important; min-height: 3.1rem; }
[class*="st-key-tl_"] button > div { justify-content: flex-start !important; width: 100%; }
[class*="st-key-tl_"] button p { font-size: 1rem; text-align: left; }
.vach-tien-do { display: flex; gap: 3px; margin: .4rem 0 1rem; }
.vach-tien-do span { flex: 1; height: 7px; border-radius: 3px; background: var(--vien); }
.vach-tien-do .d { background: var(--dung); } .vach-tien-do .s { background: var(--sai); }
.vach-tien-do .b { background: #A9B1BD; } .vach-tien-do .h { background: var(--duong); }
.dau-cau { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; }
.dau-cau .chu-bien { font-size: 1.35rem; font-weight: 700; }
.cau-hoi { font: 700 1.5rem/1.2 'Barlow Condensed', sans-serif; margin: .6rem 0 .8rem; }
.dap-an { border: 1px solid var(--vien); border-radius: 10px; padding: .7rem 1rem; margin-bottom: .5rem; }
.dap-an.dung { background: var(--dung-nhat); border-color: var(--dung); font-weight: 600; }
.dap-an.sai { background: var(--sai-nhat); border-color: var(--sai); }
.giai-thich { background: var(--be-tong); border-radius: 12px; padding: .8rem 1rem; margin: .6rem 0 .9rem; line-height: 1.55; }
.diem-lon { font: 700 4.2rem/1 'Barlow Condensed', sans-serif; color: var(--duong); }
.diem-lon small { font-size: 1.6rem; color: var(--phu); }
.ket-luan { display: inline-block; font: 700 1.2rem 'Barlow Condensed', sans-serif; padding: .2rem .8rem; border-radius: 8px; margin-left: .6rem; }
.ket-luan.dat { background: var(--dung-nhat); color: var(--dung); } .ket-luan.chua { background: var(--sai-nhat); color: var(--sai); }
.tk-nhom { margin: .55rem 0; } .tk-nhom .hang { display: flex; justify-content: space-between; font-size: .92rem; }
.tk-nhom .thanh { height: 9px; background: var(--be-tong); border-radius: 99px; overflow: hidden; margin-top: .25rem; }
.tk-nhom .thanh span { display: block; height: 100%; border-radius: 99px; }
.st-key-khung_thong_ke, .st-key-ket_qua_bai, .st-key-khung_tong_hop { background: var(--trang); border: 1px solid var(--vien); border-radius: 16px; padding: 1.1rem 1.2rem; }
.st-key-nen_bien_dialog, .st-key-nen_bien_cau { background: var(--be-tong); border-radius: 14px; padding: 1rem; }
.st-key-nen_bien_cau img { max-height: 260px; object-fit: contain; }
[data-testid="stMetric"] { background: var(--trang); border: 1px solid var(--vien); border-radius: 14px; padding: .7rem 1rem; }

/* ===================== Bố cục bảng điều khiển ===================== */
[data-testid="stSidebar"] { background: var(--ben) !important; }
[data-testid="stSidebar"] * { color: #DCE4F5; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] { background: transparent !important; border: none !important;
  color: #C9D3EA !important; justify-content: flex-start !important; padding: .6rem .8rem !important; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover { background: rgba(255,255,255,.08) !important; color: #fff !important; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] { justify-content: flex-start !important; padding: .6rem .8rem !important;
  background: var(--xanh) !important; border: none !important; }
[data-testid="stSidebar"] button > div { justify-content: flex-start !important; }
[data-testid="stSidebar"] button p { font-weight: 500 !important; font-size: .95rem !important; color: inherit !important; }
.st-key-menu_duoi { margin-top: 38vh; border-top: 1px solid rgba(255,255,255,.08); padding-top: .6rem; }
.logo { display: flex; align-items: center; gap: .7rem; font-weight: 700; color: #fff; line-height: 1.25; margin: .2rem 0 1.4rem; font-size: .98rem; }
.logo-bien { width: 34px; height: 34px; flex-shrink: 0; background: #fff; clip-path: polygon(50% 0, 100% 100%, 0 100%);
  position: relative; }
.logo-bien::after { content: ""; position: absolute; inset: 7px 7px 4px; background: var(--do); clip-path: polygon(50% 0, 100% 100%, 0 100%); }
.st-key-thanh_quay_lai button { background: var(--trang) !important; border: 1px solid var(--vien) !important; padding: .3rem .8rem !important;
  min-height: 0 !important; font-size: .88rem; }
.thanh-tren { display: flex; justify-content: flex-end; align-items: center; gap: .45rem; font-size: .92rem; color: var(--phu); margin: -.2rem 0 .8rem; }
.thanh-tren b { color: var(--duong); } .avatar { background: var(--xanh-nhat); border-radius: 50%; width: 30px; height: 30px; display: inline-grid; place-items: center; }
.tieu-de-trang h2 { font-size: 1.6rem !important; margin: 0 0 .2rem !important; padding: 0 !important; }
.tieu-de-trang p { color: var(--phu); margin: 0 0 1rem; }
[class*="st-key-khung_"], [class*="st-key-tinh_nang_"] { background: var(--trang); border: 1px solid var(--vien); border-radius: 16px;
  padding: 1rem 1.1rem; box-shadow: var(--bong); }
[class*="st-key-tinh_nang_"] { box-shadow: none; padding: .9rem; }
.st-key-tinh_nang_0 { background: #EEF4FF; border-color: #DCE7FD; } .st-key-tinh_nang_1 { background: #F5F0FF; border-color: #E6DBFD; }
.st-key-tinh_nang_2 { background: #ECF8F1; border-color: #D3EFDD; } .st-key-tinh_nang_3 { background: #FFF6E8; border-color: #FBE6C4; }
.o-bieu-tuong { width: 44px; height: 44px; border-radius: 12px; display: grid; place-items: center; font-size: 1.35rem; margin-bottom: .6rem; background: #fff; }
.ten-the { font-weight: 700; color: var(--duong); font-size: .98rem; margin-bottom: .2rem; }
.mo-ta-the { color: var(--phu); font-size: .82rem; line-height: 1.45; }
[class*="st-key-tinh_nang_"] { position: relative; cursor: pointer; transition: transform .15s, box-shadow .15s; }
[class*="st-key-tinh_nang_"]:hover { transform: translateY(-2px); box-shadow: var(--bong); }
[class*="st-key-tinh_nang_"] [data-testid="stElementContainer"], [class*="st-key-tinh_nang_"] .stButton { position: static !important; }
[class*="st-key-tinh_nang_"] [data-testid="stBaseButton-secondary"] { position: absolute !important; inset: 0; width: 100%; height: 100%;
  background: transparent !important; border: none !important; z-index: 2; display: flex !important; align-items: flex-end !important;
  justify-content: flex-start !important; padding: 0 .9rem .7rem !important; color: var(--xanh) !important; }
[class*="st-key-tinh_nang_"] [data-testid="stBaseButton-secondary"] p { font-size: 1.25rem !important; color: var(--xanh) !important; text-align: left; }
[class*="st-key-tinh_nang_"] [data-testid="stBaseButton-secondary"] > div { width: 100%; justify-content: flex-start !important; }
[class*="st-key-tinh_nang_"] .mo-ta-the { margin-bottom: 1.6rem; }
.dau-khung { display: flex; align-items: center; gap: .55rem; margin-bottom: .8rem; color: var(--duong); font-size: 1.02rem; }
.o-nho { width: 32px; height: 32px; border-radius: 9px; background: var(--xanh-nhat); display: inline-grid; place-items: center; font-size: 1rem; flex-shrink: 0; }
[class*="st-key-nhom_"] { border-radius: 14px; padding: .9rem .6rem .7rem; border: 1px solid var(--vien); }
[class*="st-key-nhom_"] [data-testid="stImage"] { display: flex; justify-content: center; }
.st-key-nhom_cam { background: #FEF1F1; border-color: #FAD9DA; } .st-key-nhom_lenh { background: #EEF4FF; border-color: #D8E5FC; }
.st-key-nhom_canh { background: #FFF7E6; border-color: #FBE8C2; } .st-key-nhom_chi { background: #EDF6FF; border-color: #D3E6FA; }
.st-key-nhom_phu { background: #F3F4F7; border-color: #E2E5EC; }
[class*="st-key-nhom_"] [data-testid="stBaseButton-secondary"] { font-size: .82rem; min-height: 0 !important; padding: .3rem .4rem !important; }
.st-key-nhom_cam button { color: #C93338 !important; background: #FBDCDD !important; border: none !important; }
.st-key-nhom_lenh button, .st-key-nhom_chi button { color: var(--xanh) !important; background: #DCE8FD !important; border: none !important; }
.st-key-nhom_canh button { color: #B26B00 !important; background: #FCE8C3 !important; border: none !important; }
.st-key-nhom_phu button { color: var(--phu) !important; background: #E4E7EE !important; border: none !important; }
.o-thong-ke { display: flex; flex-direction: column; gap: .45rem; align-items: flex-start; border: 1px solid var(--vien); border-radius: 14px; padding: .8rem; height: 100%; }
.so-lon { font-size: 1.2rem; font-weight: 700; color: var(--duong); line-height: 1.3; }
.thanh-mini { height: 6px; background: var(--be-tong); border-radius: 9px; margin-top: .35rem; overflow: hidden; width: 100%; min-width: 80px; }
.thanh-mini span { display: block; height: 100%; background: var(--xanh); }
/* Ảnh bìa */
.st-key-anh_bia [data-testid="stElementContainer"], .st-key-anh_bia [data-testid="stMarkdown"],
.st-key-anh_bia [data-testid="stMarkdownContainer"] { position: static !important; }
.st-key-anh_bia { position: relative; border-radius: 18px; overflow: hidden; padding: 1.7rem 1.8rem 1.6rem;
  background: linear-gradient(100deg, #10306E 0%, #1F56C9 48%, rgba(31,86,201,.0) 75%), #1F56C9; min-height: 220px; }
.bia-anh { position: absolute; inset: 0 0 0 46%; background-size: cover; background-position: center bottom;
  -webkit-mask-image: linear-gradient(90deg, transparent 0, #000 28%); mask-image: linear-gradient(90deg, transparent 0, #000 28%); }
.bia-anh.anh-that { inset: 0 0 0 24%; -webkit-mask-image: linear-gradient(90deg, transparent 0, #000 38%);
  mask-image: linear-gradient(90deg, transparent 0, #000 38%); background-position: center; }
.bia-anh img { position: absolute; filter: drop-shadow(0 6px 10px rgba(0,0,0,.25)); }
.bia-anh .bb0 { height: 74px; right: 40%; top: 10%; } .bia-anh .bb1 { height: 80px; right: 12%; top: 7%; }
.bia-anh .bb2 { height: 72px; right: 44%; bottom: 9%; } .bia-anh .bb3 { height: 86px; right: 16%; bottom: 8%; }
.bia-tieu-de { color: #fff !important; font-size: 1.7rem !important; line-height: 1.25 !important; margin: 0 !important; padding: 0 !important;
  position: relative; max-width: 54%; text-shadow: 0 2px 8px rgba(0,0,0,.25); }
.bia-phu { color: #D6E2FF; margin: .6rem 0 1rem; position: relative; max-width: 54%; }
.st-key-anh_bia [data-testid="stBaseButton-primary"] { background: #2D7BFF !important; border-color: #2D7BFF !important; position: relative; padding: .55rem 1.2rem !important; }
.st-key-mo_camera button { border: 2px dashed #BFD3F8 !important; background: #F7FAFF !important; min-height: 9rem;
  color: var(--duong) !important; flex-direction: column !important; gap: .5rem; margin-top: .6rem; }
.st-key-mo_camera button > div { flex-direction: column !important; align-items: center !important; gap: .45rem; }
.st-key-mo_camera [data-testid="stIconMaterial"] { font-size: 2.6rem !important; color: var(--xanh) !important; }
.st-key-mo_camera button p { font-weight: 600 !important; }
.st-key-mo_camera button::after { content: "hoặc tải ảnh từ thiết bị"; font-size: .8rem; color: var(--phu); }
[class*="st-key-mo_trang_nd"] button, [class*="st-key-xem_tat_ca_bt"] button { color: var(--xanh) !important; font-size: .85rem; padding: 0 !important;
  justify-content: flex-end !important; width: 100%; }
[class*="st-key-mo_trang_nd"] button p, [class*="st-key-xem_tat_ca_bt"] button p { font-size: .85rem !important; color: var(--xanh) !important; }
/* nút Tải ảnh lên: biến ô kéo thả thành nút xanh */
.st-key-khung_nhan_dang_nhanh [data-testid="stFileUploaderDropzone"] { background: var(--xanh) !important; border: none !important;
  padding: 0 !important; border-radius: 10px !important; min-height: 0 !important; }
.st-key-khung_nhan_dang_nhanh [data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
.st-key-khung_nhan_dang_nhanh [data-testid="stFileUploaderDropzone"] button { width: 100% !important; min-height: 2.9rem !important;
  background: transparent !important; border: none !important; font-size: 0 !important; }
.st-key-khung_nhan_dang_nhanh [data-testid="stFileUploaderDropzone"] button * { display: none !important; }
.st-key-khung_nhan_dang_nhanh [data-testid="stFileUploaderDropzone"] button::after { content: "⤒  Tải ảnh lên"; color: #fff;
  font-size: .98rem; font-weight: 600; }
.st-key-khung_nhan_dang_nhanh [data-testid="stFileUploaderDropzone"] > div, .st-key-khung_nhan_dang_nhanh [data-testid="stFileUploaderDropzone"] > span {
  width: 100%; }
.cau-nhanh { font-weight: 700; color: var(--duong); font-size: .92rem; margin-bottom: .4rem; }
.st-key-khung_bai_nhanh [data-testid="stRadio"] label { font-size: .84rem; padding: .45rem .6rem !important; }
.st-key-khung_bai_nhanh [data-testid="stRadio"] label p { font-size: .84rem !important; line-height: 1.35; }

.chu-hoac { display: flex; align-items: center; gap: .8rem; color: var(--phu); font-size: .85rem; margin: .7rem 0; }
.chu-hoac::before, .chu-hoac::after { content: ""; flex: 1; height: 1px; background: var(--vien); }
.goi-y { background: #F2F6FD; border-radius: 10px; padding: .65rem .8rem; font-size: .84rem; color: var(--phu); margin-top: .6rem; line-height: 1.5; }
.st-key-nen_bien_nhanh { background: var(--be-tong); border-radius: 12px; padding: .7rem; }
.st-key-khung_bai_nhanh [data-testid="stRadio"] label { border: 1px solid var(--vien); border-radius: 10px; padding: .5rem .7rem; width: 100%; margin-bottom: .35rem; }
.st-key-khung_bai_nhanh [data-testid="stRadio"] label:has(input:checked) { border-color: var(--xanh); background: var(--xanh-nhat); }
@media (max-width: 900px) { .bia-anh { display: none; } .bia-tieu-de, .bia-phu { max-width: 100%; } .st-key-anh_bia { background: linear-gradient(100deg, #10306E, #1F56C9); } }
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


MA_NHOM_CSS = {"Biển báo cấm": "cam", "Biển hiệu lệnh": "lenh", "Biển báo nguy hiểm và cảnh báo": "canh",
               "Biển chỉ dẫn": "chi", "Biển phụ": "phu"}
MAU_CSS = {"cam": "var(--do)", "lenh": "var(--xanh)", "canh": "var(--vang)", "chi": "#2E6FB7", "phu": "#8A94A3"}


def esc(t):
    return html.escape(str(t))


def nhan_nhom_html(m):
    n = nhom_cua(m)
    return f'<span class="nhan-nhom" style="--mau:{MAU_CSS[MA_NHOM_CSS.get(n, "phu")]}"><i></i>{esc(n)}</span>'


def thanh_diem(ten, p, dau=False, nguong=None):
    moc = f'<em style="left:{nguong * 100:.0f}%" title="Ngưỡng cảnh báo"></em>' if nguong else ""
    return (f'<div class="diem{" dau" if dau else ""}"><div class="hang"><span>{esc(ten)}</span><b>{p * 100:.1f}%</b></div>'
            f'<div class="thanh"><span style="width:{max(p, 0.005) * 100:.1f}%"></span>{moc}</div></div>')


@st.cache_data
def anh_base64(duong_dan, cao=120, trong_suot=False):
    a = Image.open(duong_dan).convert("RGBA")
    if trong_suot:   # xóa nền trắng bên ngoài biển (tô loang từ 4 góc), giữ nguyên phần trắng bên trong biển
        from PIL import ImageDraw
        for goc in [(0, 0), (a.width - 1, 0), (0, a.height - 1), (a.width - 1, a.height - 1)]:
            if a.getpixel(goc)[:3] > (235, 235, 235):
                ImageDraw.floodfill(a, goc, (255, 255, 255, 0), thresh=40)
    a.thumbnail((cao * 2, cao))
    buf = io.BytesIO(); a.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def hien_ket_qua(anh_pil, ma_anh=None, nguon_anh=""):
    """Kết quả nhận dạng ảnh người dùng: biển có điểm Softmax cao nhất + các khả năng tiếp theo."""
    thu_tu, xac_suat = nhan_dang(anh_pil)
    ma, p = str(int(thu_tu[0])), float(xac_suat[thu_tu[0]])
    tt = thong_tin(ma)
    with st.container(key="ket_qua_nd"):
        c_anh, c_chu = st.columns([1, 2], vertical_alignment="center")
        c_anh.image(ANH_MAU[ma][0] if ma in ANH_MAU else anh_pil, width="stretch")
        c_chu.markdown(f'<span class="bien-so">{esc(ky_hieu(ma))}</span>{nhan_nhom_html(ma)}'
                       f'<div class="ten-lon" style="font-size:1.6rem">{esc(ten_bien(ma))}</div>', unsafe_allow_html=True)
        if p >= NGUONG_TIN_CAY:
            st.success(f"Điểm tự tin của mô hình (Softmax): {p * 100:.1f}%")
        else:
            st.warning(f"Điểm tự tin thấp ({p * 100:.1f}%, dưới ngưỡng {NGUONG_TIN_CAY * 100:.0f}%). Kết quả có thể chưa đúng: "
                       "chỉnh khung sát quanh biển hơn, hoặc biển này có thể không thuộc 340 biển đã học.")
        khac = "".join(thanh_diem(f'{ky_hieu(str(int(k)))} · {ten_bien(str(int(k)))}', float(xac_suat[k]), dau=(j == 0),
                                  nguong=NGUONG_TIN_CAY if j == 0 else None) for j, k in enumerate(thu_tu[:4]))
        st.markdown(f'<div class="muc y-nghia"><b>Ý nghĩa</b><p>{esc(tt["y_nghia"])}</p></div>'
                    f'<div class="muc"><b>Bốn khả năng cao nhất (điểm Softmax)</b>{khac}</div>', unsafe_allow_html=True)
        st.caption("Điểm Softmax là mức tự tin của mô hình, chưa phải xác suất đúng đã được kiểm chứng; "
                   "với ảnh chụp ngoài đường, kết quả có thể kém hơn so với hình chuẩn.")
        if ma_anh:
            phan_hoi_nhan_dang(ma_anh, nguon_anh, ma, p, [str(int(k)) for k in thu_tu[:5]])


def phan_hoi_nhan_dang(ma_anh, nguon_anh, ma, p, top5):
    """Người học xác nhận kết quả đúng/sai -> dùng để đánh giá chức năng nhận dạng ảnh tải lên (không lưu ảnh)."""
    ss = st.session_state
    da = ss.setdefault("da_phan_hoi", {})
    st.markdown('<div class="muc" style="margin-top:.6rem"><b>Kết quả này có đúng với biển trong ảnh không?</b></div>',
                unsafe_allow_html=True)
    if ma_anh in da:
        st.markdown(f'<p class="chu-phu">Cảm ơn bạn đã xác nhận ({da[ma_anh]}). Phản hồi giúp đánh giá chức năng nhận dạng.</p>',
                    unsafe_allow_html=True)
        return
    c1, c2 = st.columns(2)
    if c1.button("✓ Đúng biển này", key=f"ph_dung_{ma_anh}", width="stretch"):
        dl.ghi_phan_hoi(nguon_anh, MA_BIEN[ma], p, [MA_BIEN[k] for k in top5], "dung", MA_BIEN[ma])
        da[ma_anh] = "đúng"
        st.rerun()
    if c2.toggle("✗ Chưa đúng", key=f"ph_sai_{ma_anh}"):
        with st.form(f"ph_form_{ma_anh}", border=False):
            chon = st.selectbox("Biển đúng là (nếu biết):", ["Không biết / không có trong danh sách"] + CAC_LOP,
                                format_func=lambda m: m if m.startswith("Không") else f"{ky_hieu(m)} – {ten_bien(m)}")
            if st.form_submit_button("Gửi phản hồi", type="primary"):
                dl.ghi_phan_hoi(nguon_anh, MA_BIEN[ma], p, [MA_BIEN[k] for k in top5], "sai",
                                "" if chon.startswith("Không") else MA_BIEN[chon])
                da[ma_anh] = "chưa đúng"
                st.rerun()


# ---------------- Đầu trang: dải "mặt đường" với 5 biển đại diện cho 5 nhóm ----------------
def _bien_dai_dien():
    mau = {"Biển báo cấm": "P.102", "Biển hiệu lệnh": "R.303", "Biển báo nguy hiểm và cảnh báo": "W.225",
           "Biển chỉ dẫn": "I.423a", "Biển phụ": "S.502"}
    nguoc = {v: k for k, v in MA_BIEN.items()}
    ra = []
    for n in THU_TU_NHOM:
        m = nguoc.get(mau[n]) or next((x for x in CAC_LOP if nhom_cua(x) == n), None)
        if m:
            ra.append((n, m, sum(nhom_cua(x) == n for x in CAC_LOP)))
    return ra


TEN_NGAN = {"Biển báo cấm": "Cấm", "Biển hiệu lệnh": "Hiệu lệnh", "Biển báo nguy hiểm và cảnh báo": "Cảnh báo",
            "Biển chỉ dẫn": "Chỉ dẫn", "Biển phụ": "Biển phụ"}


# ---------- Tab 1: Thư viện biển báo ----------
@st.dialog("Thông tin biển báo", width="large")
def xem_bien(m):
    """Nội dung hiển thị theo NHÃN THAM CHIẾU (biển người học đã chọn) nên luôn đúng; hình chuẩn được đưa qua
    mạng nơron để MINH HỌA kết quả nhận dạng và so khớp với nhãn tham chiếu."""
    anh = Image.open(ANH_MAU[m][0]).convert("RGB")
    thu_tu, xac_suat = nhan_dang(anh)
    kq, p = str(int(thu_tu[0])), float(xac_suat[thu_tu[0]])
    tt = thong_tin(m)
    c1, c2 = st.columns([2, 3], gap="large")
    with c1:
        with st.container(key="nen_bien_dialog"):
            st.image(anh, width="stretch")
        if kq == m:
            st.markdown(f'<div class="minh-hoa khop">🧠 <b>Minh họa nhận dạng:</b> mạng nơron nhận đúng biển này, '
                        f'điểm Softmax {p * 100:.1f}%.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="minh-hoa lech">🧠 <b>Minh họa nhận dạng:</b> mạng nơron nhận nhầm thành '
                        f'{esc(ky_hieu(kq))} – {esc(ten_bien(kq))} (điểm Softmax {p * 100:.1f}%). Nội dung bên cạnh là '
                        f'của biển bạn đã chọn.</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<span class="bien-so">{esc(ky_hieu(m))}</span>{nhan_nhom_html(m)}'
                    f'<div class="ten-lon">{esc(ten_bien(m))}</div>'
                    f'<div class="muc y-nghia"><b>Ý nghĩa</b><p>{esc(tt["y_nghia"])}</p></div>'
                    f'<div class="muc"><b>Đặc điểm nhận biết</b><p>{esc(tt["dac_diem"])}</p></div>', unsafe_allow_html=True)
        st.caption("Ký hiệu và nội dung theo QCVN 41:2024/BGTVT.")


def trang_thu_vien():
    co_nhom = [n for n in THU_TU_NHOM if any(nhom_cua(m) == n for m in CAC_LOP)]
    st.markdown('<div class="tieu-de-trang"><h2>Học lý thuyết</h2><p>Tra cứu 340 biển báo theo QCVN 41:2024 và ý nghĩa của từng biển.</p></div>',
                unsafe_allow_html=True)
    st.session_state.setdefault("loc_nhom", "Tất cả")
    nhom = st.pills("Nhóm biển báo", ["Tất cả"] + co_nhom, key="loc_nhom",
                    format_func=lambda n: n if n == "Tất cả" else f"{TEN_NGAN.get(n, n)} ({sum(nhom_cua(m) == n for m in CAC_LOP)})")
    # Ô tìm kiếm + nút kính lúp (bấm nút hoặc nhấn Enter để tìm)
    with st.form("tim_kiem", border=False):
        o_tim, nut_tim = st.columns([6, 1], vertical_alignment="bottom")
        nhap = o_tim.text_input("Tìm biển", placeholder="Tìm theo tên hoặc ký hiệu, ví dụ: trẻ em, P.102",
                                label_visibility="collapsed")
        if nut_tim.form_submit_button("Tìm", icon=":material/search:", type="primary", width="stretch"):
            st.session_state.tu_khoa = nhap.strip().lower()
    tu_khoa = st.session_state.get("tu_khoa", "")
    if tu_khoa:
        c_kq, c_xoa = st.columns([6, 1], vertical_alignment="center")
        c_kq.markdown(f'<p class="chu-phu">Kết quả tìm kiếm cho “<b>{esc(tu_khoa)}</b>”</p>', unsafe_allow_html=True)
        if c_xoa.button("Xóa tìm kiếm", icon=":material/close:", width="stretch"):
            st.session_state.tu_khoa = ""
            st.rerun()
    nhom = nhom or "Tất cả"
    ds = [m for m in CAC_LOP if (nhom == "Tất cả" or nhom_cua(m) == nhom)
          and (not tu_khoa or tu_khoa in thong_tin(m)["ten"].lower())]
    MOI_TRANG, SO_COT = 30, 6
    so_trang = max(1, (len(ds) + MOI_TRANG - 1) // MOI_TRANG)
    if not ds:
        st.info("Không có biển nào khớp. Thử gõ ít chữ hơn, hoặc chọn nhóm “Tất cả”.")
    else:
        st.markdown(f'<p class="chu-phu">{len(ds)} biển. Bấm <b>Xem ý nghĩa</b> để đọc nội dung biển theo quy chuẩn.</p>',
                    unsafe_allow_html=True)
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
        for hang_i in range(0, len(trang_nay), SO_COT):
            cot = st.columns(SO_COT)
            for k, m in enumerate(trang_nay[hang_i: hang_i + SO_COT]):
                with cot[k]:
                    with st.container(key=f"the_{MA_NHOM_CSS.get(nhom_cua(m), 'phu')}_{m}"):
                        st.image(ANH_MAU[m][0], width="stretch")
                        ten = ten_bien(m)
                        st.markdown(f'<div class="ten-bien" title="{esc(ten)}">{esc(ten)}</div>', unsafe_allow_html=True)
                        if st.button("Xem ý nghĩa", key=f"xem_{m}", width="stretch", help=f"Ký hiệu: {ky_hieu(m)}"):
                            xem_bien(m)
    ve_phan_trang("duoi")

# ---------- Tab 2: Nhận dạng ảnh ----------
def trang_nhan_dang():
    c_trai, c_phai = st.columns([3, 2], gap="large")
    with c_trai:
        st.markdown('<div class="tieu-de-trang"><h2>Nhận dạng biển báo</h2><p>Chụp hoặc tải ảnh có biển báo, chọn vùng quanh biển để mạng nơron nhận dạng.</p></div>',
                    unsafe_allow_html=True)
        st.session_state.setdefault("nguon_anh", "Tải ảnh lên")
        nguon = st.segmented_control("Nguồn ảnh", ["Tải ảnh lên", "Chụp bằng webcam"], key="nguon_anh") or "Tải ảnh lên"
        if nguon == "Tải ảnh lên":
            tep = st.file_uploader(f"Ảnh JPG, PNG hoặc WebP, tối đa {KICH_THUOC_TOI_DA_MB} MB. "
                                   "Trên điện thoại có thể chọn Máy ảnh để chụp trực tiếp.", type=["jpg", "jpeg", "png", "webp"])
        else:
            tep = st.camera_input("Chụp ảnh biển báo")
    with c_phai:
        st.markdown('<div class="the-trang"><div class="muc"><b>Cách nhận dạng một biển</b>'
                    '<p>1. Chụp hoặc tải ảnh có biển báo.<br>2. Kéo khung vàng sát quanh biển (vùng quan tâm).'
                    '<br>3. Đọc kết quả và ý nghĩa ở khung bên cạnh.</p></div>'
                    '<p class="chu-phu" style="margin:0">🔒 Ảnh chỉ được xử lý tạm thời trong bộ nhớ, không lưu trên máy chủ.</p></div>',
                    unsafe_allow_html=True)

    if tep is None and st.session_state.get("anh_nhanh") is not None:   # ảnh tải lên từ Trang chủ
        tep = io.BytesIO(st.session_state.anh_nhanh)
    anh = None
    if tep is not None:
        if len(tep.getvalue()) > KICH_THUOC_TOI_DA_MB * 1024 * 1024:
            st.error(f"Ảnh lớn hơn {KICH_THUOC_TOI_DA_MB} MB. Hãy chọn ảnh nhỏ hơn hoặc giảm chất lượng ảnh.")
        else:
            try:
                ma_anh = hashlib.md5(tep.getvalue()).hexdigest()[:12]           # mã nhận diện ảnh (không lưu ảnh)
                anh = ImageOps.exif_transpose(Image.open(tep)).convert("RGB")  # xoay đúng chiều ảnh điện thoại
                anh.thumbnail((CANH_TOI_DA, CANH_TOI_DA))                       # thu nhỏ ảnh quá lớn
            except Exception:
                st.error("Không đọc được tệp này. Hãy chọn ảnh JPG hoặc PNG hợp lệ.")
    if anh is not None:
        st.divider()
        c_vung, c_kq = st.columns([3, 2], gap="large")
        with c_vung:
            if CO_KHOANH_VUNG:
                st.markdown('<p class="chu-phu">Kéo và chỉnh khung vàng cho sát quanh biển báo; kết quả bên cạnh tự cập nhật.</p>',
                            unsafe_allow_html=True)
                w, h = anh.size
                try:   # khung mặc định bao toàn ảnh (phù hợp ảnh đã cắt sẵn)
                    vung = st_cropper(anh, realtime_update=True, box_color="#F2B705", aspect_ratio=None,
                                      default_coords=(int(w * .02), int(w * .98), int(h * .02), int(h * .98)))
                except TypeError:
                    vung = st_cropper(anh, realtime_update=True, box_color="#F2B705", aspect_ratio=None)
            else:
                vung = anh
                st.image(anh, width="stretch")
        with c_kq:
            hien_ket_qua(vung, ma_anh, "webcam" if nguon != "Tải ảnh lên" else "tải lên")

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
    ss.setdefault("da_hoi", set()).add(cau["dung"])
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
    luu_lich_su(bai)


def luu_lich_su(bai):
    """Lưu kết quả bài vào lịch sử học tập nếu người học đã đặt biệt danh (mỗi bài chỉ lưu một lần)."""
    bd = st.session_state.get("biet_danh", "").strip()
    if not bd or bai.get("da_luu"):
        return
    so = len(bai["cau"])
    dung = sum(c["tra_loi"] == c["dung"] for c in bai["cau"])
    bo = sum(c["tra_loi"] == "bo_qua" for c in bai["cau"])
    theo_nhom = {}
    for c in bai["cau"]:
        t = theo_nhom.setdefault(TEN_NGAN.get(nhom_cua(c["dung"]), "Khác"), [0, 0])
        t[1] += 1
        t[0] += c["tra_loi"] == c["dung"]
    loai = "Bộ đề" if bai["la_de"] else ("Ôn câu sai" if bai["ten"].startswith("Ôn") else "Luyện theo nhóm")
    dl.luu_bai_lam(bd, loai, bai["ten"], so, dung, so - dung - bo, bo,
                   ("Đạt" if dung >= NGUONG_DAT * so else "Chưa đạt") if bai["la_de"] else "",
                   theo_nhom, [MA_BIEN[c["dung"]] for c in bai["cau"] if c["tra_loi"] != c["dung"]])
    bai["da_luu"] = True


def dong_ho(han):
    con_lai_ms = int(max(0, han - time.time()) * 1000)
    html_dh = f"""
    <div id="dh" style="font:700 22px 'Barlow Condensed','Arial Narrow',Arial,sans-serif;color:#1D2433;text-align:right"></div>
    <script>
      const het = Date.now() + {con_lai_ms};
      function ve() {{
        const s = Math.max(0, Math.round((het - Date.now()) / 1000));
        const el = document.getElementById('dh');
        el.textContent = 'Còn ' + String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
        el.style.color = s <= 60 ? '#CC1F2D' : '#1D2433';
        if (s > 0) setTimeout(ve, 500); else el.textContent = 'Hết giờ';
      }}
      ve();
    </script>"""
    if hasattr(st, "iframe"):          # Streamlit bản mới
        st.iframe(html_dh, height=36)
    else:                              # Streamlit bản cũ
        components.html(html_dh, height=36)


def vach_tien_do(bai):
    """Mỗi câu là một vạch: xanh lá = đúng, đỏ = sai, xám = bỏ qua, đậm = câu đang làm."""
    o = []
    for j, c in enumerate(bai["cau"]):
        if c["tra_loi"] is None:
            o.append('<span class="h"></span>' if j == bai["hien"] else "<span></span>")
        else:
            o.append('<span class="b"></span>' if c["tra_loi"] == "bo_qua" else
                     ('<span class="d"></span>' if c["tra_loi"] == c["dung"] else '<span class="s"></span>'))
    return f'<div class="vach-tien-do" aria-hidden="true">{"".join(o)}</div>'


def ve_ket_qua(bai):
    so_cau = len(bai["cau"])
    dung = sum(c["tra_loi"] == c["dung"] for c in bai["cau"])
    bo_qua = sum(c["tra_loi"] == "bo_qua" for c in bai["cau"])
    with st.container(key="ket_qua_bai"):
        nhan = ""
        if bai["la_de"]:
            nhan = ('<span class="ket-luan dat">Đạt</span>' if dung >= NGUONG_DAT * so_cau
                    else '<span class="ket-luan chua">Chưa đạt</span>')
        st.markdown(f'<h3 style="margin:0">{esc(bai["ten"])}</h3>'
                    f'<div class="diem-lon">{dung}<small> / {so_cau} câu đúng</small>{nhan}</div>' + vach_tien_do(bai),
                    unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Số câu đúng", f"{dung} / {so_cau}")
        c2.metric("Số câu sai", so_cau - dung - bo_qua)
        c3.metric("Bỏ qua / hết giờ", bo_qua)
        if bai["la_de"]:
            if dung >= NGUONG_DAT * so_cau:
                st.success(f"ĐẠT: bạn trả lời đúng {dung}/{so_cau} câu (yêu cầu từ {int(NGUONG_DAT * 100)}%).")
            else:
                st.error(f"CHƯA ĐẠT: bạn trả lời đúng {dung}/{so_cau} câu (yêu cầu từ {int(NGUONG_DAT * 100)}%). "
                         "Xem lại các câu chưa đúng bên dưới rồi làm lại.")
        k1, k2 = st.columns(2)
        if k1.button("🔁 Làm lại bài này", width="stretch", type="primary"):
            t = bai["tham_so"]
            bat_dau_bai(*t[:5], seed=random.random())
            st.rerun()
        if k2.button("🏠 Về màn hình chọn bài", width="stretch"):
            st.session_state.bai = None
            st.rerun()
    sai = [c for c in bai["cau"] if c["tra_loi"] != c["dung"]]
    if sai:
        st.markdown(f"#### {len(sai)} câu cần xem lại")
        for c in sai:
            with st.container(border=True):
                a, b = st.columns([1, 6], vertical_alignment="center")
                a.image(ANH_MAU[c["dung"]][0], width=84)
                ban_chon = "Bỏ qua" if c["tra_loi"] == "bo_qua" else f"{ten_bien(c['tra_loi'])}"
                b.markdown(f'<span class="bien-so">{esc(ky_hieu(c["dung"]))}</span> <b>{esc(ten_bien(c["dung"]))}</b>'
                           f'<div class="chu-phu" style="margin:.3rem 0 .2rem">Bạn chọn: {esc(ban_chon)}</div>'
                           f'<div>{esc(thong_tin(c["dung"])["y_nghia"])}</div>', unsafe_allow_html=True)


def ve_cau_hoi(bai):
    with st.container(key="cau_hoi"):
        _ve_cau_hoi(bai)


def _ve_cau_hoi(bai):
    i = bai["hien"]
    cau = bai["cau"][i]
    so_cau = len(bai["cau"])
    dung_tam = sum(c["tra_loi"] == c["dung"] for c in bai["cau"][:i + 1])
    t1, t2 = st.columns([3, 1], vertical_alignment="center")
    t1.markdown(f'<div class="dau-cau"><span class="chu-bien">{esc(bai["ten"])}</span>'
                f'<span class="chu-phu">Câu {i + 1}/{so_cau}, đúng {dung_tam}</span></div>', unsafe_allow_html=True)
    if bai["han"]:
        with t2:
            dong_ho(bai["han"])
    st.markdown(vach_tien_do(bai), unsafe_allow_html=True)
    da_tl = cau["tra_loi"] is not None
    nhan = "ABCD"

    if cau["dang"] == "chon_ten":
        c_anh, c_dap = st.columns([2, 3], gap="large")
        with c_anh:
            with st.container(key="nen_bien_cau"):
                st.image(ANH_MAU[cau["dung"]][0], width="stretch")
        with c_dap:
            st.markdown('<div class="cau-hoi">Đây là biển báo gì?</div>', unsafe_allow_html=True)
            for k, m in enumerate(cau["lua_chon"]):
                nhan_nut = f"{nhan[k]}.  {ten_bien(m)}"
                if not da_tl:
                    if st.button(nhan_nut, key=f"tl_{id(bai)}_{i}_{k}", width="stretch"):
                        ghi_ket_qua(cau, m)
                        st.rerun()
                else:
                    lop = "dung" if m == cau["dung"] else ("sai" if m == cau["tra_loi"] else "")
                    dau = "✓ " if m == cau["dung"] else ("✗ " if m == cau["tra_loi"] else "")
                    st.markdown(f'<div class="dap-an {lop}">{dau}{esc(nhan_nut)}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="cau-hoi">Biển “{esc(ten_bien(cau["dung"]))}” là biển nào?</div>', unsafe_allow_html=True)
        cot = st.columns(4)
        for k, m in enumerate(cau["lua_chon"]):
            with cot[k]:
                st.image(ANH_MAU[m][0], width="stretch")
                if not da_tl:
                    if st.button(nhan[k], key=f"tl_{id(bai)}_{i}_{k}", width="stretch"):
                        ghi_ket_qua(cau, m)
                        st.rerun()
                else:
                    lop = "dung" if m == cau["dung"] else ("sai" if m == cau["tra_loi"] else "")
                    chu = "✓ Đúng" if m == cau["dung"] else ("✗ Bạn chọn" if m == cau["tra_loi"] else nhan[k])
                    st.markdown(f'<div class="dap-an {lop}" style="text-align:center">{chu}</div>', unsafe_allow_html=True)

    if da_tl:
        tt = thong_tin(cau["dung"])
        if cau["tra_loi"] == cau["dung"]:
            st.success(f"Chính xác. {ten_bien(cau['dung'])} (ký hiệu {ky_hieu(cau['dung'])}).")
        elif cau["tra_loi"] == "bo_qua":
            st.warning(f"Bạn đã bỏ qua câu này. Đáp án: {ten_bien(cau['dung'])}.")
        else:
            st.error(f"Chưa đúng. Đáp án là {nhan[cau['lua_chon'].index(cau['dung'])]}. {ten_bien(cau['dung'])}.")
        st.markdown(f'<div class="giai-thich"><b>Ý nghĩa:</b> {esc(tt["y_nghia"])}</div>', unsafe_allow_html=True)

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


def ve_lich_su():
    """Lịch sử học tập lưu lâu dài theo biệt danh: bảng kết quả, đồ thị tiến bộ, các biển hay nhầm."""
    ss = st.session_state
    bd = st.text_input("Biệt danh để lưu tiến độ học (không bắt buộc, không dùng họ tên thật)",
                       value=ss.get("biet_danh", ""), max_chars=30, placeholder="ví dụ: hoc_lai_xe_01")
    ss.biet_danh = bd.strip()
    if not ss.biet_danh:
        st.markdown('<p class="chu-phu">Đặt biệt danh để kết quả các bài được lưu lại và xem được tiến bộ qua nhiều lần học.</p>',
                    unsafe_allow_html=True)
        return
    ls = dl.lich_su_cua(ss.biet_danh)
    if not ls:
        st.markdown('<p class="chu-phu">Chưa có bài nào được lưu với biệt danh này. Kết quả sẽ được lưu khi bạn nộp bài.</p>',
                    unsafe_allow_html=True)
        return
    ti_le = [int(r["dung"]) / max(int(r["so_cau"]), 1) * 100 for r in ls]
    st.markdown(f"**{len(ls)} bài đã làm**, trung bình {sum(ti_le) / len(ti_le):.0f}% câu đúng; "
                f"bài gần nhất {ti_le[-1]:.0f}%" + (f", bài đầu tiên {ti_le[0]:.0f}%." if len(ls) > 1 else "."))
    if len(ls) > 1:
        st.line_chart({"% câu đúng": ti_le}, height=170, x_label="Lần làm bài", y_label="% đúng")
    with st.expander("Xem các bài đã làm"):
        st.dataframe([{"Thời gian": r["thoi_gian"], "Bài": r["ten_bai"], "Đúng": f'{r["dung"]}/{r["so_cau"]}',
                       "Kết quả": r["dat"] or "–"} for r in reversed(ls)], hide_index=True, width="stretch")
    dem = {}
    for r in ls:
        for m in r["bien_sai"].split():
            dem[m] = dem.get(m, 0) + 1
    nguoc = {v: k for k, v in MA_BIEN.items()}
    hay_sai = [nguoc[m] for m, _ in sorted(dem.items(), key=lambda x: -x[1]) if m in nguoc][:4]
    if hay_sai:
        st.markdown("**Các biển bạn hay nhầm nhất**")
        cot = st.columns(4)
        for c, m in zip(cot, hay_sai):
            c.image(ANH_MAU[m][0], width="stretch")
            c.caption(f"{ky_hieu(m)} · sai {dem[MA_BIEN[m]]} lần")


def ve_thong_ke():
    ss = st.session_state
    st.markdown("#### Kết quả học tập của bạn")
    if not ss.thong_ke:
        st.markdown('<p class="chu-phu">Thống kê sẽ hiện sau khi bạn trả lời câu hỏi đầu tiên.</p>', unsafe_allow_html=True)
        return
    tong_dung = sum(v[0] for v in ss.thong_ke.values())
    tong = sum(v[1] for v in ss.thong_ke.values())
    st.markdown(f"Đã trả lời **{tong}** câu, đúng **{tong_dung}** câu ({tong_dung / tong * 100:.0f}%). "
                f"Đã luyện **{len(ss.get('da_hoi', set()))}/{len(CAC_LOP)}** biển khác nhau.")
    o = []
    for n in THU_TU_NHOM:
        if n in ss.thong_ke:
            d, t = ss.thong_ke[n]
            o.append(f'<div class="tk-nhom"><div class="hang"><span>{esc(n)}</span><b>{d}/{t} đúng ({d / t * 100:.0f}%)</b></div>'
                     f'<div class="thanh"><span style="width:{d / t * 100:.0f}%;background:{MAU_CSS[MA_NHOM_CSS[n]]}"></span></div></div>')
    st.markdown("".join(o), unsafe_allow_html=True)
    st.caption("Kết quả được giữ trong phiên làm việc; tải lại trang sẽ bắt đầu lại từ đầu.")


def ve_chon_bai():
    ss = st.session_state
    c_trai, c_phai = st.columns([3, 2], gap="large")
    with c_trai:
        st.markdown(f'<p class="chu-phu">Ngân hàng câu hỏi: {len(CAC_LOP)} biển × 2 dạng câu (cho hình chọn tên, cho tên '
                    f'chọn hình) = {2 * len(CAC_LOP)} câu gốc; vị trí đáp án và đáp án gây nhiễu (cùng nhóm biển) được '
                    'trộn ngẫu nhiên mỗi lần làm.</p>', unsafe_allow_html=True)
        che_do = st.segmented_control("Chọn cách luyện tập", ["📝 Thi thử theo bộ đề", "🎯 Luyện theo nhóm biển", "🔁 Ôn lại câu sai"],
                                      default="📝 Thi thử theo bộ đề") or "📝 Thi thử theo bộ đề"
        co_chon_hinh = st.checkbox("Có cả câu hỏi “cho tên biển, chọn hình đúng”", value=True)
        if che_do.startswith("📝"):
            de = danh_sach_de()
            st.markdown(f'<p class="chu-phu">{len(CAC_LOP)} biển chia thành {len(de)} bộ đề cố định, mỗi đề tối đa '
                        f'{SO_CAU_MOI_DE} câu, làm trong {THOI_GIAN_DE // 60} phút. Đúng từ {int(NGUONG_DAT * 100)}% là Đạt; '
                        f'làm hết {len(de)} đề là đã ôn đủ mọi biển.</p>', unsafe_allow_html=True)
            so = st.pills("Chọn đề", list(range(1, len(de) + 1)), default=1, format_func=lambda k: f"Đề {k}") or 1
            if st.button(f"Bắt đầu Đề {so}", type="primary"):
                bat_dau_bai(f"Đề {so}", de[so - 1], co_chon_hinh, THOI_GIAN_DE, la_de=True, seed=so)
                st.rerun()
        elif che_do.startswith("🎯"):
            co_nhom = [n for n in THU_TU_NHOM if any(nhom_cua(m) == n for m in CAC_LOP)]
            nhom = st.pills("Nhóm biển", ["Tất cả"] + co_nhom, default="Tất cả") or "Tất cả"
            so_cau = st.pills("Số câu", [10, 20, 30], default=10) or 10
            st.markdown('<p class="chu-phu">Câu hỏi ưu tiên những biển bạn chưa gặp trong phiên học này.</p>', unsafe_allow_html=True)
            if st.button("Bắt đầu luyện tập", type="primary"):
                nguon = [m for m in CAC_LOP if nhom == "Tất cả" or nhom_cua(m) == nhom]
                da_hoi = ss.get("da_hoi", set())
                chua_hoi = [m for m in nguon if m not in da_hoi]
                k = min(so_cau, len(nguon))
                chon = random.sample(chua_hoi, min(k, len(chua_hoi)))
                if len(chon) < k:
                    chon += random.sample([m for m in nguon if m not in chon], k - len(chon))
                bat_dau_bai(f"Luyện tập – {nhom}", chon, co_chon_hinh)
                st.rerun()
        else:
            if not ss.cau_sai:
                st.info("Chưa có biển nào cần ôn. Làm một bộ đề hoặc luyện theo nhóm trước, các câu sai sẽ được gom vào đây.")
            else:
                st.markdown(f'<p class="chu-phu">Bạn có {len(ss.cau_sai)} biển trả lời sai hoặc bỏ qua. '
                            'Trả lời đúng biển nào thì biển đó rời khỏi danh sách.</p>', unsafe_allow_html=True)
                if st.button("Bắt đầu ôn câu sai", type="primary"):
                    bat_dau_bai("Ôn lại câu sai", random.sample(sorted(ss.cau_sai), len(ss.cau_sai)), co_chon_hinh)
                    st.rerun()
    with c_phai:
        with st.container(key="khung_thong_ke"):
            ve_thong_ke()
            st.divider()
            st.markdown("#### Tiến độ qua các lần học")
            ve_lich_su()


def trang_luyen_tap():
    st.markdown('<div class="tieu-de-trang"><h2>Luyện tập</h2><p>Thi thử theo bộ đề, luyện theo nhóm biển hoặc ôn lại các câu sai.</p></div>',
                unsafe_allow_html=True)
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


# ---------- Tab 4: Đánh giá & góp ý (khảo sát trải nghiệm người học) ----------
MUC_DO = {1: "1 · Rất không đồng ý", 2: "2", 3: "3 · Bình thường", 4: "4", 5: "5 · Rất đồng ý"}
def trang_danh_gia():
    st.markdown('<div class="tieu-de-trang"><h2>Góp ý</h2><p>Khảo sát trải nghiệm người học và tổng hợp đánh giá ứng dụng.</p></div>',
                unsafe_allow_html=True)
    ss = st.session_state
    c_trai, c_phai = st.columns([3, 2], gap="large")
    with c_trai:
        st.markdown("#### Khảo sát trải nghiệm người học")
        st.markdown('<p class="chu-phu">Sau khi dùng thử các chức năng, bạn vui lòng cho biết mức độ đồng ý với từng câu '
                    '(1 = rất không đồng ý, 5 = rất đồng ý). Khảo sát ẩn danh, mất khoảng 3 phút.</p>', unsafe_allow_html=True)
        if ss.get("da_khao_sat"):
            st.success("Cảm ơn bạn đã tham gia khảo sát!")
        else:
            with st.form("khao_sat"):
                bang_lai = st.radio("Bạn đã có giấy phép lái xe chưa?", ["Chưa có, đang ôn thi", "Chưa có", "Đã có"], horizontal=True)
                st.markdown("**Phần 1. Mức độ dễ sử dụng**")
                sus = [st.radio(f"{i + 1}. {c}", list(MUC_DO), format_func=MUC_DO.get, horizontal=True, index=None, key=f"sus_{i}")
                       for i, c in enumerate(dl.CAU_SUS)]
                st.markdown("**Phần 2. Hiệu quả học tập**")
                hoc = [st.radio(f"{i + 11}. {c}", list(MUC_DO), format_func=MUC_DO.get, horizontal=True, index=None, key=f"hoc_{i}")
                       for i, c in enumerate(dl.CAU_HOC)]
                thich = st.text_area("Điều bạn thích nhất ở ứng dụng", max_chars=500)
                cai_thien = st.text_area("Điều cần cải thiện", max_chars=500)
                if st.form_submit_button("Gửi khảo sát", type="primary"):
                    if None in sus or None in hoc:
                        st.error("Bạn vui lòng chọn mức độ cho tất cả các câu từ 1 đến 15.")
                    else:
                        dl.ghi_khao_sat(bang_lai, sus, hoc, thich.strip(), cai_thien.strip())
                        ss.da_khao_sat = True
                        st.rerun()
    with c_phai:
        with st.container(key="khung_tong_hop"):
            st.markdown("#### Tổng hợp đánh giá")
            ks = dl.doc_bang("khao_sat.csv")
            if ks:
                cot_s = [c for c in dl.COT_KHAO_SAT if c.startswith("[S")]
                cot_h = [c for c in dl.COT_KHAO_SAT if c.startswith("[H")]
                sus_tb = sum(dl.diem_sus([int(r[c]) for c in cot_s]) for r in ks) / len(ks)
                st.metric("Điểm khả dụng SUS (0–100, chuẩn 68)", f"{sus_tb:.1f}", help=f"{len(ks)} người trả lời")
                o = []
                for i, c in enumerate(cot_h):
                    tb = sum(int(r[c]) for r in ks) / len(ks)
                    o.append(f'<div class="diem"><div class="hang"><span>Câu {i + 11}. {esc(dl.CAU_HOC[i])}</span><b>{tb:.2f}/5</b></div>'
                             f'<div class="thanh"><span style="width:{(tb - 1) / 4 * 100:.0f}%"></span></div></div>')
                st.markdown("".join(o), unsafe_allow_html=True)
                st.caption(f"{len(ks)} người trả lời; điểm trung bình trên thang 1–5.")
            else:
                st.markdown('<p class="chu-phu">Chưa có câu trả lời khảo sát.</p>', unsafe_allow_html=True)
            ph = dl.doc_bang("phan_hoi_nhan_dang.csv")
            if ph:
                d = sum(r["danh_gia"] == "dung" for r in ph)
                st.metric("Nhận dạng ảnh được xác nhận đúng", f"{d}/{len(ph)} ({d / len(ph) * 100:.0f}%)")
            ls = dl.doc_bang("lich_su_hoc.csv")
            if ls:
                st.metric("Bài luyện tập đã lưu", f"{len(ls)} bài", help=f"{len({r['biet_danh'] for r in ls})} người học")



# ======================= TRANG CHỦ (bảng điều khiển) =======================
def di_toi(trang, **gia_tri):
    ss_ = st.session_state
    if ss_.get("trang") != trang:
        ss_.setdefault("lich_su_trang", []).append(ss_.get("trang", "trang_chu"))
        ss_.lich_su_trang = ss_.lich_su_trang[-20:]
    ss_.trang = trang
    for k, v in gia_tri.items():
        st.session_state[k] = v


SVG_DUONG = ("data:image/svg+xml;utf8," + """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 600 260' preserveAspectRatio='xMidYMax slice'>
<defs><linearGradient id='t' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='%23CFE6FF'/><stop offset='1' stop-color='%23F2F8FF'/></linearGradient></defs>
<rect width='600' height='260' fill='url(%23t)'/>
<path d='M0 150 C120 110 220 130 320 115 S520 100 600 120 L600 260 L0 260Z' fill='%2397C77A'/>
<path d='M0 175 C150 150 300 165 600 150 L600 260 L0 260Z' fill='%236FAE5A'/>
<path d='M300 128 L330 128 L520 260 L120 260Z' fill='%234A5568'/>
<path d='M313 135 L317 135 L318 150 L312 150Z M309 165 L321 165 L324 190 L306 190Z M302 205 L328 205 L334 245 L296 245Z' fill='%23FFFFFF' opacity='.9'/>
</svg>""").replace("\n", "").replace("#", "%23")


# Ảnh bìa: đặt ảnh của bạn tại giao_dien/anh_bia.jpg (hoặc .png, .webp). Không có ảnh thì dùng hình con đường vẽ sẵn.
HIEN_BIEN_TREN_ANH_BIA = False     # False nếu ảnh bìa của bạn đã có sẵn biển báo


@st.cache_data
def _doc_anh_bia(duong_dan, thoi_diem_sua):
    a = ImageOps.exif_transpose(Image.open(duong_dan)).convert("RGB")
    a.thumbnail((1600, 1600))                      # thu nhỏ để trang tải nhanh
    buf = io.BytesIO(); a.save(buf, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def anh_bia():
    for duoi in ("jpg", "jpeg", "png", "webp"):
        p = os.path.join(GOC, "giao_dien", f"anh_bia.{duoi}")
        if os.path.exists(p):
            return _doc_anh_bia(p, os.path.getmtime(p)), True
    return SVG_DUONG, False


def the_tinh_nang(i, bieu_tuong, ten, mo_ta, trang):
    with st.container(key=f"tinh_nang_{i}"):
        st.markdown(f'<div class="o-bieu-tuong">{bieu_tuong}</div><div class="ten-the">{ten}</div><div class="mo-ta-the">{mo_ta}</div>',
                    unsafe_allow_html=True)
        st.button("→", key=f"mo_{trang}", on_click=di_toi, args=(trang,), help=f"Mở {ten}")


def bai_tap_nhanh():
    ss = st.session_state
    if "cau_nhanh" not in ss:
        rng = random.Random()
        ss.cau_nhanh = tao_cau(rng.choice(CAC_LOP), rng, False)
    cau = ss.cau_nhanh
    with st.container(key="khung_bai_nhanh"):
        h1, h2 = st.columns([3, 1.3], vertical_alignment="center")
        h1.markdown('<div class="dau-khung" style="margin:0"><span class="o-nho">📝</span><b>Bài tập nhanh</b></div>', unsafe_allow_html=True)
        h2.button("Tất cả", key="xem_tat_ca_bt", icon=":material/arrow_forward:", type="tertiary",
                  on_click=di_toi, args=("luyen_tap",))
        c1, c2 = st.columns([1, 1.55], vertical_alignment="top", gap="small")
        with c1:
            with st.container(key="nen_bien_nhanh"):
                st.image(ANH_MAU[cau["dung"]][0], width="stretch")
        with c2:
            st.markdown('<div class="cau-nhanh">Biển báo này có ý nghĩa gì?</div>', unsafe_allow_html=True)
            nhan = "ABCD"
            chon = st.radio("Chọn đáp án", list(range(4)), format_func=lambda k: f"{nhan[k]}. {ten_bien(cau['lua_chon'][k])}",
                            index=None, key=f"nhanh_{cau['dung']}", label_visibility="collapsed", disabled=cau["tra_loi"] is not None)
        if cau["tra_loi"] is None:
            if st.button("Kiểm tra →", type="primary", width="stretch", disabled=chon is None, key="kiem_tra_nhanh"):
                ghi_ket_qua(cau, cau["lua_chon"][chon])
                st.rerun()
        else:
            if cau["tra_loi"] == cau["dung"]:
                st.success(f"Chính xác! {ten_bien(cau['dung'])} ({ky_hieu(cau['dung'])}).")
            else:
                st.error(f"Chưa đúng. Đáp án: {ten_bien(cau['dung'])} ({ky_hieu(cau['dung'])}).")
            st.markdown(f'<div class="giai-thich" style="margin:.2rem 0 .6rem">{esc(thong_tin(cau["dung"])["y_nghia"])}</div>',
                        unsafe_allow_html=True)
            if st.button("Câu khác →", type="primary", width="stretch", key="cau_khac"):
                del ss.cau_nhanh
                st.rerun()


def trang_chu():
    ss = st.session_state
    trai, phai = st.columns([1.85, 1], gap="medium")
    with trai:
        # --- Ảnh bìa ---
        nen, la_anh_that = anh_bia()
        bien = "".join(f'<img class="bb{i}" alt="" src="data:image/png;base64,{anh_base64(ANH_MAU[m][0], 160, True)}">'
                       for i, m in enumerate(x for x in [_ma("P.102"), _ma("P.127-60"), _ma("R.301a"), _ma("W.224")] if x)
                       ) if HIEN_BIEN_TREN_ANH_BIA else ""
        with st.container(key="anh_bia"):
            st.markdown(f'<div class="bia-anh{" anh-that" if la_anh_that else ""}" '
                        f'style="background-image:url(&quot;{nen}&quot;)">{bien}</div>'
                        '<h1 class="bia-tieu-de">Cùng tìm hiểu<br>và nhận dạng biển báo giao thông!</h1>'
                        '<p class="bia-phu">Học · Nhận diện · Ghi nhớ · An toàn trên mọi hành trình</p>', unsafe_allow_html=True)
            st.button("▶  Bắt đầu học ngay", key="bat_dau_hoc", type="primary", on_click=di_toi, args=("thu_vien",))
        # --- Bốn chức năng ---
        with st.container(key="khung_tinh_nang"):
            cot = st.columns(4)
            for i, (c, (bt, ten, mt, tr)) in enumerate(zip(cot, [
                    ("📘", "Học lý thuyết", "Khám phá các nhóm biển báo và ý nghĩa", "thu_vien"),
                    ("📷", "Nhận dạng biển báo", "Dùng camera hoặc ảnh để nhận diện", "nhan_dang"),
                    ("📝", "Luyện tập", "Làm bài trắc nghiệm, thi thử theo bộ đề", "luyen_tap"),
                    ("📊", "Xem kết quả", "Theo dõi tiến độ học tập của bạn", "ket_qua")])):
                with c:
                    the_tinh_nang(i, bt, ten, mt, tr)
        # --- Các nhóm biển báo ---
        with st.container(key="khung_nhom"):
            st.markdown('<div class="dau-khung"><span class="o-nho">⚠️</span><b>Các nhóm biển báo</b></div>', unsafe_allow_html=True)
            cot = st.columns(5)
            for c, (n, m, so) in zip(cot, _bien_dai_dien()):
                with c:
                    with st.container(key=f"nhom_{MA_NHOM_CSS[n]}"):
                        st.markdown(f'<div style="text-align:center"><img alt="" style="height:62px" '
                                    f'src="data:image/png;base64,{anh_base64(ANH_MAU[m][0], 124, True)}"></div>'
                                    f'<div class="ten-the" style="text-align:center;margin-top:.4rem">{TEN_NGAN_NHOM.get(n, n)}</div>'
                                    f'<div class="mo-ta-the" style="text-align:center">({so} biển)</div>', unsafe_allow_html=True)
                        st.button("Xem chi tiết", key=f"xem_nhom_{MA_NHOM_CSS[n]}", width="stretch",
                                  on_click=di_toi, args=("thu_vien",), kwargs={"loc_nhom": n})
        # --- Thống kê học tập ---
        with st.container(key="khung_thong_ke_nhanh"):
            st.markdown('<div class="dau-khung"><span class="o-nho">📈</span><b>Thống kê học tập</b></div>', unsafe_allow_html=True)
            tk = ss.get("thong_ke", {})
            d, t = sum(v[0] for v in tk.values()), sum(v[1] for v in tk.values())
            phut = int((time.time() - ss.bat_dau_phien) // 60)
            the = [("📚", "Tổng số biển báo", f"{len(CAC_LOP)}", "biển báo", None),
                   ("🎯", "Đã học", f"{len(ss.get('da_hoi', set()))}", "biển báo", None),
                   ("✅", "Độ chính xác", f"{d / t * 100:.0f}%" if t else "–", f"{d}/{t} câu đúng" if t else "chưa làm bài", d / t if t else 0),
                   ("⏱️", "Thời gian học", f"{phut // 60} giờ {phut % 60} phút" if phut >= 60 else f"{phut} phút", "trong phiên này", None)]
            for c, (bt, ten, gt, phu, tl) in zip(st.columns(4), the):
                thanh = f'<div class="thanh-mini"><span style="width:{tl * 100:.0f}%"></span></div>' if tl is not None else ""
                c.markdown(f'<div class="o-thong-ke"><span class="o-nho">{bt}</span><div><div class="mo-ta-the">{ten}</div>'
                           f'<div class="so-lon">{gt}</div><div class="mo-ta-the">{phu}</div>{thanh}</div></div>', unsafe_allow_html=True)
    with phai:
        with st.container(key="khung_nhan_dang_nhanh"):
            h1, h2 = st.columns([3, 1.3], vertical_alignment="center")
            h1.markdown('<div class="dau-khung" style="margin:0"><span class="o-nho">📷</span><b>Nhận dạng biển báo</b></div>',
                        unsafe_allow_html=True)
            h2.button("Mở trang", key="mo_trang_nd", icon=":material/chevron_right:", type="tertiary",
                      on_click=di_toi, args=("nhan_dang",))
            st.button("Nhấn vào đây để mở camera", key="mo_camera", icon=":material/photo_camera:", width="stretch",
                      on_click=di_toi, args=("nhan_dang",), kwargs={"nguon_anh": "Chụp bằng webcam", "anh_nhanh": None})
            st.markdown('<div class="chu-hoac"><span>Hoặc</span></div>', unsafe_allow_html=True)
            tep = st.file_uploader("Tải ảnh lên", type=["jpg", "jpeg", "png", "webp"], key="tai_nhanh", label_visibility="collapsed")
            if tep is not None and ss.get("id_anh_nhanh") != tep.file_id:
                ss.id_anh_nhanh = tep.file_id
                ss.anh_nhanh = tep.getvalue()
                di_toi("nhan_dang", nguon_anh="Tải ảnh lên")
                st.rerun()
            st.markdown('<div class="goi-y">💡 Hỗ trợ ảnh chụp hoặc ảnh có sẵn trên thiết bị (JPG, PNG, tối đa 5 MB). '
                        'Ảnh chỉ được xử lý tạm thời, không lưu lại.</div>', unsafe_allow_html=True)
        bai_tap_nhanh()


def trang_ket_qua():
    st.markdown('<div class="tieu-de-trang"><h2>Kết quả học tập</h2><p>Thống kê trong phiên làm việc và tiến độ qua các lần học.</p></div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        with st.container(key="khung_kq_phien"):
            ve_thong_ke()
    with c2:
        with st.container(key="khung_kq_lich_su"):
            st.markdown("#### Tiến độ qua các lần học")
            ve_lich_su()


def trang_cai_dat():
    ss = st.session_state
    st.markdown('<div class="tieu-de-trang"><h2>Cài đặt</h2><p>Thông tin người học và thông tin về ứng dụng.</p></div>',
                unsafe_allow_html=True)
    with st.container(key="khung_cai_dat"):
        bd = st.text_input("Biệt danh (dùng để lưu tiến độ học, không dùng họ tên thật)", value=ss.get("biet_danh", ""), max_chars=30)
        ss.biet_danh = bd.strip()
        st.markdown(f"""<div class="muc"><b>Về ứng dụng</b><p>Nhận dạng {len(CAC_LOP)} biển báo theo QCVN 41:2024/BGTVT bằng mạng
nơron nhiều lớp (3.072 – 512 – 256 – 340) tự cài đặt với thuật toán lan truyền ngược. Ngưỡng cảnh báo điểm Softmax hiện tại:
{NGUONG_TIN_CAY:.2f}.</p></div><div class="muc"><b>Quyền riêng tư</b><p>Ảnh tải lên chỉ được xử lý trong bộ nhớ và không được lưu.
Ứng dụng chỉ lưu kết quả luyện tập (theo biệt danh), xác nhận đúng/sai của kết quả nhận dạng và câu trả lời khảo sát ẩn danh.</p></div>""",
                    unsafe_allow_html=True)


def _ma(ma_qcvn):
    return next((k for k, v in MA_BIEN.items() if v == ma_qcvn), None)


# ======================= THANH BÊN VÀ ĐIỀU HƯỚNG =======================
TRANG = [("trang_chu", "Trang chủ", ":material/home:", trang_chu),
         ("thu_vien", "Học lý thuyết", ":material/menu_book:", trang_thu_vien),
         ("nhan_dang", "Nhận dạng biển báo", ":material/photo_camera:", trang_nhan_dang),
         ("luyen_tap", "Luyện tập", ":material/assignment:", trang_luyen_tap),
         ("ket_qua", "Kết quả", ":material/bar_chart:", trang_ket_qua),
         ("danh_gia", "Góp ý", ":material/rate_review:", trang_danh_gia)]
ss = st.session_state
ss.setdefault("trang", "trang_chu")
ss.setdefault("bat_dau_phien", time.time())
ss.setdefault("bai", None)
ss.setdefault("cau_sai", set())
ss.setdefault("thong_ke", {})
with st.sidebar:
    st.markdown('<div class="logo"><span class="logo-bien"></span><div>Nhận dạng<br>biển báo giao thông</div></div>', unsafe_allow_html=True)
    for k, ten, bt, _ in TRANG:
        st.button(ten, key=f"menu_{k}", icon=bt, width="stretch", type="primary" if ss.trang == k else "secondary",
                  on_click=di_toi, args=(k,))
    with st.container(key="menu_duoi"):
        st.button("Cài đặt", key="menu_cai_dat", icon=":material/settings:", width="stretch",
                  type="primary" if ss.trang == "cai_dat" else "secondary", on_click=di_toi, args=("cai_dat",))
def quay_lai():
    ls_ = st.session_state.get("lich_su_trang", [])
    st.session_state.trang = ls_.pop() if ls_ else "trang_chu"


c_lui, c_chao = st.columns([1, 1], vertical_alignment="center")
with c_lui:
    if ss.trang != "trang_chu":
        with st.container(key="thanh_quay_lai"):
            b1, b2 = st.columns([1, 1.25], gap="small")
            b1.button("Quay lại", key="nut_quay_lai", icon=":material/arrow_back:", on_click=quay_lai)
            b2.button("Trang chủ", key="nut_ve_trang_chu", icon=":material/home:", on_click=di_toi, args=("trang_chu",))
c_chao.markdown(f'<div class="thanh-tren"><span class="avatar">👤</span>Xin chào, <b>{esc(ss.get("biet_danh") or "Học viên")}</b></div>',
                unsafe_allow_html=True)
{**{k: f for k, _, _, f in TRANG}, "cai_dat": trang_cai_dat}[ss.trang]()
