"use strict";
/* =========================================================================
   Ung dung "Bien Bao Giao Thong" - giao dien 1 trang, dinh tuyen bang #/...
   Du lieu hoc tap luu trong localStorage cua trinh duyet (khong gui di dau).
   ========================================================================= */

/* ---------------- tien ich ---------------- */
const $ = (s, g = document) => g.querySelector(s);
const $$ = (s, g = document) => [...g.querySelectorAll(s)];
const main = $("#noi-dung");
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pct1 = p => (p * 100).toFixed(1).replace(".", ",") + "%";
const ngu = ms => new Promise(r => setTimeout(r, ms));
const tron = a => { a = [...a]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const khongDau = s => String(s).normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();
const chuanTim = s => khongDau(s).replace(/[.,\s()_-]/g, "");
const kyHieu = ma => (ma.startsWith("DP") ? "p" : ma[0].toLowerCase());
const lopNhom = ma => "nhom-" + kyHieu(ma);
const TEN_LOAI = { p: "Biển cấm", w: "Biển nguy hiểm", r: "Biển hiệu lệnh", i: "Biển chỉ dẫn", s: "Biển phụ" };
const MAU_LOAI = { p: "#dc2b2b", w: "#f2b100", r: "#1d63e8", i: "#2f6f9f", s: "#64748b" };
const mmss = giay => `${String(Math.floor(giay / 60)).padStart(2, "0")}:${String(Math.max(0, giay % 60)).padStart(2, "0")}`;
const gio = t => new Date(t).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
const ngayGio = t => new Date(t).toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
const ngayStr = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
function diToi(hash) { if (location.hash === hash) dieuHuong(); else location.hash = hash; }

const ICON = {
  home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h5v-6h4v6h5V9.5"/>',
  book: '<path d="M2 4h7a3 3 0 0 1 3 3v14a2 2 0 0 0-2-2H2z"/><path d="M22 4h-7a3 3 0 0 0-3 3v14a2 2 0 0 1 2-2h8z"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
  scan: '<path d="M3 8V5a2 2 0 0 1 2-2h3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/><circle cx="12" cy="12" r="3.5"/>',
  camera: '<path d="M3 8a2 2 0 0 1 2-2h2.5L9 4h6l1.5 2H19a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><circle cx="12" cy="13" r="3.5"/>',
  "camera-off": '<path d="M3 8a2 2 0 0 1 2-2h2.5L9 4h6l1.5 2H19a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 3l18 18"/>',
  chart: '<path d="M3 21h18"/><path d="M6 17v-5M11 17V7M16 17v-8M20 17V4"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  "arrow-left": '<path d="M19 12H5M11 18l-6-6 6-6"/>',
  "arrow-right": '<path d="M5 12h14M13 6l6 6-6 6"/>',
  "chevron-left": '<path d="M15 6l-6 6 6 6"/>',
  "chevron-right": '<path d="M9 6l6 6-6 6"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 17-5-5-9 8"/>',
  shuffle: '<path d="M16 3h5v5M4 20 21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/>',
  "chevron-up": '<path d="M6 15l6-6 6 6"/>',
  "chevron-down": '<path d="M6 9l6 6 6-6"/>',
  bookmark: '<path d="M6 3h12v18l-6-4-6 4z"/>',
  grid: '<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7"/>',
  "check-circle": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/>',
  "x-circle": '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
  percent: '<path d="M19 5 5 19"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/>',
  upload: '<path d="M12 15V4M7 9l5-5 5 5"/><path d="M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
  video: '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="m16 10 5-3v10l-5-3z"/>',
  refresh: '<path d="M20 12a8 8 0 1 1-2.34-5.66"/><path d="M20 4v5h-5"/>',
  save: '<path d="M12 4v11M7 10l5 5 5-5"/><path d="M4 20h16"/>',
  trash: '<path d="M4 7h16M10 11v6M14 11v6"/><path d="M6 7l1 13h10l1-13M9 7V4h6v3"/>',
  volume: '<path d="M4 9h4l5-4v14l-5-4H4z"/><path d="M17 9a4 4 0 0 1 0 6"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  bulb: '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
  alert: '<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17h.01"/>',
};
const ic = (ten, lop = "ic") => `<svg class="${lop}" viewBox="0 0 24 24" aria-hidden="true">${ICON[ten] || ""}</svg>`;

/* ---------------- du lieu bien bao ---------------- */
const S = { bien: [], theoMa: {}, nguong: 0.5, ketQuaXem: null };
const anhBien = (ma, alt = "") => S.theoMa[ma]?.anh ? `<img src="${S.theoMa[ma].anh}" alt="${esc(alt)}" loading="lazy">` : `<span class="nhan-ma">${esc(ma)}</span>`;

const DAC_DIEM_LOAI = {
  p: ["Hình tròn, viền đỏ, nền trắng", "Hình vẽ màu đen thể hiện điều bị cấm"],
  w: ["Hình tam giác đều, viền đỏ, nền vàng", "Hình vẽ màu đen mô tả điều nguy hiểm phía trước"],
  r: ["Hình tròn, nền xanh lam", "Hình vẽ màu trắng chỉ điều bắt buộc phải làm"],
  i: ["Hình vuông hoặc chữ nhật, nền xanh lam", "Cung cấp thông tin, chỉ dẫn hướng đi"],
  s: ["Hình chữ nhật hoặc hình vuông", "Đặt ngay dưới biển chính để bổ sung thông tin"],
};
const DAC_DIEM_RIENG = {
  "P.102": ["Hình tròn, nền đỏ", "Một vạch ngang màu trắng ở giữa"],
  "P.130": ["Hình tròn, viền đỏ, nền xanh lam", "Hai vạch đỏ chéo nhau thành dấu X"],
  "P.131a": ["Hình tròn, viền đỏ, nền xanh lam", "Một vạch đỏ chéo"],
  "R.122": ["Hình bát giác (8 cạnh), nền đỏ", "Chữ STOP màu trắng ở giữa"],
  "W.208": ["Hình tam giác ngược (đỉnh chúc xuống), viền đỏ, nền vàng", "Không có hình vẽ bên trong"],
};
const MEO_LOAI = {
  p: "Vòng tròn viền đỏ là biển cấm: điều được vẽ bên trong là điều không được làm.",
  w: "Tam giác viền đỏ nền vàng là biển cảnh báo: phía trước có nguy hiểm, hãy giảm tốc độ và quan sát.",
  r: "Hình tròn nền xanh là biển hiệu lệnh: bắt buộc phải làm theo điều vẽ trên biển.",
  i: "Biển vuông nền xanh là biển chỉ dẫn: cho biết thông tin và hướng đi, không phải lệnh cấm.",
  s: "Biển phụ không đứng một mình: luôn đọc cùng biển chính đặt phía trên.",
};
const MEO_RIENG = {
  "P.130": "Dấu X đỏ (hai vạch) là cấm cả dừng lẫn đỗ; chỉ có một vạch (P.131a) thì chỉ cấm đỗ.",
  "P.131a": "Một vạch đỏ là cấm đỗ nhưng vẫn được dừng; hai vạch thành dấu X (P.130) là cấm cả dừng và đỗ.",
  "P.123a": "Mũi tên rẽ trái bị gạch là cấm mọi xe rẽ trái; có thêm hình ô tô (P.103c) thì chỉ cấm ô tô.",
  "P.103c": "Có hình ô tô trong biển nghĩa là lệnh cấm chỉ áp dụng cho ô tô.",
  "P.102": "Nền đỏ với vạch trắng nằm ngang giống một thanh chắn: không được đi vào theo chiều đặt biển.",
  "P.127": "Con số trên biển là tốc độ tối đa cho phép, tính bằng km/h.",
  "R.122": "Hình bát giác đỏ chữ STOP: bắt buộc dừng hẳn, quan sát an toàn rồi mới được đi tiếp.",
  "W.208": "Tam giác ngược là dấu hiệu bạn đang ở đường nhánh: phải nhường đường cho xe trên đường chính.",
  "W.207a": "Nét đậm là đường chính bạn đang đi (được ưu tiên), nét mảnh là đường nhánh nhập vào.",
  "W.207b": "Nét đậm là đường chính bạn đang đi (được ưu tiên), nét mảnh là đường nhánh nhập vào.",
  "W.207c": "Nét đậm là đường chính bạn đang đi (được ưu tiên), nét mảnh là đường nhánh nhập vào.",
  "W.224": "Hình người đi trên vạch kẻ: sắp đến chỗ người đi bộ qua đường, giảm tốc và nhường đường.",
  "W.225": "Hình hai em nhỏ: gần trường học hoặc khu vui chơi, đi chậm và quan sát kỹ.",
};
const LA_KHU_VUC = ma => ma.startsWith("R.E,");
const DAC_DIEM_KHU_VUC = ["Hình chữ nhật nền trắng, có chữ ZONE (khu vực) ở trên", "Hình biển bên dưới cho biết lệnh áp dụng cho cả khu vực"];
const DAC_DIEM_HET_CAM = ["Hình tròn, nền trắng, viền xanh lam", "Các vạch chéo màu đen: báo hết hiệu lực lệnh cấm"];
const dacDiem = b => [
  ...(b.ma.startsWith("DP") && !DAC_DIEM_RIENG[b.ma] ? DAC_DIEM_HET_CAM : []),
  ...(b.ma.startsWith("DP") && !DAC_DIEM_RIENG[b.ma] ? [] : (DAC_DIEM_RIENG[b.ma] || (LA_KHU_VUC(b.ma) ? DAC_DIEM_KHU_VUC : DAC_DIEM_LOAI[kyHieu(b.ma)])))];
/* noi dung chi tiet kieu "Cam doi tuong / Pham vi cam / Loai tru / Luu y" */
function khoiChiTiet(b) {
  const c = b.chi_tiet;
  if (!c) return "";
  const cam = (c.nhan_doi_tuong || "Cấm đối tượng") === "Cấm đối tượng";
  const o = (lop, icon, tieuDe, noiDung) => noiDung ? `<div class="o-tt"><span class="bieu-tuong ${lop}">${ic(icon)}</span><div><h3>${tieuDe}</h3><p>${esc(noiDung)}</p></div></div>` : "";
  return o("do", c.nhan_doi_tuong === "Hết hiệu lực" ? "info" : "x-circle", c.nhan_doi_tuong || "Cấm đối tượng", c.doi_tuong)
    + o("", "scan", cam ? "Phạm vi cấm" : "Phạm vi áp dụng", c.pham_vi)
    + o("la", "check-circle", "Loại trừ", c.loai_tru)
    + o("vang", "alert", "Lưu ý", c.luu_y);
}
const meo = b => MEO_RIENG[b.ma] || (b.ma.startsWith("DP") ? "Biển tròn có các vạch chéo màu đen là biển hết lệnh cấm: từ đây lệnh cấm tương ứng không còn hiệu lực."
  : LA_KHU_VUC(b.ma) ? "Có chữ ZONE là biển khu vực: lệnh có hiệu lực trong cả khu vực, đến khi gặp biển hết khu vực R.E,10 tương ứng." : MEO_LOAI[kyHieu(b.ma)]);
const MAU_SAC_LOAI = { p: "Đỏ, trắng, đen", w: "Đỏ, vàng, đen", r: "Xanh lam, trắng", i: "Xanh lam, trắng", s: "Trắng, đen hoặc xanh lam" };
const MAU_SAC_RIENG = { "P.102": "Đỏ, trắng", "P.130": "Đỏ, xanh lam", "P.131a": "Đỏ, xanh lam", "R.122": "Đỏ, trắng", "W.208": "Đỏ, vàng" };
const mauSac = b => MAU_SAC_RIENG[b.ma] || (b.ma.startsWith("DP") ? "Trắng, xanh lam, đen" : LA_KHU_VUC(b.ma) ? "Trắng, đen và màu của biển bên trong" : MAU_SAC_LOAI[kyHieu(b.ma)]);

function bienLienQuan(b, n = 4) {
  const goc = b.ma.replace(/\(\d+\)$/, "").replace(/[a-z]$/, "");
  return S.bien.filter(x => x.ma !== b.ma)
    .map(x => [x.ma.startsWith(goc) ? 0 : kyHieu(x.ma) === kyHieu(b.ma) ? 1 : 2, x])
    .sort((a, c) => a[0] - c[0] || a[1].ma.localeCompare(c[1].ma)).slice(0, n).map(t => t[1]);
}

/* ---------------- luu tru hoc tap ---------------- */
const KHO = "hbb_du_lieu_v2";
const macDinh = () => ({ ten: "Người học", da_hoc: {}, bai_tap: [], nhan_dang: [], ngay: [], cai_dat: { am_thanh: true, thong_bao: true, giao_dien: "tu-dong" } });
function docKho() {
  try {
    const x = JSON.parse(localStorage.getItem(KHO));
    if (x) return { ...macDinh(), ...x, cai_dat: { ...macDinh().cai_dat, ...(x.cai_dat || {}) } };
  } catch { /* du lieu hong -> dung mac dinh */ }
  const d = macDinh();
  try {   // chuyen lich su on tap cua phien ban truoc
    (JSON.parse(localStorage.getItem("hocbienbao_lich_su")) || []).forEach(l =>
      d.bai_tap.push({ thoi_gian: l.thoi_gian, ten: l.nhom, che_do: "luyen-tap", dung: l.dung, tong: l.tong, giay: 0, cau: [] }));
  } catch { /* bo qua */ }
  return d;
}
let D = docKho();
function luuKho() {
  try { localStorage.setItem(KHO, JSON.stringify(D)); }
  catch { thongBao("Bộ nhớ trình duyệt đã đầy. Hãy xóa bớt lịch sử nhận dạng trong trang Người học.", true); }
}
function ghiNgay() { const h = ngayStr(new Date()); if (!D.ngay.includes(h)) D.ngay = [...D.ngay, h].slice(-180); }
function danhDauDaHoc(ma) { if (!D.da_hoc[ma]) D.da_hoc[ma] = Date.now(); ghiNgay(); luuKho(); }
const soDaHoc = () => Object.keys(D.da_hoc).filter(m => S.theoMa[m]).length;

/* ---------------- giao dien chung ---------------- */
const mq = matchMedia("(prefers-color-scheme: dark)");
function apGiaoDien() {
  const g = D.cai_dat.giao_dien;
  document.documentElement.dataset.theme = g === "toi" || (g === "tu-dong" && mq.matches) ? "toi" : "sang";
}
mq.addEventListener("change", apGiaoDien);
let amCtx = null;
function phatAm(dung) {
  if (!D.cai_dat.am_thanh) return;
  try {
    amCtx = amCtx || new AudioContext();
    const o = amCtx.createOscillator(), g = amCtx.createGain(), t = amCtx.currentTime;
    o.frequency.setValueAtTime(dung ? 660 : 220, t);
    if (dung) o.frequency.setValueAtTime(880, t + 0.09);
    g.gain.setValueAtTime(0.12, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.3);
    o.connect(g).connect(amCtx.destination); o.start(t); o.stop(t + 0.31);
  } catch { /* trinh duyet khong ho tro am thanh */ }
}
let hThongBao = 0;
function thongBao(t, quanTrong = false) {
  if (!quanTrong && !D.cai_dat.thong_bao) return;
  const e = $("#thong-bao"); e.textContent = t; e.hidden = false;
  clearTimeout(hThongBao); hThongBao = setTimeout(() => { e.hidden = true; }, 3000);
}
function capNhatTenNho() { $("#ten-nho").textContent = D.ten; }
const trangThaiTrong = (icon, tieuDe, moTa) => `<div class="trang-thai-trong">${ic(icon)}<b>${esc(tieuDe)}</b><span>${esc(moTa)}</span></div>`;

const MENU = [["", "home", "Trang chủ"], ["hoc", "book", "Học biển báo"], ["bai-tap", "target", "Bài tập"],
  ["nhan-dang", "scan", "Nhận dạng"], ["thong-ke", "chart", "Thống kê"], ["gioi-thieu", "info", "Giới thiệu"]];
$("#menu").innerHTML = MENU.map(([r, i, t]) => `<a href="#/${r}" data-trang="${r}" title="${t}">${ic(i)}<span>${t}</span></a>`).join("");
function apThuGon() {
  const g = !!D.cai_dat.thu_gon, nut = $("#thu-gon");
  document.body.classList.toggle("thu-gon", g);
  nut.setAttribute("aria-expanded", String(!g));
  nut.setAttribute("aria-label", g ? "Mở rộng menu" : "Thu gọn menu");
  nut.title = g ? "Mở rộng menu" : "Thu gọn menu";
}
$("#thu-gon").onclick = () => { D.cai_dat.thu_gon = !D.cai_dat.thu_gon; luuKho(); apThuGon(); };

/* ---------------- dinh tuyen ---------------- */
function dieuHuong() {
  const phan = location.hash.replace(/^#\/?/, "").split("/").map(p => { try { return decodeURIComponent(p); } catch { return p; } });
  const trang = phan[0] || "";
  if (trang !== "nhan-dang") dungNhanDang();
  if (trang !== "") clearInterval(hChuyenAnh);
  $$("#menu a, .nguoi-hoc-nho").forEach(a => a.classList.toggle("dang-xem", a.dataset.trang === trang));
  const bang = {
    "": veTrangChu,
    hoc: () => (phan[1] ? veChiTiet(phan[1]) : veThuVien()),
    "bai-tap": () => veBaiTap(phan[1]),
    "nhan-dang": () => (phan[1] === "ket-qua" ? veKetQuaNhanDang() : veNhanDang()),
    "thong-ke": veThongKe, "gioi-thieu": veGioiThieu, "nguoi-hoc": veNguoiHoc,
  };
  (bang[trang] || veTrangChu)();
  window.scrollTo(0, 0);
  main.focus({ preventScroll: true });
}

/* =========================== 1. TRANG CHU =========================== */
const MINH_HOA = `<svg class="tranh-nen" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <linearGradient id="tn-troi" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b7d3fb"/><stop offset=".45" stop-color="#e9f2ff"/></linearGradient>
    <linearGradient id="tn-co" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#97cf78"/><stop offset="1" stop-color="#4f8f39"/></linearGradient>
    <linearGradient id="tn-duong" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8d98a6"/><stop offset="1" stop-color="#434c58"/></linearGradient>
    <linearGradient id="tn-kinh" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#617a98"/><stop offset="1" stop-color="#1f2c3b"/></linearGradient>
  </defs>
  <rect width="1600" height="1000" fill="url(#tn-troi)"/>
  <g fill="#fff" opacity=".75"><ellipse cx="1010" cy="120" rx="150" ry="28"/><ellipse cx="1090" cy="100" rx="90" ry="26"/><ellipse cx="1420" cy="170" rx="110" ry="22"/><ellipse cx="560" cy="330" rx="130" ry="20"/></g>
  <path d="M0 410 160 340l140 40 170-70 170 80 150-50 160 60 170-70 190 64 160-48 130 40v84H0z" fill="#b6cbe8"/>
  <path d="M0 440 220 392l200 34 210-40 200 46 220-30 240 40 220-36 290 30v54H0z" fill="#a5bfe3"/>
  <g fill="#9db7de"><rect x="842" y="350" width="30" height="86"/><rect x="878" y="318" width="24" height="118"/><rect x="906" y="364" width="36" height="72"/>
    <rect x="948" y="336" width="22" height="100"/><rect x="976" y="372" width="30" height="64"/><rect x="688" y="384" width="24" height="52"/><rect x="716" y="362" width="20" height="74"/></g>
  <rect y="430" width="1600" height="570" fill="url(#tn-co)"/>
  <g fill="#4a8737"><circle cx="40" cy="410" r="60"/><circle cx="140" cy="392" r="72"/><circle cx="250" cy="414" r="56"/><circle cx="350" cy="424" r="44"/><circle cx="440" cy="430" r="32"/>
    <circle cx="1380" cy="396" r="70"/><circle cx="1480" cy="380" r="80"/><circle cx="1580" cy="400" r="70"/><circle cx="1290" cy="420" r="46"/><circle cx="1110" cy="430" r="30"/></g>
  <g fill="#68ad52"><circle cx="90" cy="440" r="44"/><circle cx="200" cy="446" r="40"/><circle cx="300" cy="448" r="30"/><circle cx="1430" cy="436" r="46"/><circle cx="1540" cy="442" r="42"/><circle cx="1330" cy="446" r="30"/></g>
  <path d="M790 432h22l688 568H100z" fill="url(#tn-duong)"/>
  <path d="M790 432 120 1000M812 432l668 568" stroke="#f3f5f8" stroke-width="7"/>
  <path d="M801 436v564" stroke="#fff" stroke-width="9" stroke-dasharray="34 40"/>
  <path d="M822 436 1560 960" stroke="#dde3ea" stroke-width="8"/>
  <g stroke="#b5bfcb" stroke-width="6"><path d="M920 504v16M1040 590v20M1180 690v24M1340 804v28"/></g>
  <g transform="translate(67 229.9) scale(1.15)">
    <ellipse cx="520" cy="376" rx="132" ry="13" fill="#1b2531" opacity=".3"/>
    <rect x="418" y="338" width="36" height="36" rx="7" fill="#1f2630"/><rect x="586" y="338" width="36" height="36" rx="7" fill="#1f2630"/>
    <path d="M440 284 462 236q5-9 15-9h86q10 0 15 9l22 48z" fill="#e9edf2" stroke="#c3ccd7" stroke-width="2"/>
    <path d="M454 280 471 242h98l17 38z" fill="url(#tn-kinh)"/>
    <path d="M406 304q0-22 24-24h180q24 2 24 24v46q0 12-12 12H418q-12 0-12-12z" fill="#f7f9fb" stroke="#c3ccd7" stroke-width="2"/>
    <rect x="414" y="298" width="46" height="16" rx="5" fill="#e3262b"/><rect x="580" y="298" width="46" height="16" rx="5" fill="#e3262b"/>
    <rect x="490" y="322" width="60" height="18" rx="3" fill="#fff" stroke="#9aa5b5" stroke-width="2"/>
    <path d="M420 346h200" stroke="#d3dae3" stroke-width="3"/></g>
  <rect x="1136" y="400" width="16" height="320" fill="#96a2b2"/>
  <circle cx="1144" cy="300" r="112" fill="#e3262b"/><circle cx="1144" cy="300" r="85" fill="#fff"/>
  <text x="1144" y="340" text-anchor="middle" font-family="Be Vietnam Pro, Arial, sans-serif" font-weight="700" font-size="112" fill="#111">50</text>
  <g fill="none" stroke="#1d63e8" stroke-width="10" stroke-linecap="round"><path d="M1004 200v-40h42M1242 160h42v40M1284 400v40h-42M1046 440h-42v-40"/></g>
</svg>`;

const GIAY_CHUYEN_ANH = 10;   // thoi gian moi anh nen (giay)
let hChuyenAnh = 0;

async function veTrangChu() {
  clearInterval(hChuyenAnh);
  main.innerHTML = `
  <section class="trang-chu" aria-label="Trang chủ">
    <div class="lop-anh" id="lop-anh">${MINH_HOA}</div>
    <div class="tieu-de-hero">
      <h1>Nhận dạng biển báo<br>giao thông bằng AI</h1>
      <p>Học – Luyện tập – Nhận dạng – Theo dõi kết quả</p>
    </div>
    <div class="cham-anh" id="cham-anh" role="group" aria-label="Chọn ảnh nền"></div>
    <nav class="o-vuong" aria-label="Truy cập nhanh">
      <a href="#/hoc">${ic("book", "ic mau-xanh")}<b>Học biển báo</b><small>Tra cứu ${S.bien.length} biển</small></a>
      <a href="#/bai-tap">${ic("target", "ic mau-tim")}<b>Bài tập</b><small>Trắc nghiệm nhận biết</small></a>
      <a href="#/nhan-dang" class="noi-bat">${ic("camera", "ic mau-xanh")}<b>Nhận dạng</b><small>Ảnh, video, camera</small></a>
      <a href="#/thong-ke">${ic("chart", "ic mau-cam")}<b>Thống kê</b><small>Theo dõi tiến độ</small></a>
    </nav>
  </section>`;
  // anh nen tu thu muc 6_ung_dung/anh_nen; khong co anh thi giu tranh ve
  const ds = await fetch("/api/anh_nen").then(r => (r.ok ? r.json() : [])).catch(() => []);
  const lop = $("#lop-anh");
  if (!ds.length || !lop) return;
  // tai va giai ma truoc tung anh de luc chuyen khong bi giat
  const daTai = ds.map(u => { const im = new Image(); im.src = u; return im.decode().catch(() => {}); });
  lop.insertAdjacentHTML("beforeend", ds.map(u => `<div class="anh-nen" style="background-image:url('${esc(u)}')"></div>`).join(""));
  $(".trang-chu").classList.add("co-anh");
  await daTai[0];
  if ($(".anh-nen")) chayTrinhChieu(ds.length, daTai);
}

function chayTrinhChieu(n, daTai) {
  const anh = $$(".anh-nen");
  let i = -1, hBoCu = 0;
  const den = async k => {
    k = (k + n) % n;
    if (k === i) return;
    await daTai[k];                                  // doi anh tai xong moi chuyen
    if (!anh[k].isConnected) return;                 // da roi trang chu
    clearTimeout(hBoCu);
    anh.forEach(e => e.classList.remove("truoc"));
    const cu = i;
    if (cu >= 0) { anh[cu].classList.remove("hien"); anh[cu].classList.add("truoc"); }  // anh cu nam yen ben duoi
    anh[k].classList.add("hien");                                                       // anh moi hien dan len tren
    i = k;
    hBoCu = setTimeout(() => { if (cu >= 0) anh[cu].classList.remove("truoc"); }, 1700);
    $$("#cham-anh button").forEach((b, j) => b.setAttribute("aria-current", String(j === i)));
  };
  if (n > 1) $("#cham-anh").innerHTML = [...Array(n)].map((_, k) => `<button type="button" aria-label="Ảnh nền ${k + 1}"></button>`).join("");
  const hen = () => {
    clearInterval(hChuyenAnh);
    if (n > 1) hChuyenAnh = setInterval(() => {
      if (!anh[0].isConnected) { clearInterval(hChuyenAnh); return; }   // da roi trang chu
      if (!document.hidden) den(i + 1);                                  // tab an thi tam dung
    }, GIAY_CHUYEN_ANH * 1000);
  };
  $$("#cham-anh button").forEach((b, k) => b.onclick = () => { den(k); hen(); });
  den(0);
  hen();
}

/* =========================== 2. THU VIEN =========================== */
const TV = { loai: "", tu: "", ai: false };
function veThuVien() {
  const coLoai = Object.keys(TEN_LOAI).filter(k => S.bien.some(b => kyHieu(b.ma) === k));
  main.innerHTML = `
  <div class="dau-trang"><h1>${ic("book")}Học biển báo</h1>
    <p class="mo-ta">Tra cứu, tìm hiểu ý nghĩa và đặc điểm của các loại biển báo giao thông.</p></div>
  <label class="tim-kiem">${ic("search")}<input type="search" id="tim" value="${esc(TV.tu)}"
    placeholder="Nhập mã hoặc tên biển báo, ví dụ P.127 hoặc cấm đỗ" aria-label="Tìm biển báo"></label>
  <div class="chip-loc" role="group" aria-label="Lọc theo nhóm biển">
    ${[["", "Tất cả"], ...coLoai.map(k => [k, TEN_LOAI[k]])].map(([k, t]) =>
      `<button type="button" data-loai="${k}" aria-pressed="${TV.loai === k}">${t}</button>`).join("")}
    <button type="button" id="loc-ai" class="chip-ai" aria-pressed="${TV.ai}">${ic("scan")}AI nhận dạng được</button>
  </div>
  <p class="phu nho-chu" id="dem" style="margin:12px 0 0"></p>
  <div class="luoi-bien" id="luoi"></div>`;
  $$("[data-loai]").forEach(b => b.onclick = () => {
    TV.loai = b.dataset.loai;
    $$("[data-loai]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
    veLuoiBien();
  });
  $("#tim").oninput = e => { TV.tu = e.target.value; veLuoiBien(); };
  $("#loc-ai").onclick = e => { TV.ai = !TV.ai; e.currentTarget.setAttribute("aria-pressed", String(TV.ai)); veLuoiBien(); };
  veLuoiBien();
}
function veLuoiBien() {
  const q = chuanTim(TV.tu.trim());
  const ds = S.bien.filter(b => (!TV.loai || kyHieu(b.ma) === TV.loai) && (!TV.ai || b.nhan_dang) && (!q || chuanTim(b.ma + b.ten).includes(q)));
  $("#dem").textContent = `Hiển thị ${ds.length} biển, đã học ${soDaHoc()}/${S.bien.length}`;
  $("#luoi").innerHTML = ds.length ? ds.map(b => `
    <article class="the o-bien ${lopNhom(b.ma)}"><span class="vach"></span>
      ${D.da_hoc[b.ma] ? `<span class="da-hoc" title="Đã học">${ic("check")}Đã học</span>` : ""}
      ${b.nhan_dang ? `<span class="nhan-ai" title="Mô hình AI nhận dạng được biển này">${ic("scan")}AI</span>` : ""}
      ${anhBien(b.ma, "Biển " + b.ma)}
      <span class="ma">${esc(b.ma)}</span><span class="ten">${esc(b.ten)}</span>
      <a class="lien-ket" href="#/hoc/${encodeURIComponent(b.ma)}">Xem chi tiết</a>
    </article>`).join("")
    : `<div class="trong" style="grid-column:1/-1">${ic("search")}<p>Không có biển nào khớp với “${esc(TV.tu)}”. Thử tìm bằng mã biển, ví dụ W.224.</p></div>`;
}

/* =========================== 3. CHI TIET =========================== */
async function veChiTiet(ma) {
  const b = S.theoMa[ma];
  if (!b) {
    main.innerHTML = `<div class="the trong">${ic("search")}<p>Không tìm thấy biển ${esc(ma)} trong thư viện.</p><a class="nut" href="#/hoc">Về thư viện</a></div>`;
    return;
  }
  danhDauDaHoc(ma);
  const lq = bienLienQuan(b);
  main.innerHTML = `
  <div class="dau-trang"><a class="quay-lai" href="#/hoc" aria-label="Quay lại thư viện">${ic("arrow-left")}</a><h1>Chi tiết biển báo</h1></div>
  <div class="chi-tiet">
    <div class="the anh-lon">
      ${anhBien(ma, "Biển " + ma)}
      <div class="ma">${esc(ma)}</div><p class="phu">${esc(b.ten)}</p>
      ${b.nhan_dang ? `<p class="the-ai">${ic("scan")}AI nhận dạng được biển này</p>` : ""}
      <dl class="bang-tt">
        <dt>Nhóm biển:</dt><dd>${esc(TEN_LOAI[kyHieu(ma)])}</dd>
        <dt>Mã hiệu:</dt><dd>${esc(ma)}</dd>
        <dt>Màu sắc:</dt><dd>${esc(mauSac(b))}</dd>
        <dt>Căn cứ:</dt><dd>${esc(b.can_cu)}</dd>
      </dl>
    </div>
    <div class="cot">
      <div class="the">
        <div class="o-tt"><span class="bieu-tuong">${ic("info")}</span><div><h3>Ý nghĩa</h3><p>${esc(b.y_nghia)}</p>
          ${b.y_nghia_tom_tat ? `<p class="phu nho-chu" style="margin:0">Tóm tắt theo tên biển. Giải thích đầy đủ: ${esc(b.can_cu)}.</p>` : ""}</div></div>
        ${khoiChiTiet(b)}
        <div class="o-tt"><span class="bieu-tuong">${ic("eye")}</span><div><h3>Đặc điểm nhận dạng</h3>
          <ul>${dacDiem(b).map(x => `<li>${esc(x)}</li>`).join("")}</ul></div></div>
        <div class="o-tt"><span class="bieu-tuong vang">${ic("bulb")}</span><div><h3>Mẹo ghi nhớ</h3><p>${esc(meo(b))}</p></div></div>
        ${b.can_kiem_tra ? `<p class="ghi-chu" style="margin:14px 0 0">${esc(b.ghi_chu)}</p>` : ""}
      </div>
      <div class="the"><h3>Ví dụ thực tế</h3><div class="luoi-vi-du" id="vi-du"><p class="phu">Đang tải ảnh…</p></div></div>
    </div>
  </div>
  <div class="the"><h2>Biển báo liên quan</h2><div class="lien-quan">
    ${lq.map(x => `<a href="#/hoc/${encodeURIComponent(x.ma)}">${anhBien(x.ma)}<span class="ma">${esc(x.ma)}</span><span class="phu">${esc(x.ten)}</span></a>`).join("")}
  </div></div>
  <div class="hang-nut">
    <a class="nut" href="#/hoc">${ic("arrow-left")}Quay lại thư viện</a>
    <button class="nut chinh" id="luyen" type="button">${ic("target")}Luyện tập với biển này</button>
  </div>`;
  $("#luyen").onclick = () => batDauBaiTap({ nguon: [b, ...bienLienQuan(b, 8)], so: 5, dang: "ket-hop", ten: `Luyện tập ${ma}`, batBuoc: b });
  const anhThat = await fetch(`/api/vi_du/${encodeURIComponent(ma)}`).then(r => r.json()).catch(() => []);
  const tuLichSu = D.nhan_dang.filter(x => x.ma === ma && x.anh).slice(-4).reverse().map(x => x.anh);
  const ds = [...anhThat, ...tuLichSu].slice(0, 4), vung = $("#vi-du");
  if (!vung) return;   // nguoi dung da sang trang khac
  vung.innerHTML = ds.length ? ds.map(u => `<img src="${u}" alt="Ảnh thực tế biển ${esc(ma)}" loading="lazy">`).join("")
    : `<p class="phu">Chưa có ảnh thực tế. Ảnh trong thư mục <b>1_du_lieu\\anh_tu_chup\\${esc(ma)}</b> và ảnh bạn nhận dạng được biển này sẽ hiện ở đây.</p>`;
}

/* =========================== 4-5. NHAN DANG =========================== */
const ND = { tab: "camera", luong: null, video: null, urlVideo: null, vong: 0, raf: 0, kq: null, khoa: "" };
const tam = document.createElement("canvas");

async function guiNhanDang(blob) {
  const r = await fetch("/api/nhan_dang", { method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: blob });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.loi || "Máy chủ không xử lý được ảnh. Kiểm tra cửa sổ đang chạy ứng dụng.");
  return d;
}
function dungNhanDang() {
  ND.vong++;
  cancelAnimationFrame(ND.raf);
  if (ND.luong) { ND.luong.getTracks().forEach(t => t.stop()); ND.luong = null; }
  if (ND.video) { ND.video.pause(); ND.video.srcObject = null; ND.video.removeAttribute("src"); ND.video = null; }
  if (ND.urlVideo) { URL.revokeObjectURL(ND.urlVideo); ND.urlVideo = null; }
}
function datKetQuaXem(url, d, laUrlTam) {
  if (S.ketQuaXem?.laUrlTam) URL.revokeObjectURL(S.ketQuaXem.url);
  S.ketQuaXem = { url, d, laUrlTam, thoi_gian: Date.now() };
}

/* ve anh + khung bao len canvas */
function veHop(c, d, sx, sy) {
  const w0 = c.canvas.width, lw = Math.max(2, w0 / 320), fs = Math.max(13, Math.round(w0 / 42));
  c.font = `600 ${fs}px "Be Vietnam Pro", Arial, sans-serif`;
  c.textBaseline = "top";
  for (const k of d.ket_qua) {
    const [x1, y1, x2, y2] = k.hop, x = x1 * sx, y = y1 * sy, w = (x2 - x1) * sx, h = (y2 - y1) * sy;
    const mau = k.chac_chan ? "#22c55e" : "#f2b100";
    c.lineWidth = lw; c.strokeStyle = mau;
    c.setLineDash(k.chac_chan ? [] : [lw * 3, lw * 2]); c.strokeRect(x, y, w, h); c.setLineDash([]);
    const nhan = `${k.chac_chan ? "" : "? "}${k.ma} (${k.do_tin_cay.toFixed(2)})`;
    const tw = c.measureText(nhan).width + fs * 0.7, th = fs * 1.5, ty = y >= th ? y - th : y + h;
    c.fillStyle = mau; c.fillRect(x - lw / 2, ty, tw, th);
    c.fillStyle = "#0b2414"; c.fillText(nhan, x + fs * 0.35, ty + fs * 0.25);
  }
}
function veLenCanvas(cv, nguon, rong, cao, d) {
  const tl = Math.min(1, 1280 / rong);
  cv.width = Math.round(rong * tl); cv.height = Math.round(cao * tl);
  const c = cv.getContext("2d");
  c.drawImage(nguon, 0, 0, cv.width, cv.height);
  if (d) veHop(c, d, cv.width / d.rong, cv.height / d.cao);
}
/* cat anh nho cua bien de luu lich su */
function catAnhNho(nguon, rongNguon, d, k) {
  const s = rongNguon / d.rong, [x1, y1, x2, y2] = k.hop.map(v => v * s);
  const cv = document.createElement("canvas"); cv.width = cv.height = 96;
  try { cv.getContext("2d").drawImage(nguon, x1, y1, Math.max(1, x2 - x1), Math.max(1, y2 - y1), 0, 0, 96, 96); return cv.toDataURL("image/jpeg", 0.8); }
  catch { return null; }
}
function ghiLichSuND(d, nguon, rongNguon, songTrucTiep) {
  let moi = false;
  for (const k of d.ket_qua) {
    if (!k.chac_chan) continue;
    if (songTrucTiep && D.nhan_dang.some(x => x.ma === k.ma && Date.now() - x.thoi_gian < 15000)) continue;
    D.nhan_dang.push({ thoi_gian: Date.now(), ma: k.ma, p: k.do_tin_cay, anh: catAnhNho(nguon, rongNguon, d, k) });
    if (songTrucTiep) thongBao(`Nhận dạng được: ${k.ma} ${S.theoMa[k.ma]?.ten || ""}`);
    moi = true;
  }
  if (!moi) return;
  D.nhan_dang = D.nhan_dang.slice(-40);
  ghiNgay(); luuKho(); veLichSuND();
}
function veLichSuND() {
  const ul = $("#lich-su"); if (!ul) return;
  const ds = D.nhan_dang.slice(-8).reverse();
  ul.innerHTML = ds.length ? ds.map(x => `<li>${anhBien(x.ma)}
      <span><b>${esc(x.ma)} – ${pct1(x.p)}</b><br><span class="phu nho-chu">${esc(S.theoMa[x.ma]?.ten || "")}</span></span>
      <time>${gio(x.thoi_gian)}</time></li>`).join("")
    : `<li class="phu" style="display:block">Chưa có lần nhận dạng nào.</li>`;
}

function veKetQuaND(d, trangThai, loi) {
  const o = $("#kq-nd"); if (!o) return;
  if (trangThai === "loi") { o.innerHTML = `<h2>Kết quả nhận dạng</h2><p class="loi">${esc(loi)}</p>`; return; }
  if (trangThai === "dang") { o.innerHTML = `<h2>Kết quả nhận dạng</h2><p class="phu">Đang nhận dạng…</p>`; return; }
  if (!d) {
    const goiY = { camera: "Bật camera và đưa biển báo vào giữa khung hình.", anh: "Chọn hoặc kéo thả một ảnh có biển báo.", video: "Chọn một video có biển báo." }[ND.tab];
    o.innerHTML = `<h2>Kết quả nhận dạng</h2><p class="phu">Chưa có kết quả. ${goiY}</p>`; ND.khoa = ""; return;
  }
  const khoa = d.ket_qua.map(k => k.ma + (k.chac_chan ? "+" : "?")).join("|");
  if (trangThai === "song" && khoa === ND.khoa) { const t = $("#thoi-gian-nd"); if (t) t.textContent = `Xử lý trong ${d.thoi_gian_ms} ms`; return; }
  ND.khoa = khoa;
  if (!d.ket_qua.length) {
    o.innerHTML = `<h2>Kết quả nhận dạng</h2><p class="phu nho-chu" id="thoi-gian-nd">Xử lý trong ${d.thoi_gian_ms} ms</p>
      <p class="canh-bao">Không phát hiện biển báo. Hãy để biển chiếm phần lớn khung hình, đủ sáng và không bị che khuất.</p>`;
    return;
  }
  const k = d.ket_qua[0], b = S.theoMa[k.ma] || { ten: k.ten }, thap = k.chac_chan ? "" : "thap";
  o.innerHTML = `<h2>Kết quả nhận dạng</h2><p class="phu nho-chu" id="thoi-gian-nd">Xử lý trong ${d.thoi_gian_ms} ms</p>
    <div class="kq-chinh">${anhBien(k.ma)}<div><span class="ma">${esc(k.ma)}</span><div class="phu nho-chu">${esc(b.ten)}</div></div></div>
    <div class="${thap}"><div class="thanh-tin-cay"><span style="width:${(k.do_tin_cay * 100).toFixed(1)}%"></span></div>
      <span class="nho-chu">Độ tin cậy: <b>${pct1(k.do_tin_cay)}</b></span></div>
    ${k.chac_chan ? "" : `<p class="canh-bao">Độ tin cậy thấp. Hãy kiểm tra lại bằng cách so biển thật với các khả năng dưới đây.</p>
      <ul class="ds-khac">${k.goi_y.map(g => `<li>${anhBien(g.ma)}<a href="#/hoc/${encodeURIComponent(g.ma)}">${esc(g.ma)} ${esc(g.ten)}</a><span>${pct1(g.p)}</span></li>`).join("")}</ul>`}
    <a class="nut nhat day-du" href="#/hoc/${encodeURIComponent(k.ma)}" style="margin-top:12px">Xem chi tiết biển báo ${ic("arrow-right")}</a>
    ${d.ket_qua.length > 1 ? `<h3 style="margin-top:14px">Biển khác trong khung hình</h3><ul class="ds-khac">${d.ket_qua.slice(1, 6).map(x =>
      `<li>${anhBien(x.ma)}<a href="#/hoc/${encodeURIComponent(x.ma)}">${esc(x.ma)} ${esc(S.theoMa[x.ma]?.ten || x.ten)}</a><span>${x.chac_chan ? "" : "? "}${pct1(x.do_tin_cay)}</span></li>`).join("")}</ul>` : ""}`;
}

function veNhanDang() {
  main.innerHTML = `
  <div class="dau-trang"><h1>${ic("scan")}Nhận dạng biển báo</h1>
    <p class="mo-ta">Hệ thống tìm vị trí biển báo trong hình, sau đó mạng nơron xác định loại biển và độ tin cậy.</p></div>
  <div class="tab-ngang" role="tablist" aria-label="Nguồn hình ảnh">
    <button role="tab" data-tab="camera">${ic("camera")}Camera trực tiếp</button>
    <button role="tab" data-tab="anh">${ic("upload")}Tải ảnh lên</button>
    <button role="tab" data-tab="video">${ic("video")}Video</button>
  </div>
  <div class="hai-cot">
    <div class="the"><h2>Camera / ảnh đầu vào</h2><div class="san-khau" id="san-khau"></div><div id="dieu-khien"></div></div>
    <div class="cot"><div class="the" id="kq-nd"></div><div class="the"><h2>Lịch sử nhận dạng</h2><ul class="lich-su" id="lich-su"></ul></div></div>
  </div>`;
  $$(".tab-ngang [role=tab]").forEach(b => b.onclick = () => chonTab(b.dataset.tab));
  chonTab(ND.tab);
  veLichSuND();
}

function chonTab(t) {
  dungNhanDang();
  ND.tab = t; ND.kq = null;
  $$(".tab-ngang [role=tab]").forEach(b => b.setAttribute("aria-selected", String(b.dataset.tab === t)));
  veKetQuaND(null);
  const sk = $("#san-khau"), dk = $("#dieu-khien");
  if (t === "camera") {
    sk.innerHTML = trangThaiTrong("camera", "Camera chưa bật", "Bấm Bật camera rồi đưa biển báo vào giữa khung hình.");
    dk.innerHTML = `<div class="duoi-san-khau"><button class="nut chinh" id="nut-cam" type="button">${ic("camera")}Bật camera</button>
      <button class="nut" id="nut-chup" type="button" disabled>${ic("scan")}Chụp ảnh</button></div>`;
    $("#nut-cam").onclick = () => (ND.luong ? chonTab("camera") : batCamera());
    $("#nut-chup").onclick = chupAnh;
  } else if (t === "anh") {
    sk.innerHTML = `<label class="vung-tha" id="vung-tha">${ic("upload")}<br><b>Kéo thả ảnh vào đây</b><br>hoặc bấm để chọn ảnh JPG, PNG
      <input type="file" accept="image/*" id="chon-tep" hidden></label>`;
    dk.innerHTML = `<div class="duoi-san-khau" id="nut-anh" hidden><label class="nut">${ic("upload")}Chọn ảnh khác
      <input type="file" accept="image/*" id="chon-tep-2" hidden></label>
      <a class="nut chinh" href="#/nhan-dang/ket-qua">Xem kết quả chi tiết ${ic("arrow-right")}</a></div>`;
    const vt = $("#vung-tha");
    $("#chon-tep").onchange = e => xuLyTepAnh(e.target.files[0]);
    $("#chon-tep-2").onchange = e => xuLyTepAnh(e.target.files[0]);
    vt.ondragover = e => { e.preventDefault(); vt.classList.add("dang-keo"); };
    vt.ondragleave = () => vt.classList.remove("dang-keo");
    vt.ondrop = e => { e.preventDefault(); xuLyTepAnh(e.dataTransfer.files[0]); };
  } else {
    sk.innerHTML = trangThaiTrong("video", "Chưa chọn video", "Chọn một video MP4 quay đường phố có biển báo.");
    dk.innerHTML = `<div class="thanh-video"><label class="nut">${ic("video")}Chọn video<input type="file" accept="video/*" id="chon-video" hidden></label>
      <button class="nut" id="nut-phat" type="button" disabled>Phát</button>
      <input type="range" id="tua" min="0" max="1000" value="0" disabled aria-label="Tua video"></div>`;
    $("#chon-video").onchange = e => { const f = e.target.files[0]; e.target.value = ""; if (f) chonVideo(f); };
  }
}

function manHinhSong() {
  $("#san-khau").innerHTML = `<canvas id="man-hinh"></canvas>`;
}
function veLienTuc(v, token) {
  const cv = $("#man-hinh");
  if (!cv || token !== ND.vong) return;
  if (v.videoWidth) {
    const tl = Math.min(1, 1280 / v.videoWidth), w = Math.round(v.videoWidth * tl), h = Math.round(v.videoHeight * tl);
    if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
    const c = cv.getContext("2d");
    c.drawImage(v, 0, 0, w, h);
    if (ND.kq) veHop(c, ND.kq, w / ND.kq.rong, h / ND.kq.cao);
  }
  ND.raf = requestAnimationFrame(() => veLienTuc(v, token));
}
async function vongNhanDang(v, token) {
  while (token === ND.vong) {
    if (v.readyState >= 2 && !v.paused && !v.ended && v.videoWidth) {
      const s = Math.min(1, 960 / v.videoWidth);
      tam.width = Math.round(v.videoWidth * s); tam.height = Math.round(v.videoHeight * s);
      tam.getContext("2d").drawImage(v, 0, 0, tam.width, tam.height);
      const blob = await new Promise(r => tam.toBlob(r, "image/jpeg", 0.85));
      try {
        const d = await guiNhanDang(blob);
        if (token !== ND.vong) break;
        ND.kq = d; veKetQuaND(d, "song"); ghiLichSuND(d, tam, tam.width, true);
      } catch (e) { veKetQuaND(null, "loi", e.message); await ngu(1500); }
    } else {
      await ngu(150);
    }
  }
}

async function batCamera() {
  const sk = $("#san-khau");
  if (!navigator.mediaDevices?.getUserMedia) {
    sk.innerHTML = trangThaiTrong("camera-off", "Trình duyệt không hỗ trợ camera", "Hãy mở ứng dụng bằng Chrome hoặc Edge tại địa chỉ 127.0.0.1.");
    return;
  }
  sk.innerHTML = trangThaiTrong("camera", "Đang mở camera…", "Nếu trình duyệt hỏi quyền, hãy chọn Cho phép.");
  try {
    ND.luong = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment", width: { ideal: 1280 } }, audio: false });
  } catch {
    ND.luong = null;
    sk.innerHTML = trangThaiTrong("camera-off", "Không mở được camera",
      "Hãy cho phép trình duyệt dùng camera (biểu tượng camera trên thanh địa chỉ), đóng ứng dụng khác đang dùng camera rồi bấm lại.");
    return;
  }
  if (ND.tab !== "camera" || !$("#san-khau")) { dungNhanDang(); return; }
  const v = document.createElement("video");
  v.muted = true; v.playsInline = true; v.srcObject = ND.luong; ND.video = v;
  await v.play().catch(() => {});
  manHinhSong();
  const token = ++ND.vong;
  veLienTuc(v, token); vongNhanDang(v, token);
  const nut = $("#nut-cam"); nut.innerHTML = `${ic("x-circle")}Dừng`; nut.classList.remove("chinh"); nut.classList.add("do-dam");
  $("#nut-chup").disabled = false;
}

async function chupAnh() {
  const v = ND.video; if (!v || !v.videoWidth) return;
  const cv = document.createElement("canvas"), tl = Math.min(1, 1600 / v.videoWidth);
  cv.width = Math.round(v.videoWidth * tl); cv.height = Math.round(v.videoHeight * tl);
  cv.getContext("2d").drawImage(v, 0, 0, cv.width, cv.height);
  const blob = await new Promise(r => cv.toBlob(r, "image/jpeg", 0.9));
  try {
    const d = await guiNhanDang(blob);
    datKetQuaXem(cv.toDataURL("image/jpeg", 0.9), d, false);
    ghiLichSuND(d, cv, cv.width, false);
    diToi("#/nhan-dang/ket-qua");
  } catch (e) { thongBao(e.message, true); }
}

function xuLyTepAnh(f) {
  if (!f) return;
  if (!f.type.startsWith("image/")) { veKetQuaND(null, "loi", "Tệp này không phải ảnh. Hãy chọn ảnh JPG hoặc PNG."); return; }
  const url = URL.createObjectURL(f), img = new Image();
  img.onload = async () => {
    if (!$("#san-khau")) return;
    $("#san-khau").innerHTML = `<canvas id="man-hinh"></canvas><span class="dang-xu-ly"><span class="vong-quay"></span>Đang nhận dạng…</span>`;
    const cv = $("#man-hinh");
    veLenCanvas(cv, img, img.naturalWidth, img.naturalHeight, null);
    veKetQuaND(null, "dang");
    try {
      const d = await guiNhanDang(f);
      if (!$("#man-hinh")) return;
      veLenCanvas(cv, img, img.naturalWidth, img.naturalHeight, d);
      ND.kq = d; ND.khoa = "";
      veKetQuaND(d);
      ghiLichSuND(d, img, img.naturalWidth, false);
      datKetQuaXem(url, d, true);
      $("#nut-anh").hidden = false;
    } catch (e) { veKetQuaND(null, "loi", e.message); URL.revokeObjectURL(url); }
    $(".dang-xu-ly")?.remove();
  };
  img.onerror = () => {
    URL.revokeObjectURL(url);
    veKetQuaND(null, "loi", "Không đọc được tệp ảnh này. Ảnh có thể bị hỏng hoặc ở định dạng trình duyệt chưa hỗ trợ (ví dụ HEIC). Hãy chọn ảnh JPG hoặc PNG.");
  };
  img.src = url;
}

function chonVideo(f) {
  dungNhanDang();
  ND.kq = null; veKetQuaND(null);
  const v = document.createElement("video"), sk = $("#san-khau");
  v.muted = true; v.playsInline = true; ND.urlVideo = URL.createObjectURL(f); v.src = ND.urlVideo; ND.video = v;
  const phat = $("#nut-phat"), tua = $("#tua");
  v.onerror = () => {
    sk.innerHTML = trangThaiTrong("video", "Không phát được video", "Trình duyệt không đọc được video này. Hãy dùng video MP4 (H.264) hoặc WebM.");
    phat.disabled = tua.disabled = true;
  };
  v.onloadedmetadata = () => {
    manHinhSong();
    const token = ++ND.vong;
    veLienTuc(v, token); vongNhanDang(v, token);
    phat.disabled = tua.disabled = false;
    v.play().catch(() => {});
  };
  v.onplay = () => { phat.textContent = "Tạm dừng"; };
  v.onpause = () => { phat.textContent = v.ended ? "Phát lại" : "Phát"; };
  v.ontimeupdate = () => { if (v.duration) tua.value = Math.round(v.currentTime / v.duration * 1000); };
  phat.onclick = () => (v.paused ? v.play() : v.pause());
  tua.oninput = () => { if (v.duration) { v.currentTime = tua.value / 1000 * v.duration; ND.kq = null; } };
}

function veKetQuaNhanDang() {
  const x = S.ketQuaXem;
  if (!x) {
    main.innerHTML = `<div class="dau-trang"><a class="quay-lai" href="#/nhan-dang" aria-label="Quay lại">${ic("arrow-left")}</a><h1>Kết quả nhận dạng</h1></div>
      <div class="the trong">${ic("scan")}<p>Chưa có kết quả. Hãy tải ảnh lên hoặc chụp ảnh từ camera trước.</p><a class="nut chinh" href="#/nhan-dang">Đến trang nhận dạng</a></div>`;
    return;
  }
  const k = x.d.ket_qua[0], b = k ? (S.theoMa[k.ma] || { ten: k.ten, y_nghia: "" }) : null;
  main.innerHTML = `
  <div class="dau-trang"><a class="quay-lai" href="#/nhan-dang" aria-label="Quay lại nhận dạng">${ic("arrow-left")}</a><h1>${ic("scan")}Kết quả nhận dạng</h1></div>
  <div class="the">
    <div class="kq-trang">
      <figure style="margin:0"><canvas id="kq-canvas" aria-label="Ảnh đầu vào có đánh dấu vùng biển báo"></canvas>
        <figcaption style="text-align:center;margin-top:8px">Ảnh đầu vào<br><span class="phu nho-chu">${ngayGio(x.thoi_gian)}, xử lý trong ${x.d.thoi_gian_ms} ms</span></figcaption></figure>
      <div>${k ? `
        <div class="kq-bien">${anhBien(k.ma, "Biển chuẩn " + k.ma)}
          <div><div class="ma">${esc(k.ma)}</div><h2>${esc(b.ten)}</h2>
            <span class="huy-hieu ${k.chac_chan ? "" : "thap"}">${ic(k.chac_chan ? "check-circle" : "alert")}Độ tin cậy: ${pct1(k.do_tin_cay)}</span></div></div>
        ${k.chac_chan ? "" : `<p class="canh-bao">Độ tin cậy thấp, kết quả có thể chưa đúng. Hãy so biển trong ảnh với các khả năng sau:</p>
          <ul class="ds-khac">${k.goi_y.map(g => `<li>${anhBien(g.ma)}<a href="#/hoc/${encodeURIComponent(g.ma)}">${esc(g.ma)} ${esc(g.ten)}</a><span>${pct1(g.p)}</span></li>`).join("")}</ul>`}
        <div class="o-tt" style="margin-top:16px"><span class="bieu-tuong">${ic("info")}</span><div><h3>Ý nghĩa</h3><p>${esc(b.y_nghia)}</p></div></div>
        ${S.theoMa[k.ma] ? khoiChiTiet(S.theoMa[k.ma]) : ""}
        ${S.theoMa[k.ma] ? `<div class="o-tt"><span class="bieu-tuong">${ic("eye")}</span><div><h3>Đặc điểm nhận biết</h3>
          <ul>${dacDiem(S.theoMa[k.ma]).map(t => `<li>${esc(t)}</li>`).join("")}</ul></div></div>` : ""}`
        : `<div class="trong">${ic("search")}<p>Không phát hiện biển báo trong ảnh này. Hãy chụp gần hơn, đủ sáng, biển không bị che.</p></div>`}
      </div>
    </div>
    <div class="hang-nut" style="margin-top:18px">
      ${k ? `<a class="nut chinh" href="#/hoc/${encodeURIComponent(k.ma)}">${ic("book")}Xem chi tiết</a>` : ""}
      <a class="nut" href="#/nhan-dang">${ic("refresh")}Nhận dạng lại</a>
      <button class="nut" id="luu-kq" type="button">${ic("save")}Lưu kết quả</button>
    </div>
  </div>
  ${x.d.ket_qua.length > 1 ? `<div class="the"><h2>Các biển khác trong ảnh</h2><ul class="ds-khac">${x.d.ket_qua.slice(1).map(t =>
    `<li>${anhBien(t.ma)}<a href="#/hoc/${encodeURIComponent(t.ma)}">${esc(t.ma)} ${esc(S.theoMa[t.ma]?.ten || t.ten)}</a><span>${pct1(t.do_tin_cay)}</span></li>`).join("")}</ul></div>` : ""}`;
  const cv = $("#kq-canvas"), img = new Image();
  img.onload = () => veLenCanvas(cv, img, img.naturalWidth, img.naturalHeight, x.d);
  img.src = x.url;
  $("#luu-kq").onclick = () => cv.toBlob(blob => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `nhan-dang-${k ? k.ma : "khong-co-bien"}-${ngayStr(new Date())}.png`;
    a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    thongBao("Đã lưu ảnh kết quả vào thư mục Tải xuống.");
  });
}

/* =========================== 6-7. LUYEN TAP BIEN BAO =========================== */
const HINH_THUC = {
  nhom: { so: "01", ten: "Theo nhóm biển", ngan: "Cấm, nguy hiểm, hiệu lệnh, chỉ dẫn", icon: "book", mau: "xanh" },
  hang: { so: "02", ten: "Theo hạng GPLX", ngan: "A1, A, B, C, D, E", icon: "user", mau: "tim" },
  "tong-hop": { so: "03", ten: "Tổng hợp", ngan: "Ngẫu nhiên từ mọi biển", icon: "shuffle", mau: "la" },
  "on-sai": { so: "04", ten: "Ôn câu sai", ngan: "", icon: "refresh", mau: "cam" },
};
// Hang GPLX theo Luat TTATGT duong bo 2024; loc bien theo loai phuong tien xuat hien trong ten bien
const HANG = [
  { ma: "A", ten: "A1, A", ngan: "Mô tô", tu: ["xe máy", "mô tô", "gắn máy"] },
  { ma: "B1", ten: "B1", ngan: "Mô tô 3 bánh", tu: ["xe máy", "mô tô", "gắn máy", "ba bánh"] },
  { ma: "B", ten: "B", ngan: "Ô tô con", tu: ["ô tô", "taxi"] },
  { ma: "C", ten: "C1, C", ngan: "Ô tô tải", tu: ["ô tô", "xe tải", "chở hàng"] },
  { ma: "D", ten: "D1, D2, D", ngan: "Ô tô khách", tu: ["ô tô", "khách", "xe buýt"] },
  { ma: "E", ten: "Hạng E", ngan: "Kéo rơ-moóc", tu: ["ô tô", "rơ-moóc", "sơ-mi"] },
];
const TU_PHUONG_TIEN = ["xe máy", "mô tô", "gắn máy", "ba bánh", "ô tô", "xe tải", "taxi", "khách", "xe buýt", "rơ-moóc", "sơ-mi",
  "máy kéo", "công nông", "xích lô", "xe lam", "vật nuôi", "người kéo", "chở hàng"];
const DANG_CAU = { "nhin-anh": "Nhìn hình", "doc-ten": "Chọn hình", "ket-hop": "Kết hợp" };
const BT = { dangLam: false, cau: [], i: 0, ten: "", xem: "ngay", batDau: 0, ketQua: null, thuGon: false, lanTruoc: null,
  cauHinh: { loai: "p", hang: "B", dang: "ket-hop", so: 10, xem: "ngay" } };
const hopLe = b => !!b.anh && !b.can_kiem_tra && !b.ma_cu;            // bien du dieu kien lam cau hoi
const dungCau = c => c.chon !== null && c.lua_chon[c.chon] === c.dap_an;

function bienSaiNhieu() {
  const dem = {};
  D.bai_tap.forEach(l => (l.cau || []).forEach(c => { if (!c.dung) dem[c.ma] = (dem[c.ma] || 0) + 1; }));
  return Object.entries(dem).filter(([m]) => S.theoMa[m] && S.theoMa[m].anh).sort((a, b) => b[1] - a[1]).map(([m]) => S.theoMa[m]);
}
function nguonCauHoi(ht) {
  const hl = S.bien.filter(hopLe), ch = BT.cauHinh;
  if (ht === "nhom") return hl.filter(b => kyHieu(b.ma) === ch.loai);
  if (ht === "hang") {
    const h = HANG.find(x => x.ma === ch.hang);
    return hl.filter(b => {
      const t = b.ten.toLowerCase(), co = TU_PHUONG_TIEN.filter(w => t.includes(w));
      return !co.length || co.some(w => h.tu.includes(w));   // bien chung cho moi xe, hoac lien quan loai xe cua hang
    });
  }
  if (ht === "on-sai") return bienSaiNhieu();
  return hl;
}
function tenBai(ht) {
  const ch = BT.cauHinh;
  if (ht === "nhom") return `Nhóm ${TEN_LOAI[ch.loai].toLowerCase()}`;
  if (ht === "hang") { const h = HANG.find(x => x.ma === ch.hang); return h.ma === "E" ? "Hạng E" : `Hạng ${h.ten}`; }
  return ht === "tong-hop" ? "Luyện tập tổng hợp" : "Ôn câu đã sai";
}

function taoCauHoi(nguon, n, dang, batBuoc) {
  const kho = S.bien.filter(hopLe);
  let chon = tron(nguon.filter(b => b.anh && b !== batBuoc && (hopLe(b) || nguon.length < 4)));
  if (batBuoc?.anh) chon = [batBuoc, ...chon];
  return chon.slice(0, n).map(b => {
    const ung = [...tron(kho.filter(x => kyHieu(x.ma) === kyHieu(b.ma))), ...tron(kho.filter(x => kyHieu(x.ma) !== kyHieu(b.ma)))];
    const nhieu = [];
    for (const x of ung) {          // phuong an nhieu: uu tien cung nhom, khong trung ten voi dap an va voi nhau
      if (nhieu.length === 3) break;
      if (x !== b && x.ten !== b.ten && !nhieu.some(y => y.ten === x.ten)) nhieu.push(x);
    }
    const kieu = dang === "ket-hop" ? (Math.random() < 0.5 ? "nhin-anh" : "doc-ten") : dang;
    return { kieu, dap_an: b, lua_chon: tron([b, ...nhieu]), chon: null, danh_dau: false };
  });
}
function batDauBaiTap(o) {
  const cau = taoCauHoi(o.nguon, o.so, o.dang || "ket-hop", o.batBuoc);
  if (!cau.length) { thongBao("Không đủ biển hợp lệ để tạo câu hỏi.", true); return; }
  Object.assign(BT, { dangLam: true, cau, i: 0, ten: o.ten, xem: "cuoi", batDau: Date.now(), ketQua: null, thuGon: false, lanTruoc: o });
  diToi("#/bai-tap/lam");
}

function veBaiTap(phan) {
  if (phan === "lam") { if (BT.dangLam) veCauHoi(); else diToi("#/bai-tap"); return; }
  if (phan === "ket-qua") { veKetQuaBaiTap(); return; }
  if (HINH_THUC[phan]) { veThietLap(phan); return; }
  const soSai = bienSaiNhieu().length, daLam = BT.cau.filter(c => c.chon !== null).length;
  main.innerHTML = `
  <div class="dau-trang"><h1>${ic("target")}Luyện tập biển báo</h1></div>
  ${BT.dangLam ? `<div class="the bt-do-dang">${ic("clock")}<span><b>${esc(BT.ten)}</b> đang làm dở (${daLam}/${BT.cau.length})</span>
    <a class="nut chinh" href="#/bai-tap/lam">Làm tiếp</a></div>` : ""}
  <div class="bt-hinh-thuc">${Object.entries(HINH_THUC).map(([k, h]) => `
    <a class="the bt-ht mau-${h.mau}" href="#/bai-tap/${k}"><span class="bt-so">${h.so}</span>
      <span class="bt-bieu-tuong">${ic(h.icon)}</span><b>${h.ten}</b>
      <span class="phu">${k === "on-sai" ? (soSai ? `${soSai} biển cần ôn` : "Chưa có câu sai") : h.ngan}</span></a>`).join("")}
  </div>
  <div class="the"><h2>Bài làm gần đây</h2>${bangLichSuBT(5)}</div>`;
}

function veThietLap(ht) {
  const ch = BT.cauHinh, h = HINH_THUC[ht], hl = S.bien.filter(hopLe);
  const coLoai = Object.keys(TEN_LOAI).filter(k => hl.some(b => kyHieu(b.ma) === k));
  const sai = ht === "on-sai" ? bienSaiNhieu() : [];
  main.innerHTML = `
  <div class="dau-trang"><a class="quay-lai" href="#/bai-tap" aria-label="Quay lại">${ic("arrow-left")}</a><h1>${h.ten}</h1></div>
  <div class="tl-khung">
    <div class="the tl-cai-dat">
      ${ht === "nhom" ? `<div class="tl-muc"><h3>Nhóm biển</h3><div class="chip-loc">
        ${coLoai.map(k => `<button type="button" data-loai="${k}" aria-pressed="${ch.loai === k}">${TEN_LOAI[k]}<span class="dem">${hl.filter(b => kyHieu(b.ma) === k).length}</span></button>`).join("")}</div></div>` : ""}
      ${ht === "hang" ? `<div class="tl-muc"><h3>Hạng GPLX</h3><div class="tl-hang">
        ${HANG.map(x => `<button type="button" data-hang="${x.ma}" aria-pressed="${ch.hang === x.ma}" title="${x.ma === "E" ? "BE, C1E, CE, D1E, D2E, DE" : x.ten}"><b>${x.ten}</b><span>${x.ngan}</span></button>`).join("")}</div></div>` : ""}
      ${ht === "on-sai" ? `<div class="tl-muc"><h3>Biển cần ôn</h3>${sai.length
        ? `<div class="tl-sai">${sai.slice(0, 16).map(b => `<a href="#/hoc/${encodeURIComponent(b.ma)}" title="${esc(b.ma)} ${esc(b.ten)}">${anhBien(b.ma, b.ma)}</a>`).join("")}${sai.length > 16 ? `<span class="phu">+${sai.length - 16}</span>` : ""}</div>`
        : `<p class="phu" style="margin:0">Chưa có câu sai.</p>`}</div>` : ""}
      <div class="tl-muc"><h3>Dạng câu hỏi</h3><div class="tl-dang">
        ${[["nhin-anh", "image"], ["doc-ten", "grid"], ["ket-hop", "shuffle"]].map(([v, i]) =>
          `<button type="button" data-dang="${v}" aria-pressed="${ch.dang === v}">${ic(i)}<span>${DANG_CAU[v]}</span></button>`).join("")}</div></div>
      <div class="tl-muc"><h3>Số câu</h3><div class="chip-loc" id="so-cau"></div></div>
    </div>
    <aside class="the tl-tom-tat mau-${h.mau}">
      <span class="bt-bieu-tuong">${ic(h.icon)}</span>
      <b id="tt-ten"></b><span class="phu" id="tt-chi-tiet"></span>
      <button class="nut chinh" id="bat-dau" type="button">Bắt đầu</button>
      <span class="phu nho-chu">Đáp án hiện sau khi nộp bài</span>
    </aside>
  </div>`;
  const capNhat = () => {
    const n = nguonCauHoi(ht).length, cacSo = [5, 10, 20, 30].filter(x => x <= n);
    if (n && n < 5) cacSo.push(n);
    if (!cacSo.includes(ch.so)) ch.so = cacSo.length ? cacSo[Math.min(1, cacSo.length - 1)] : 0;
    $("#so-cau").innerHTML = cacSo.map(x => `<button type="button" data-so="${x}" aria-pressed="${ch.so === x}">${x}</button>`).join("")
      || `<span class="phu">Không có câu hỏi</span>`;
    $$("[data-so]").forEach(b => b.onclick = () => { ch.so = +b.dataset.so; capNhat(); });
    $("#tt-ten").textContent = tenBai(ht);
    $("#tt-chi-tiet").textContent = n ? `${DANG_CAU[ch.dang]}, ${ch.so} câu` : "Chưa có biển để luyện";
    $("#bat-dau").disabled = !n;
  };
  const chon = (sel, khoa) => $$(sel).forEach(b => b.onclick = () => {
    ch[khoa] = b.dataset[khoa]; $$(sel).forEach(x => x.setAttribute("aria-pressed", String(x === b))); capNhat();
  });
  chon("[data-loai]", "loai"); chon("[data-hang]", "hang"); chon("[data-dang]", "dang");
  $("#bat-dau").onclick = () => {
    const nguon = nguonCauHoi(ht);
    batDauBaiTap({ nguon: ht === "on-sai" ? nguon.slice(0, Math.max(ch.so, 1) * 2) : nguon, so: ch.so, dang: ch.dang, ten: tenBai(ht), hinh_thuc: ht });
  };
  capNhat();
}

function bangLichSuBT(n) {
  const ds = D.bai_tap.slice(-n).reverse();
  if (!ds.length) return `<p class="phu">Chưa có bài làm nào. Kết quả mỗi lần làm bài được lưu trên máy này.</p>`;
  return `<table class="bang"><thead><tr><th>Thời gian</th><th>Bài</th><th>Kết quả</th><th>Thời gian làm</th></tr></thead><tbody>
    ${ds.map(l => `<tr><td>${ngayGio(l.thoi_gian)}</td><td>${esc(l.ten)}</td>
      <td><b>${l.dung}/${l.tong}</b> (${pct1(l.dung / l.tong)})</td><td>${l.giay ? mmss(l.giay) : "–"}</td></tr>`).join("")}</tbody></table>`;
}

/* ---------- man hinh lam bai ---------- */
function khoiPhuongAn(c, khoa) {
  const nhin = c.kieu === "nhin-anh";
  return `<div class="phuong-an ${nhin ? "" : "luoi-anh"}" role="group" aria-label="Các phương án">${c.lua_chon.map((x, j) => {
    const lop = khoa ? (x === c.dap_an ? "dung" : j === c.chon ? "sai" : "") : (j === c.chon ? "da-chon" : "");
    const chu = "ABCD"[j];
    return `<button type="button" data-j="${j}" class="${lop}" ${khoa ? "disabled" : ""} aria-pressed="${j === c.chon}">
      <span class="o-radio">${ic("check")}</span>${nhin ? `<span>${chu}. ${esc(x.ten)}</span>` : `<span class="chu-pa">${chu}.</span><img src="${x.anh}" alt="Phương án ${chu}">`}</button>`;
  }).join("")}</div>`;
}
function giaiThich(c) {
  const d = dungCau(c), b = c.dap_an;
  return `<div class="giai-thich ${d ? "dung" : "sai"}"><b>${d ? "Chính xác." : c.chon === null ? "Bạn bỏ trống câu này." : "Chưa đúng."}</b>
    Đáp án: <span class="nhan-ma">${esc(b.ma)}</span> ${esc(b.ten)}. ${esc(b.y_nghia)}
    <a class="lien-ket" href="#/hoc/${encodeURIComponent(b.ma)}">Xem biển này</a></div>`;
}
function lopO(c, k) {
  const lop = [];
  if (c.chon !== null) lop.push(BT.xem === "ngay" ? (dungCau(c) ? "dung" : "sai") : "da-lam");
  if (k === BT.i) lop.push("hien-tai");
  return lop.join(" ");
}
function veCauHoi() {
  const c = BT.cau[BT.i], n = BT.cau.length, khoa = BT.xem === "ngay" && c.chon !== null, nhin = c.kieu === "nhin-anh";
  const daLam = BT.cau.filter(x => x.chon !== null).length, dd = BT.cau.filter(x => x.danh_dau).length;
  main.innerHTML = `
  <div class="the bt-khung">
    <div class="bt-dau"><div><h1>Luyện nhận biết biển báo</h1><p class="phu nho-chu">Câu ${BT.i + 1}/${n} · ${esc(BT.ten)}</p></div>
      <span class="dong-ho" id="dong-ho">${ic("clock")}<span>00:00</span></span></div>
    <div class="thanh-tien-do" role="progressbar" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${daLam}"><span style="width:${daLam / n * 100}%"></span></div>
    <div class="bt-cau ${nhin ? "" : "doc"}">
      ${nhin ? `<div class="bt-anh"><img src="${c.dap_an.anh}" alt="Biển báo cần nhận biết"></div>` : ""}
      <div class="bt-phai">
        <div class="bt-hoi"><h2>${nhin ? "Biển báo này có ý nghĩa gì?" : `Biển nào có ý nghĩa “${esc(c.dap_an.ten)}”?`}</h2>
          <button type="button" class="nut-danh-dau" id="danh-dau" aria-pressed="${c.danh_dau}">${ic("bookmark")}${c.danh_dau ? "Đã đánh dấu" : "Đánh dấu"}</button></div>
        ${khoiPhuongAn(c, khoa)}
        ${khoa ? giaiThich(c) : ""}
        <div class="bt-dieu-huong">
          <button class="nut" id="truoc" type="button" ${BT.i === 0 ? "disabled" : ""}>${ic("arrow-left")}Câu trước</button>
          ${BT.i < n - 1 ? `<button class="nut ${c.chon === null ? "den" : "chinh"}" id="sau" type="button">${c.chon === null ? "Bỏ qua" : "Câu tiếp theo"}${ic("arrow-right")}</button>` : ""}
        </div>
      </div>
    </div>
    <div class="bt-theo-doi">
      <button type="button" class="bt-theo-doi-dau" id="thu-gon-bang" aria-expanded="${!BT.thuGon}">${ic("grid")}<b>Bảng theo dõi câu hỏi</b>
        <span class="phu">${daLam}/${n} đã làm</span>${ic(BT.thuGon ? "chevron-down" : "chevron-up")}</button>
      ${BT.thuGon ? "" : `<div class="bt-o-so">${BT.cau.map((x, k) => `<button type="button" data-den="${k}" class="${lopO(x, k)}"
          aria-label="Câu ${k + 1}${x.chon !== null ? ", đã trả lời" : ", chưa trả lời"}${x.danh_dau ? ", đã đánh dấu" : ""}">${k + 1}${x.danh_dau ? ic("bookmark", "ic co") : ""}</button>`).join("")}</div>
        <p class="bt-chu-giai phu nho-chu"><span><i class="o-mau da-lam"></i>Đã trả lời: ${daLam}</span><span><i class="o-mau"></i>Chưa trả lời: ${n - daLam}</span>
          <span>${ic("bookmark", "ic co")}Đánh dấu: ${dd}</span></p>`}
    </div>
    <button class="nut nop-bai" id="nop" type="button">Nộp bài luyện tập</button>
  </div>
  <dialog class="hop-nop" id="hop-nop"></dialog>`;
  $$("[data-j]").forEach(b => b.onclick = () => chonDapAn(+b.dataset.j));
  $("#danh-dau").onclick = () => { c.danh_dau = !c.danh_dau; veCauHoi(); };
  $("#truoc").onclick = () => { BT.i--; veCauHoi(); };
  const sau = $("#sau"); if (sau) sau.onclick = () => { BT.i++; veCauHoi(); };
  $("#thu-gon-bang").onclick = () => { BT.thuGon = !BT.thuGon; veCauHoi(); };
  $$("[data-den]").forEach(b => b.onclick = () => { BT.i = +b.dataset.den; veCauHoi(); });
  $("#nop").onclick = hoiNopBai;
  capNhatDongHo();
}
function chonDapAn(j) {
  const c = BT.cau[BT.i];
  if (BT.xem === "ngay" && c.chon !== null) return;          // da khoa sau khi xem giai thich
  c.chon = j;
  if (BT.xem === "ngay") phatAm(dungCau(c));
  veCauHoi();
}
function hoiNopBai() {
  const n = BT.cau.length, daLam = BT.cau.filter(x => x.chon !== null).length, chua = n - daLam, dd = BT.cau.filter(x => x.danh_dau).length;
  if (!chua && !dd) { ketThucBaiTap(); return; }
  const hop = $("#hop-nop");
  const conLai = [chua ? `<b>${chua} câu chưa làm</b>` : "", dd ? `<b>${dd} câu được đánh dấu</b>` : ""].filter(Boolean).join(" và ");
  hop.innerHTML = `<h3>${ic("alert")}Xác nhận nộp bài</h3>
    <p>Bạn đã trả lời <b>${daLam}/${n} câu</b>. Hiện còn ${conLai}.</p><p>Bạn có muốn nộp bài ngay không?</p>
    <div class="hang-nut"><button class="nut" id="quay-lai-kt" type="button">Quay lại kiểm tra</button>
      <button class="nut den" id="xac-nhan-nop" type="button">Nộp bài</button></div>`;
  hop.showModal();
  $("#quay-lai-kt").onclick = () => hop.close();
  $("#xac-nhan-nop").onclick = () => { hop.close(); ketThucBaiTap(); };
}
function ketThucBaiTap() {
  if (!BT.dangLam) return;
  const tong = BT.cau.length, dung = BT.cau.filter(dungCau).length, giay = Math.round((Date.now() - BT.batDau) / 1000);
  const banGhi = { thoi_gian: Date.now(), ten: BT.ten, xem: BT.xem, dung, tong, giay, cau: BT.cau.map(c => ({ ma: c.dap_an.ma, dung: dungCau(c) })) };
  D.bai_tap = [...D.bai_tap, banGhi].slice(-200);
  BT.cau.forEach(c => { if (dungCau(c) && !D.da_hoc[c.dap_an.ma]) D.da_hoc[c.dap_an.ma] = Date.now(); });
  ghiNgay(); luuKho();
  BT.dangLam = false; BT.ketQua = banGhi;
  diToi("#/bai-tap/ket-qua");
}
function capNhatDongHo() {
  const o = $("#dong-ho span");
  if (o && BT.dangLam) o.textContent = mmss(Math.round((Date.now() - BT.batDau) / 1000));
}
setInterval(capNhatDongHo, 1000);
document.addEventListener("keydown", e => {
  if (!BT.dangLam || !$("#dong-ho") || $("#hop-nop")?.open || e.ctrlKey || e.altKey || e.metaKey || /input|select|textarea/i.test(e.target.tagName)) return;
  const j = "abcd".indexOf(e.key.toLowerCase());
  if (j >= 0 && j < BT.cau[BT.i].lua_chon.length) { chonDapAn(j); e.preventDefault(); }
  else if (e.key === "ArrowRight" && BT.i < BT.cau.length - 1) { BT.i++; veCauHoi(); e.preventDefault(); }
  else if (e.key === "ArrowLeft" && BT.i > 0) { BT.i--; veCauHoi(); e.preventDefault(); }
});

const CUP = `<svg viewBox="0 0 200 200" aria-hidden="true">
  <g><rect x="30" y="44" width="8" height="14" rx="2" fill="#f43f5e" transform="rotate(-25 34 51)"/><rect x="160" y="36" width="8" height="14" rx="2" fill="#3b82f6" transform="rotate(20 164 43)"/>
  <rect x="44" y="104" width="7" height="12" rx="2" fill="#22c55e" transform="rotate(30 47 110)"/><rect x="150" y="100" width="7" height="12" rx="2" fill="#a855f7" transform="rotate(-30 153 106)"/>
  <circle cx="54" cy="24" r="4" fill="#f59e0b"/><circle cx="146" cy="74" r="4" fill="#f43f5e"/><circle cx="24" cy="86" r="3.5" fill="#3b82f6"/><circle cx="176" cy="118" r="3.5" fill="#22c55e"/></g>
  <path d="M64 50H44a20 20 0 0 0 24 30M136 50h20a20 20 0 0 1-24 30" fill="none" stroke="#e7a300" stroke-width="8"/>
  <path d="M62 36h76v40a38 38 0 0 1-76 0z" fill="#f5b400"/><path d="M62 36h22v40a38 38 0 0 0 14 29.5A38 38 0 0 1 62 76z" fill="#ffd34d" opacity=".7"/>
  <path d="M91 112h18v24H91z" fill="#e09a00"/><rect x="72" y="134" width="56" height="14" rx="3" fill="#c98500"/><rect x="62" y="146" width="76" height="14" rx="3" fill="#a86f00"/>
  <path d="m100 50 6 12.2 13.4 1.9-9.7 9.5 2.3 13.4-12-6.3-12 6.3 2.3-13.4-9.7-9.5 13.4-1.9z" fill="#fff6c8"/></svg>`;

function trangThaiCau(c) {
  if (c.chon === null) return { lop: "trong sai", nhan: "Bỏ trống", icon: "x-circle" };
  return dungCau(c) ? { lop: "dung", nhan: "Đúng", icon: "check-circle" } : { lop: "sai", nhan: "Sai", icon: "x-circle" };
}
function xemChiTietCau(i) {
  const hop = $("#hop-cau"), c = BT.cau[i], n = BT.cau.length, tt = trangThaiCau(c), nhin = c.kieu === "nhin-anh";
  hop.innerHTML = `
    <div class="hop-cau-dau"><b>Câu ${i + 1}/${n}</b><span class="kq-tt ${tt.lop}">${ic(tt.icon)}${tt.nhan}</span>
      ${c.danh_dau ? `<span class="nhan-ma">đã đánh dấu</span>` : ""}
      <button class="quay-lai" type="button" id="dong-cau" aria-label="Đóng">${ic("x")}</button></div>
    <div class="bt-cau ${nhin ? "" : "doc"}">
      ${nhin ? `<div class="bt-anh"><img src="${c.dap_an.anh}" alt="Biển báo của câu hỏi"></div>` : ""}
      <div class="bt-phai"><div class="bt-hoi"><h2>${nhin ? "Biển báo này có ý nghĩa gì?" : `Biển nào có ý nghĩa “${esc(c.dap_an.ten)}”?`}</h2></div>
        ${khoiPhuongAn(c, true)}${giaiThich(c)}</div>
    </div>
    <div class="bt-dieu-huong">
      <button class="nut" type="button" id="cau-truoc" ${i === 0 ? "disabled" : ""}>${ic("arrow-left")}Câu trước</button>
      <button class="nut chinh" type="button" id="cau-sau" ${i === n - 1 ? "disabled" : ""}>Câu sau${ic("arrow-right")}</button>
    </div>`;
  if (!hop.open) hop.showModal();
  $("#dong-cau").onclick = () => hop.close();
  $("#cau-truoc").onclick = () => xemChiTietCau(i - 1);
  $("#cau-sau").onclick = () => xemChiTietCau(i + 1);
  hop.onclick = e => { if (e.target === hop) hop.close(); };
}
function veKetQuaBaiTap() {
  const r = BT.ketQua;
  if (!r) { diToi("#/bai-tap"); return; }
  const ti = r.dung / r.tong, sai = BT.cau.filter(c => !dungCau(c)).map(c => c.dap_an);
  const loiKhen = ti >= 0.9 ? "Xuất sắc! Hoàn thành bài luyện tập!" : ti >= 0.7 ? "Hoàn thành bài luyện tập!" : "Cần ôn thêm. Xem đáp án để rút kinh nghiệm.";
  main.innerHTML = `
  <div class="dau-trang"><h1>${ic("target")}Kết quả bài tập</h1><p class="mo-ta">${esc(r.ten)}</p></div>
  <div class="the">
    <div class="ket-qua-bt">
      <div class="cup">${CUP}<div class="ruy-bang ${ti >= 0.8 ? "" : "thap"}">${r.dung} / ${r.tong}</div><h2 style="margin-top:16px">${loiKhen}</h2></div>
      <div class="the" style="box-shadow:none"><h3>Kết quả chi tiết</h3>
        <div class="dong-tk"><span>${ic("check-circle", "ic mau-la")}Đúng</span><b>${r.dung} câu</b></div>
        <div class="dong-tk"><span>${ic("x-circle", "ic mau-do")}Sai hoặc bỏ trống</span><b>${r.tong - r.dung} câu</b></div>
        <div class="dong-tk"><span>${ic("percent", "ic mau-xanh")}Độ chính xác</span><b>${pct1(ti)}</b></div>
        <div class="dong-tk"><span>${ic("clock", "ic mau-tim")}Thời gian làm bài</span><b>${mmss(r.giay)}</b></div>
      </div>
    </div>
    <div class="hang-nut" style="justify-content:center;margin-top:18px">
      ${sai.length ? `<button class="nut" id="on-sai" type="button">${ic("refresh")}Ôn lại ${sai.length} câu sai</button>` : ""}
      <button class="nut" id="lam-lai" type="button">${ic("refresh")}Làm lại</button>
      <button class="nut chinh" id="bai-khac" type="button">${ic("target")}Bài tập khác</button>
    </div>
  </div>
  <section class="the">
    <div class="kq-dau"><h2>Đáp án</h2><div class="chip-loc" role="group" aria-label="Lọc câu">
      <button type="button" data-loc="tat-ca" aria-pressed="true">Tất cả (${r.tong})</button>
      <button type="button" data-loc="sai" aria-pressed="false">Câu sai (${r.tong - r.dung})</button>
      <button type="button" data-loc="dung" aria-pressed="false">Câu đúng (${r.dung})</button></div></div>
    <p class="phu nho-chu" style="margin:6px 0 12px">Nhấn vào một câu để xem chi tiết đáp án và giải thích.</p>
    <div class="kq-luoi">${BT.cau.map((c, i) => {
      const tt = trangThaiCau(c), dungIdx = c.lua_chon.indexOf(c.dap_an);
      return `<button type="button" class="kq-o ${tt.lop}" data-xem="${i}" aria-label="Câu ${i + 1}: ${tt.nhan}">
        <span class="kq-so">Câu ${i + 1}${c.danh_dau ? ic("bookmark", "ic co") : ""}</span>${anhBien(c.dap_an.ma)}
        <span class="kq-tt">${ic(tt.icon)}${tt.nhan}</span>
        <span class="phu nho-chu">Chọn ${c.chon === null ? "–" : "ABCD"[c.chon]}, đáp án ${"ABCD"[dungIdx]}</span></button>`;
    }).join("")}</div>
  </section>
  <dialog class="hop-cau" id="hop-cau"></dialog>`;
  $$("[data-loc]").forEach(bt => bt.onclick = () => {
    $$("[data-loc]").forEach(x => x.setAttribute("aria-pressed", String(x === bt)));
    $$(".kq-o").forEach(o => { o.hidden = bt.dataset.loc !== "tat-ca" && !o.classList.contains(bt.dataset.loc); });
  });
  $$("[data-xem]").forEach(o => o.onclick = () => xemChiTietCau(+o.dataset.xem));
  const os = $("#on-sai");
  if (os) os.onclick = () => batDauBaiTap({ nguon: sai, so: sai.length, dang: BT.lanTruoc?.dang, ten: "Ôn lại câu sai" });
  $("#lam-lai").onclick = () => {
    BT.cau.forEach(c => { c.chon = null; c.danh_dau = false; c.lua_chon = tron(c.lua_chon); });
    Object.assign(BT, { dangLam: true, i: 0, batDau: Date.now(), ketQua: null });
    diToi("#/bai-tap/lam");
  };
  $("#bai-khac").onclick = () => { BT.ketQua = null; diToi("#/bai-tap"); };
}

/* =========================== 8. THONG KE =========================== */
function chuoiNgay() {
  const co = new Set(D.ngay), d = new Date();
  if (!co.has(ngayStr(d))) d.setDate(d.getDate() - 1);
  let n = 0;
  while (co.has(ngayStr(d))) { n++; d.setDate(d.getDate() - 1); }
  return n;
}
function bieuDoDuong(diem) {
  const W = 560, H = 220, L = 40, R = 14, T = 14, B = 30, w = W - L - R, h = H - T - B;
  const x = i => L + (w * i) / (diem.length - 1), y = v => T + h * (1 - v);
  const doan = []; let cur = [];
  diem.forEach((p, i) => { if (p.v === null) { if (cur.length) doan.push(cur); cur = []; } else cur.push([x(i), y(p.v)]); });
  if (cur.length) doan.push(cur);
  const duong = doan.map(d => d.map((q, k) => `${k ? "L" : "M"}${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join("")).join("");
  const vung = doan.filter(d => d.length > 1).map(d => `M${d[0][0].toFixed(1)} ${y(0)}` + d.map(q => `L${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join("") + `L${d[d.length - 1][0].toFixed(1)} ${y(0)}Z`).join("");
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Tỷ lệ trả lời đúng 7 ngày gần đây">
    <defs><linearGradient id="vung-tk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--chinh)" stop-opacity=".28"/><stop offset="1" stop-color="var(--chinh)" stop-opacity="0"/></linearGradient></defs>
    ${[0, 0.2, 0.4, 0.6, 0.8, 1].map(v => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--vien)"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${v * 100}%</text>`).join("")}
    ${diem.map((p, i) => `<text x="${x(i)}" y="${H - 8}" text-anchor="middle">${p.nhan}</text>`).join("")}
    <path d="${vung}" fill="url(#vung-tk)"/>
    <path d="${duong}" fill="none" stroke="var(--chinh)" stroke-width="3" stroke-linejoin="round"/>
    ${diem.map((p, i) => p.v === null ? "" : `<circle cx="${x(i)}" cy="${y(p.v)}" r="5" fill="var(--chinh)" stroke="var(--the)" stroke-width="2"><title>${p.nhan}: ${pct1(p.v)}</title></circle>`).join("")}
  </svg>`;
}
function bieuDoTron(dung, sai) {
  const r = 52, C = 2 * Math.PI * r, tong = dung + sai, t = tong ? dung / tong : 0;
  return `<svg viewBox="0 0 140 140" role="img" aria-label="Tỷ lệ đúng ${pct1(t)}">
    <circle cx="70" cy="70" r="${r}" fill="none" stroke="${tong ? "var(--do)" : "var(--vien)"}" stroke-width="18"/>
    <circle cx="70" cy="70" r="${r}" fill="none" stroke="var(--la)" stroke-width="18" stroke-dasharray="${(C * t).toFixed(1)} ${C.toFixed(1)}" transform="rotate(-90 70 70)"/>
    <text x="70" y="70" text-anchor="middle" font-size="22" font-weight="700" fill="var(--chu)">${Math.round(t * 100)}%</text>
    <text x="70" y="90" text-anchor="middle" font-size="12" fill="var(--phu)">Đúng</text></svg>`;
}
function veThongKe() {
  const bt = D.bai_tap, tongCau = bt.reduce((s, l) => s + l.tong, 0), tongDung = bt.reduce((s, l) => s + l.dung, 0);
  const THU = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
  const diem = [...Array(7)].map((_, i) => {
    const d = new Date(); d.setDate(d.getDate() - (6 - i));
    const ls = bt.filter(l => ngayStr(new Date(l.thoi_gian)) === ngayStr(d));
    const t = ls.reduce((s, l) => s + l.tong, 0);
    return { nhan: THU[d.getDay()], v: t ? ls.reduce((s, l) => s + l.dung, 0) / t : null };
  });
  const theoLoai = {};
  bt.forEach(l => (l.cau || []).forEach(c => { const k = kyHieu(c.ma); theoLoai[k] = theoLoai[k] || [0, 0]; theoLoai[k][1]++; if (c.dung) theoLoai[k][0]++; }));
  main.innerHTML = `
  <div class="dau-trang"><h1>${ic("chart")}Thống kê học tập</h1><p class="mo-ta">Số liệu lấy từ hoạt động học của bạn trên máy này.</p></div>
  <div class="so-lieu">
    <div class="the">${ic("book", "ic mau-xanh")}<b>${soDaHoc()}<span class="phu" style="font-size:16px">/${S.bien.length}</span></b><span class="phu">Biển báo đã học</span></div>
    <div class="the">${ic("target", "ic mau-tim")}<b>${bt.length}</b><span class="phu">Bài tập đã làm</span></div>
    <div class="the">${ic("chart", "ic mau-cam")}<b>${tongCau ? pct1(tongDung / tongCau) : "–"}</b><span class="phu">Độ chính xác</span></div>
    <div class="the">${ic("calendar", "ic mau-la")}<b>${chuoiNgay()} ngày</b><span class="phu">Chuỗi học tập</span></div>
  </div>
  ${bt.length ? `
  <div class="hai-bieu-do">
    <div class="the bieu-do"><h2>Tiến độ học tập (7 ngày gần đây)</h2>${bieuDoDuong(diem)}
      ${diem.every(p => p.v === null) ? `<p class="phu nho-chu">Chưa có bài làm nào trong 7 ngày qua.</p>` : ""}</div>
    <div class="the"><h2>Kết quả bài tập</h2><div class="tron">${bieuDoTron(tongDung, tongCau - tongDung)}
      <ul class="chu-thich"><li><i style="background:var(--la)"></i>Đúng: ${tongDung} câu</li><li><i style="background:var(--do)"></i>Sai: ${tongCau - tongDung} câu</li><li>Tổng: ${tongCau} câu</li></ul></div></div>
  </div>
  <div class="the"><h2>Kết quả theo nhóm biển</h2>${Object.keys(theoLoai).length ? `<div class="theo-nhom">${Object.entries(theoLoai).map(([k, [d, t]]) =>
    `<div class="dong" style="--mau:${MAU_LOAI[k]}"><span>${TEN_LOAI[k]}</span><span class="vach-ngang"><span style="width:${d / t * 100}%"></span></span><b>${Math.round(d / t * 100)}%</b></div>`).join("")}</div>`
    : `<p class="phu">Chưa có dữ liệu chi tiết theo nhóm.</p>`}</div>
  <div class="the"><h2>Lịch sử làm bài gần đây</h2>${bangLichSuBT(10)}</div>`
  : `<div class="the trong">${ic("chart")}<p>Chưa có bài tập nào. Biểu đồ tiến độ sẽ xuất hiện sau khi bạn làm bài đầu tiên.</p><a class="nut chinh" href="#/bai-tap">Làm bài tập</a></div>`}`;
}

/* =========================== GIOI THIEU =========================== */
async function veGioiThieu() {
  main.innerHTML = `<div class="dau-trang"><h1>${ic("info")}Giới thiệu</h1></div><div class="the"><p class="phu">Đang tải…</p></div>`;
  const g = await fetch("/api/gioi_thieu").then(r => r.json()).catch(() => null);
  if (!$(".dau-trang") || location.hash !== "#/gioi-thieu") return;
  const pl = g?.ket_qua?.phan_loai, ph = g?.ket_qua?.phat_hien;
  main.innerHTML = `
  <div class="dau-trang"><h1>${ic("info")}Giới thiệu</h1></div>
  <div class="the"><h2>Về ứng dụng</h2>
    <p>Ứng dụng trợ giúp người học nhận biết biển báo giao thông đường bộ Việt Nam: tra cứu biển báo, luyện tập trắc nghiệm và nhận dạng biển báo từ ảnh, video, camera bằng mạng nơron nhân tạo.</p>
    <p class="phu">Tên và ý nghĩa biển theo QCVN 41:2024/BGTVT. Ứng dụng phục vụ học tập, không thay thế văn bản quy chuẩn.</p></div>
  <div class="the"><h2>Cách hệ thống nhận dạng</h2><ol style="margin:0;padding-left:20px;display:grid;gap:6px">
    <li>Nhận ảnh từ camera, tệp ảnh hoặc từng khung hình video.</li>
    <li><b>Phát hiện:</b> mạng YOLO tìm vị trí các biển báo trong ảnh${g ? ` (ảnh đầu vào ${g.co_anh_phat_hien}×${g.co_anh_phat_hien}, ngưỡng ${g.nguong_phat_hien})` : ""} và vẽ khung bao.</li>
    <li><b>Chuẩn hóa:</b> cắt vùng biển, đưa về ảnh màu ${g ? `${g.co_anh_phan_loai}×${g.co_anh_phan_loai}` : "cố định"} điểm ảnh.</li>
    <li><b>Phân loại:</b> mạng nơron tích chập (CNN) tự xây dựng, huấn luyện bằng thuật toán lan truyền ngược, xác định biển thuộc 1 trong ${g ? g.so_bien : S.bien.length} loại.</li>
    <li>Độ tin cậy dưới ${g ? pct1(g.nguong) : "ngưỡng"} được đánh dấu “chưa chắc chắn” kèm 3 khả năng để người học tự đối chiếu.</li></ol></div>
  ${pl || ph ? `<div class="the"><h2>Kết quả kiểm thử mô hình</h2><table class="bang"><tbody>
    ${pl?.accuracy != null ? `<tr><td>Độ chính xác phân loại trên tập kiểm thử độc lập</td><td><b>${pct1(pl.accuracy)}</b> (${pl.so_dung}/${pl.so_mau} mẫu)</td></tr>` : ""}
    ${pl?.macro_f1 != null ? `<tr><td>Macro-F1 phân loại</td><td><b>${pl.macro_f1.toFixed(3).replace(".", ",")}</b></td></tr>` : ""}
    ${pl?.tong_tham_so ? `<tr><td>Số tham số của mạng CNN</td><td>${pl.tong_tham_so.toLocaleString("vi-VN")}</td></tr>` : ""}
    ${ph?.mAP50 != null ? `<tr><td>Bộ phát hiện: mAP50 / recall</td><td><b>${ph.mAP50.toFixed(3).replace(".", ",")}</b> / ${ph.recall.toFixed(3).replace(".", ",")}</td></tr>` : ""}
    </tbody></table><p class="phu nho-chu" style="margin:10px 0 0">Đây là kết quả đo trên dữ liệu kiểm thử của mô hình, khác với kết quả học tập của người học.</p></div>` : ""}
  <div class="the"><h2>Giới hạn</h2><p>Biển không nằm trong ${g ? g.so_bien : S.bien.length} biển đã huấn luyện có thể bị nhận nhầm sang biển gần giống. Hãy luôn đối chiếu với biển chuẩn trong thư viện khi độ tin cậy thấp.</p></div>`;
}

/* =========================== 9. NGUOI HOC =========================== */
function veNguoiHoc(dangSua = false) {
  const n = soDaHoc(), cd = D.cai_dat;
  main.innerHTML = `
  <div class="dau-trang"><h1>${ic("user")}Thông tin người học</h1></div>
  <div class="nguoi-hoc">
    <div class="the ho-so"><span class="avatar">${ic("user")}</span>
      ${dangSua ? `<input id="ten" value="${esc(D.ten)}" maxlength="40" aria-label="Tên người học">`
                : `<h2>${esc(D.ten)}</h2>`}
      <span class="phu">Học viên</span>
      <div style="width:100%;text-align:left;margin-top:6px"><span class="phu nho-chu">Tiến độ học: ${n}/${S.bien.length} biển</span>
        <div class="thanh-tin-cay"><span style="width:${S.bien.length ? n / S.bien.length * 100 : 0}%"></span></div></div>
      ${dangSua ? `<div class="hang-nut"><button class="nut chinh" id="luu-ten" type="button">${ic("check")}Lưu</button><button class="nut" id="huy-sua" type="button">Hủy</button></div>`
                : `<button class="nut vien-xanh" id="sua" type="button">${ic("edit")}Chỉnh sửa</button>`}
    </div>
    <div class="the"><h2 class="tieu-de-ic">${ic("sun")}Cài đặt</h2>
      <div class="dong-cd"><span>${ic("volume")}Âm thanh</span>
        <label class="cong-tac"><input type="checkbox" id="am" ${cd.am_thanh ? "checked" : ""} aria-label="Âm thanh khi trả lời"><span></span></label></div>
      <div class="dong-cd"><span>${ic("info")}Thông báo</span>
        <label class="cong-tac"><input type="checkbox" id="tb" ${cd.thong_bao ? "checked" : ""} aria-label="Hiện thông báo nhỏ"><span></span></label></div>
      <div class="dong-cd"><span>${ic("clock")}Giao diện</span><div class="nhom-nut" role="group" aria-label="Giao diện">
        ${[["sang", "Sáng"], ["toi", "Tối"], ["tu-dong", "Tự động"]].map(([v, t]) => `<button type="button" data-gd="${v}" aria-pressed="${cd.giao_dien === v}">${t}</button>`).join("")}</div></div>
      <button class="dong-cd dong-nut" id="xoa-nd" type="button"><span>${ic("trash")}Xóa lịch sử nhận dạng</span><span class="phu nho-chu">${D.nhan_dang.length} mục</span></button>
      <button class="dong-cd dong-nut mau-do" id="xoa-het" type="button"><span>${ic("trash")}Xóa toàn bộ dữ liệu học tập</span></button>
      <p class="phu nho-chu" style="margin:12px 0 0">Chưa dùng tài khoản: dữ liệu học tập chỉ lưu trong trình duyệt trên máy này, không gửi đi đâu.</p>
    </div>
  </div>`;
  if (dangSua) {
    const o = $("#ten"); o.focus(); o.select();
    const luu = () => { D.ten = o.value.trim() || "Người học"; luuKho(); capNhatTenNho(); veNguoiHoc(); thongBao("Đã lưu tên."); };
    $("#luu-ten").onclick = luu; $("#huy-sua").onclick = () => veNguoiHoc();
    o.onkeydown = e => { if (e.key === "Enter") luu(); if (e.key === "Escape") veNguoiHoc(); };
  } else $("#sua").onclick = () => veNguoiHoc(true);
  $("#am").onchange = e => { cd.am_thanh = e.target.checked; luuKho(); if (e.target.checked) phatAm(true); };
  $("#tb").onchange = e => { cd.thong_bao = e.target.checked; luuKho(); thongBao("Đã bật thông báo."); };
  $$("[data-gd]").forEach(b => b.onclick = () => {
    cd.giao_dien = b.dataset.gd; luuKho(); apGiaoDien();
    $$("[data-gd]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
  });
  $("#xoa-nd").onclick = () => { if (confirm("Xóa toàn bộ lịch sử nhận dạng?")) { D.nhan_dang = []; luuKho(); veNguoiHoc(); thongBao("Đã xóa lịch sử nhận dạng."); } };
  $("#xoa-het").onclick = () => {
    if (!confirm("Xóa toàn bộ dữ liệu học tập (biển đã học, bài tập, lịch sử)? Thao tác này không hoàn tác được.")) return;
    D = { ...macDinh(), cai_dat: cd }; luuKho(); capNhatTenNho(); veNguoiHoc(); thongBao("Đã xóa dữ liệu học tập.");
  };
}

/* =========================== KHOI DONG =========================== */
(async function khoiDong() {
  apGiaoDien(); capNhatTenNho(); apThuGon();
  try {
    const d = await (await fetch("/api/bien")).json();
    S.bien = d.bien; S.nguong = d.nguong;
    S.bien.forEach(b => { S.theoMa[b.ma] = b; });
  } catch {
    main.innerHTML = `<div class="the"><p class="loi">Không kết nối được máy chủ. Hãy chạy lại chay_ung_dung.bat rồi tải lại trang.</p></div>`;
    return;
  }
  window.addEventListener("hashchange", dieuHuong);
  dieuHuong();
})();
