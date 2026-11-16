"use strict";
/* =========================================================================
   Ung dung "Bien Bao Giao Thong" - giao dien 1 trang, dinh tuyen bang #/...
   Luu cuc bo; bai tap moi nop duoc luu SQLite khi da dang nhap Google.
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
  sparkles: '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/>',
  lock: '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3.6 9h16.8M3.6 15h16.8M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
  database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.66 3.58 3 8 3s8-1.34 8-3V5"/><path d="M4 11v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6"/>',
  at: '<circle cx="12" cy="12" r="4"/><path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-3.92 7.94"/>',
};
const ic = (ten, lop = "ic") => `<svg class="${lop}" viewBox="0 0 24 24" aria-hidden="true">${ICON[ten] || ""}</svg>`;

/* ---------------- du lieu bien bao ---------------- */
const S = { bien: [], theoMa: {}, nguong: 0.5, ketQuaXem: null, quizBankVersion: null };
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
function capNhatTenNho() {
    const user = window.TAI_KHOAN_GOOGLE;

    $("#ten-nho").textContent =
        user ? user.ten : D.ten;
}
const trangThaiTrong = (icon, tieuDe, moTa) => `<div class="trang-thai-trong">${ic(icon)}<b>${esc(tieuDe)}</b><span>${esc(moTa)}</span></div>`;

const MENU = [["", "home", "Trang chủ"], ["hoc", "book", "Học biển báo"], ["bai-tap", "target", "Bài tập"],
  ["nhan-dang", "scan", "Nhận dạng"], ["thong-ke", "chart", "Thống kê"]];
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
  window.dongThongKe?.();
  window.dongKhaoSat?.();
  const phan = location.hash.replace(/^#\/?/, "").split("/").map(p => { try { return decodeURIComponent(p); } catch { return p; } });
  const trang = phan[0] || "";
  if (trang !== "nhan-dang") dungNhanDang();
  if (trang !== "") dungTrangChuHieuUng();
  // Chuyen huong route cu ve trang phu hop
  if (trang === "gioi-thieu") {
    if (phan[1] === "danh-gia") {
      diToi("#/nguoi-hoc/danh-gia");
      return;
    }
    // Gioi thieu chung chuyen ve Landing Page
    window.location.href = "/";
    return;
  }
  $$("#menu a, .nguoi-hoc-nho").forEach(a => a.classList.toggle("dang-xem", a.dataset.trang === trang));
  const bang = {
    "": veTrangChu,
    hoc: () => (phan[1] ? veChiTiet(phan[1]) : veThuVien()),
    "bai-tap": () => veBaiTap(phan[1]),
    "nhan-dang": () => (phan[1] === "ket-qua" ? veKetQuaNhanDang() : veNhanDang()),
    "thong-ke": veThongKe,
    "nguoi-hoc": () => veNguoiHoc(false, phan[1] === "danh-gia"),
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

let hChuyenAnh = 0;
let tcRenderToken = 0;
let tcCleanupFns = [];

/* Cau hinh Background Slideshow cho Hero Trang chu */
const HERO_SLIDESHOW_CONFIG = {
  intervalMs: 10000,           // Tu dong chuyen anh sau moi 10 giay
  transitionMs: 1350,          // Thoi gian crossfade giua 2 anh (1.35s, trong khoang 1.2-1.5s)
  sourceEndpoint: "/api/anh_nen", // API tu dong doc thu muc 6_ung_dung/anh_nen/
  defaultPosition: "center 24%",
  positionsByName: {
    "1.jpg": "center 22%",
    "2.jpg": "center 20%",
    "3.jpg": "center 22%",
  },
  // Danh sach anh tuy chinh (neu dien mang duong dan web tuong doi tai day, vi du ["/anh-nen/1.jpg", "/anh-nen/2.jpg"], se uu tien theo dung thu tu nay; de [] de tu dong nap tu thu muc anh_nen/)
  customSlides: [],
  // Danh sach du phong neu /api/anh_nen khong tra ve anh
  fallbackSlides: [],
};

function dungTrangChuHieuUng() {
  tcRenderToken += 1;
  if (hChuyenAnh) {
    clearInterval(hChuyenAnh);
    hChuyenAnh = 0;
  }
  while (tcCleanupFns.length) {
    const fn = tcCleanupFns.pop();
    try { fn(); } catch { /* bo qua */ }
  }
}

function layViTriAnhHero(url) {
  const tenFile = String(url || "").split("?")[0].split("/").pop() || "";
  let giaiMa = tenFile;
  try { giaiMa = decodeURIComponent(tenFile); } catch { /* giu nguyen */ }
  return HERO_SLIDESHOW_CONFIG.positionsByName[giaiMa]
    || HERO_SLIDESHOW_CONFIG.positionsByName[tenFile]
    || HERO_SLIDESHOW_CONFIG.defaultPosition;
}

function taiTruocAnh(url) {
  if (!url) return Promise.reject(new Error("Empty URL"));
  S.anhDaTai ||= new Map();
  if (S.anhDaTai.has(url)) return S.anhDaTai.get(url);
  const promise = new Promise((resolve, reject) => {
    const img = new Image();
    img.decoding = "async";
    img.onload = () => {
      if (typeof img.decode === "function") {
        img.decode().catch(() => { /* bo qua loi decode */ }).then(() => resolve(url));
      } else {
        resolve(url);
      }
    };
    img.onerror = () => {
      S.anhDaTai.delete(url);
      reject(new Error("Image load error"));
    };
    img.src = url;
  });
  S.anhDaTai.set(url, promise);
  return promise;
}

async function layDanhSachAnhHero() {
  if (Array.isArray(HERO_SLIDESHOW_CONFIG.customSlides) && HERO_SLIDESHOW_CONFIG.customSlides.length) {
    return HERO_SLIDESHOW_CONFIG.customSlides;
  }
  if (Array.isArray(S.anhNenHero)) return S.anhNenHero;
  try {
    const res = await fetch(HERO_SLIDESHOW_CONFIG.sourceEndpoint || "/api/anh_nen", { cache: "no-store" });
    if (res.ok) {
      const ds = await res.json();
      if (Array.isArray(ds) && ds.length) {
        S.anhNenHero = ds;
        return ds;
      }
    }
  } catch { /* dung fallback */ }
  return Array.isArray(HERO_SLIDESHOW_CONFIG.fallbackSlides)
    ? HERO_SLIDESHOW_CONFIG.fallbackSlides
    : [];
}

function khoiTaoHeroSlideshow(token) {
  const stage = $("#tc-hero-bg-stage");
  const controls = $("#tc-hero-controls");
  const dotsWrap = $("#tc-slide-dots");
  const btnPrev = $("#tc-slide-prev");
  const btnNext = $("#tc-slide-next");
  if (!stage) return;

  const layers = [$("#tc-hero-slide-a"), $("#tc-hero-slide-b")].filter(Boolean);
  if (layers.length < 2) return;

  const mqReduce = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  const giamChuyenDong = () => !!(mqReduce && mqReduce.matches);

  let slides = [];
  let idx = 0;
  let activeLayer = 0;
  let isTransitioning = false;
  let idlePreloadTimer = 0;
  let fadeTimer = 0;
  let daBaoReducedMotion = false;

  const dongBoThoiGianCss = () => {
    const ms = giamChuyenDong() ? 0 : Math.max(0, Number(HERO_SLIDESHOW_CONFIG.transitionMs) || 1350);
    stage.style.setProperty("--tc-slide-transition", `${ms}ms`);
  };
  dongBoThoiGianCss();

  const capNhatTrangThaiChuyenDong = () => {
    const reduced = giamChuyenDong();
    const hidden = !!document.hidden;
    const state = slides.length <= 1 ? "single" : (reduced ? "reduced-motion" : (hidden ? "paused-hidden" : "auto"));
    if (controls) controls.dataset.motionState = state;
    if (reduced && slides.length > 1 && !daBaoReducedMotion) {
      daBaoReducedMotion = true;
      console.info("[HeroSlideshow] Tự động chuyển ảnh đang tạm tắt do bật 'prefers-reduced-motion: reduce'. Bạn vẫn có thể bấm nút hoặc chấm tròn để đổi ảnh.");
    }
  };

  const clearTimers = () => {
    if (hChuyenAnh) { clearInterval(hChuyenAnh); hChuyenAnh = 0; }
    if (idlePreloadTimer) { clearTimeout(idlePreloadTimer); idlePreloadTimer = 0; }
    if (fadeTimer) { clearTimeout(fadeTimer); fadeTimer = 0; }
  };
  tcCleanupFns.push(clearTimers);

  const capNhatDots = () => {
    if (!dotsWrap) return;
    $$(".tc-slide-dot", dotsWrap).forEach((dot, i) => {
      const chon = i === idx;
      dot.classList.toggle("is-active", chon);
      dot.setAttribute("aria-selected", String(chon));
    });
  };

  const preloadNext = (curIdx) => {
    if (slides.length <= 1) return;
    const nextUrl = slides[(curIdx + 1) % slides.length];
    taiTruocAnh(nextUrl).catch(() => { /* bo qua loi tai truoc */ });
  };

  const renderControls = () => {
    if (!controls || !dotsWrap) return;
    if (slides.length <= 1) {
      controls.hidden = true;
      dotsWrap.innerHTML = "";
      return;
    }
    controls.hidden = false;
    dotsWrap.innerHTML = slides.map((_, i) =>
      `<button type="button" class="tc-slide-dot${i === idx ? " is-active" : ""}" data-slide-idx="${i}" role="tab" aria-selected="${i === idx}" aria-label="Xem ảnh nền ${i + 1}"></button>`
    ).join("");
    $$(".tc-slide-dot", dotsWrap).forEach(dot => {
      dot.addEventListener("click", () => {
        const targetIdx = Number(dot.dataset.slideIdx);
        if (!Number.isNaN(targetIdx)) {
          chuyenToiSlide(targetIdx, true);
        }
      });
    });
  };

  const datAnhDauTien = async () => {
    while (slides.length > 0) {
      const candidate = slides[0];
      try {
        await taiTruocAnh(candidate);
        if (token !== tcRenderToken) return false;
        const layer = layers[0];
        layer.src = candidate;
        layer.style.objectPosition = layViTriAnhHero(candidate);
        layer.classList.remove("is-kenburns", "is-under");
        layer.classList.add("is-front", "is-initial", "is-visible");
        if (!giamChuyenDong()) {
          void layer.offsetWidth;
          layer.classList.add("is-kenburns");
        }
        stage.classList.add("has-photo");
        capNhatDots();
        idlePreloadTimer = setTimeout(() => {
          layer.classList.remove("is-initial");
          if (token === tcRenderToken) preloadNext(0);
        }, 450);
        return true;
      } catch {
        slides = slides.filter(u => u !== candidate);
        S.anhNenHero = slides;
        renderControls();
      }
    }
    stage.classList.remove("has-photo");
    return false;
  };

  const chuyenToiSlide = async (targetIdx, tuNguoiDung = false) => {
    if (token !== tcRenderToken || slides.length <= 1) return;
    const nextIdx = ((targetIdx % slides.length) + slides.length) % slides.length;
    if (nextIdx === idx || isTransitioning) {
      if (tuNguoiDung) khoiDongTuDong();
      return;
    }

    const nextUrl = slides[nextIdx];
    isTransitioning = true;
    try {
      await taiTruocAnh(nextUrl);
    } catch {
      isTransitioning = false;
      slides = slides.filter(u => u !== nextUrl);
      S.anhNenHero = slides;
      if (idx >= slides.length) idx = 0;
      renderControls();
      if (slides.length <= 1) {
        clearTimers();
        return;
      }
      chuyenToiSlide(nextIdx < slides.length ? nextIdx : 0, tuNguoiDung);
      return;
    }

    if (token !== tcRenderToken) {
      isTransitioning = false;
      return;
    }

    const outgoing = layers[activeLayer];
    const incomingIndex = 1 - activeLayer;
    const incoming = layers[incomingIndex];

    // Giu outgoing o lop duoi (opacity 1), dua incoming len tren voi opacity 0 roi crossfade muot
    outgoing.classList.remove("is-front");
    outgoing.classList.add("is-under", "is-visible");

    incoming.classList.remove("is-visible", "is-under", "is-kenburns");
    incoming.classList.add("is-front");
    incoming.src = nextUrl;
    incoming.style.objectPosition = layViTriAnhHero(nextUrl);
    void incoming.offsetWidth;

    if (!giamChuyenDong()) incoming.classList.add("is-kenburns");
    requestAnimationFrame(() => {
      if (token !== tcRenderToken) return;
      incoming.classList.add("is-visible");
    });

    activeLayer = incomingIndex;
    idx = nextIdx;
    capNhatDots();

    const waitMs = giamChuyenDong() ? 50 : (Number(HERO_SLIDESHOW_CONFIG.transitionMs) || 1350) + 80;
    if (fadeTimer) { clearTimeout(fadeTimer); fadeTimer = 0; }
    fadeTimer = setTimeout(() => {
      if (token !== tcRenderToken) return;
      incoming.classList.add("is-visible");
      outgoing.classList.remove("is-visible", "is-under", "is-kenburns");
      isTransitioning = false;
      fadeTimer = 0;
      preloadNext(idx);
    }, waitMs);

    if (tuNguoiDung) khoiDongTuDong();
  };

  const khoiDongTuDong = () => {
    if (hChuyenAnh) { clearInterval(hChuyenAnh); hChuyenAnh = 0; }
    dongBoThoiGianCss();
    capNhatTrangThaiChuyenDong();
    if (token !== tcRenderToken || slides.length <= 1 || giamChuyenDong() || document.hidden) return;
    hChuyenAnh = setInterval(() => {
      if (token !== tcRenderToken) {
        clearInterval(hChuyenAnh);
        hChuyenAnh = 0;
        return;
      }
      chuyenToiSlide(idx + 1, false);
    }, HERO_SLIDESHOW_CONFIG.intervalMs);
  };

  const onVisibilityChange = () => {
    if (token !== tcRenderToken) return;
    if (document.hidden) {
      if (hChuyenAnh) { clearInterval(hChuyenAnh); hChuyenAnh = 0; }
      capNhatTrangThaiChuyenDong();
    } else {
      khoiDongTuDong();
    }
  };
  document.addEventListener("visibilitychange", onVisibilityChange);
  tcCleanupFns.push(() => document.removeEventListener("visibilitychange", onVisibilityChange));

  if (mqReduce && mqReduce.addEventListener) {
    const onMotionChange = () => {
      dongBoThoiGianCss();
      if (giamChuyenDong()) {
        if (hChuyenAnh) { clearInterval(hChuyenAnh); hChuyenAnh = 0; }
        layers.forEach(l => l.classList.remove("is-kenburns"));
        capNhatTrangThaiChuyenDong();
      } else {
        layers[activeLayer]?.classList.add("is-kenburns");
        khoiDongTuDong();
      }
    };
    mqReduce.addEventListener("change", onMotionChange);
    tcCleanupFns.push(() => mqReduce.removeEventListener("change", onMotionChange));
  }

  btnPrev?.addEventListener("click", () => chuyenToiSlide(idx - 1, true));
  btnNext?.addEventListener("click", () => chuyenToiSlide(idx + 1, true));

  layDanhSachAnhHero().then(async ds => {
    if (token !== tcRenderToken || !ds || !ds.length) return;
    slides = [...ds];
    renderControls();
    const ok = await datAnhDauTien();
    if (ok && token === tcRenderToken) khoiDongTuDong();
  });
}

function khoiTaoHieuUngCuon(token) {
  const mucTieu = $$(".tc-reveal");
  if (!mucTieu.length) return;
  const giam = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (giam || typeof IntersectionObserver !== "function") {
    mucTieu.forEach(el => el.classList.add("is-shown"));
    return;
  }
  const io = new IntersectionObserver((entries) => {
    if (token !== tcRenderToken) return;
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-shown");
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.01, rootMargin: "0px 0px -10px 0px" });
  mucTieu.forEach(el => io.observe(el));
  tcCleanupFns.push(() => io.disconnect());
}

/* =========================== 1. TRANG CHU DASHBOARD =========================== */
async function veTrangChu() {
  dungTrangChuHieuUng();
  const token = tcRenderToken;

  // Thong tin nguoi dung (neu da dang nhap)
  const tkGoogle = window.TAI_KHOAN_GOOGLE;
  const tenNguoiDung = tkGoogle ? (tkGoogle.ten || tkGoogle.username || tkGoogle.email || "Học viên") : "";
  const chaoMung = tkGoogle ? `Xin chào, ${esc(tenNguoiDung)}!` : "Chào mừng đến với Biển Báo AI!";

  // 5 nhom bien bao chinh quy QCVN 41:2019/BGTVT
  const NHOM_BIEN_BAO = [
    {
      ma: "p",
      ten: "Biển báo cấm",
      maHien: "Nhóm P",
      anh: "/bien_chuan/P.102.png",
      tenAnh: "P.102 - Cấm đi ngược chiều",
      mau: "var(--nhom-p)",
      bgNhat: "var(--do-nhat)",
      moTa: "Biểu thị các điều cấm mà người tham gia giao thông không được vi phạm."
    },
    {
      ma: "w",
      ten: "Biển nguy hiểm",
      maHien: "Nhóm W",
      anh: "/bien_chuan/W.201a.png",
      tenAnh: "W.201a - Chỗ ngoặt nguy hiểm vòng bên trái",
      mau: "var(--nhom-w)",
      bgNhat: "var(--vang-nhat)",
      moTa: "Cảnh báo trước các tình huống nguy hiểm trên đường để chủ động phòng ngừa."
    },
    {
      ma: "r",
      ten: "Biển hiệu lệnh",
      maHien: "Nhóm R",
      anh: "/bien_chuan/R.301c.png",
      tenAnh: "R.301c - Các xe chỉ được rẽ trái",
      mau: "var(--nhom-r)",
      bgNhat: "var(--chinh-nhat)",
      moTa: "Báo các hiệu lệnh người tham gia giao thông bắt buộc phải chấp hành."
    },
    {
      ma: "i",
      ten: "Biển chỉ dẫn",
      maHien: "Nhóm I",
      anh: "/bien_chuan/I.407a.png",
      tenAnh: "I.407a - Đường một chiều",
      mau: "var(--nhom-i)",
      bgNhat: "var(--chinh-nhat)",
      moTa: "Hướng dẫn hướng đi, vị trí hoặc các điều có ích trên hành trình."
    },
    {
      ma: "s",
      ten: "Biển phụ",
      maHien: "Nhóm S",
      anh: "/bien_chuan/S.501.png",
      tenAnh: "S.501 - Phạm vi tác dụng của biển",
      mau: "var(--nhom-s)",
      bgNhat: "var(--the-phu)",
      moTa: "Thuyết minh bổ sung và làm rõ cho các biển báo chính đi kèm."
    }
  ];

  main.innerHTML = `
  <section class="trang-chu-dashboard" aria-label="Trang chủ ứng dụng">
    <!-- 1. Hero Banner voi Background Slideshow -->
    <div class="tc-hero">
      <div class="tc-hero-bg-stage" id="tc-hero-bg-stage" aria-hidden="true">
        <div class="tc-hero-fallback">${MINH_HOA}</div>
        <img class="tc-hero-slide is-front" id="tc-hero-slide-a" alt="" decoding="async">
        <img class="tc-hero-slide" id="tc-hero-slide-b" alt="" decoding="async">
      </div>
      <div class="tc-hero-overlay" aria-hidden="true"></div>

      <div class="tc-hero-inner">
        <div class="tc-hero-trai">
          <div class="tc-loi-chao tc-anim-up" style="--tc-delay:0ms">
            <span class="tc-chao-badge">${ic("sparkles")} ${chaoMung}</span>
          </div>
          <h1 class="tc-hero-tieu-de tc-anim-up" style="--tc-delay:70ms">Học biển báo thông minh hơn mỗi ngày</h1>
          <p class="tc-hero-mo-ta tc-anim-up" style="--tc-delay:140ms">Khám phá thư viện biển báo giao thông Việt Nam, luyện tập trắc nghiệm trực quan và trải nghiệm công nghệ nhận dạng AI.</p>
          <div class="tc-hero-nut-hang tc-anim-up" style="--tc-delay:210ms">
            <button type="button" class="nut tc-btn-primary tc-nut-lon" id="tc-nut-bat-dau">
              ${ic("book")} Bắt đầu học
            </button>
            <button type="button" class="nut tc-btn-glass tc-nut-lon" id="tc-nut-luyen-tap">
              ${ic("target")} Luyện tập ngay
            </button>
          </div>
        </div>
      </div>

      <div class="tc-hero-controls" id="tc-hero-controls" hidden aria-label="Điều khiển ảnh nền">
        <button type="button" class="tc-slide-btn" id="tc-slide-prev" aria-label="Ảnh nền trước">${ic("chevron-left")}</button>
        <div class="tc-slide-dots" id="tc-slide-dots" role="tablist" aria-label="Chọn ảnh nền"></div>
        <button type="button" class="tc-slide-btn" id="tc-slide-next" aria-label="Ảnh nền tiếp theo">${ic("chevron-right")}</button>
      </div>
    </div>

    <!-- 2. Truy cap nhanh: 4 cards -->
    <div class="tc-phan tc-reveal">
      <div class="tc-dau-phan">
        <h2 class="tc-tieu-de-phan">Bạn muốn làm gì hôm nay?</h2>
        <p class="tc-mo-ta-phan">Lựa chọn chế độ học tập hoặc công cụ hỗ trợ để bắt đầu ngay</p>
      </div>
      <div class="tc-luoi-truy-cap">
        <a href="#/hoc" class="tc-the-truy-cap" style="--tc-stagger:0">
          <div class="tc-truy-cap-icon mau-xanh">${ic("book")}</div>
          <h3 class="tc-truy-cap-ten">Học biển báo</h3>
          <p class="tc-truy-cap-mo-ta">Thư viện ${S.bien.length || 352} biển báo giao thông chuẩn QCVN 41:2019/BGTVT.</p>
          <span class="tc-truy-cap-cta">Khám phá ngay ${ic("arrow-right")}</span>
        </a>
        <a href="#/bai-tap" class="tc-the-truy-cap" style="--tc-stagger:1">
          <div class="tc-truy-cap-icon mau-tim">${ic("target")}</div>
          <h3 class="tc-truy-cap-ten">Bài tập</h3>
          <p class="tc-truy-cap-mo-ta">Luyện tập và kiểm tra kiến thức qua các câu hỏi trắc nghiệm trực quan.</p>
          <span class="tc-truy-cap-cta">Làm bài tập ${ic("arrow-right")}</span>
        </a>
        <a href="#/nhan-dang" class="tc-the-truy-cap" style="--tc-stagger:2">
          <div class="tc-truy-cap-icon mau-luc">${ic("scan")}</div>
          <h3 class="tc-truy-cap-ten">Nhận dạng AI</h3>
          <p class="tc-truy-cap-mo-ta">Nhận diện biển báo từ ảnh, video và camera bằng YOLO11n + CNN.</p>
          <span class="tc-truy-cap-cta">Thử nhận dạng ${ic("arrow-right")}</span>
        </a>
        <a href="#/thong-ke" class="tc-the-truy-cap" style="--tc-stagger:3">
          <div class="tc-truy-cap-icon mau-cam">${ic("chart")}</div>
          <h3 class="tc-truy-cap-ten">Thống kê</h3>
          <p class="tc-truy-cap-mo-ta">Theo dõi tiến bộ, tỷ lệ chính xác và lịch sử luyện tập cá nhân.</p>
          <span class="tc-truy-cap-cta">Xem thống kê ${ic("arrow-right")}</span>
        </a>
      </div>
    </div>

    <!-- 3. Tiep tuc hanh trinh hoc tap -->
    <div class="tc-phan tc-reveal">
      <div class="tc-dau-phan">
        <h2 class="tc-tieu-de-phan">Tiếp tục hành trình học tập</h2>
        <p class="tc-mo-ta-phan">Theo dõi tiến độ và thành tích rèn luyện của bạn</p>
      </div>
      <div class="tc-khu-tiep-tuc-box" id="tc-khu-tiep-tuc">
        <div class="tc-skeleton-wrap">
          <div class="tc-skeleton tc-skel-line"></div>
          <div class="tc-skel-luoi">
            <div class="tc-skeleton tc-skel-o"></div>
            <div class="tc-skeleton tc-skel-o"></div>
            <div class="tc-skeleton tc-skel-o"></div>
            <div class="tc-skeleton tc-skel-o"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 4. Kham pha cac nhom bien bao -->
    <div class="tc-phan tc-reveal">
      <div class="tc-dau-phan">
        <h2 class="tc-tieu-de-phan">Khám phá các nhóm biển báo</h2>
        <p class="tc-mo-ta-phan">Hệ thống 5 nhóm biển báo chính quy theo Quy chuẩn kỹ thuật quốc gia QCVN 41:2019/BGTVT</p>
      </div>
      <div class="tc-luoi-nhom">
        ${NHOM_BIEN_BAO.map(g => {
          const dem = S.bien.filter(b => kyHieu(b.ma) === g.ma).length;
          return `
          <div class="tc-the-nhom" data-loai="${g.ma}" role="button" tabindex="0" title="Xem danh sách ${g.ten}">
            <div class="tc-nhom-dau">
              <span class="tc-nhom-badge" style="color:${g.mau}; background:${g.bgNhat};">${g.maHien} • ${dem} biển</span>
            </div>
            <div class="tc-nhom-anh">
              <img src="${g.anh}" alt="${esc(g.tenAnh)}" loading="lazy">
            </div>
            <h3 class="tc-nhom-ten">${g.ten}</h3>
            <p class="tc-nhom-mo-ta">${g.moTa}</p>
            <span class="tc-nhom-cta">Khám phá ${dem} biển ${ic("arrow-right")}</span>
          </div>`;
        }).join("")}
      </div>
    </div>

    <!-- 5. Gioi thieu AI -->
    <div class="tc-phan tc-reveal">
      <div class="tc-the-ai-banner">
        <div class="tc-ai-banner-trai">
          <div class="tc-ai-tag">${ic("sparkles")} Công nghệ Trí tuệ Nhân tạo</div>
          <h2 class="tc-ai-tieu-de">Biến hình ảnh thành kiến thức cùng AI</h2>
          <p class="tc-ai-mo-ta">Sử dụng YOLO11n để phát hiện vị trí biển báo và mạng nơron tích chập CNN để phân loại các biển báo được hỗ trợ.</p>
          <div class="tc-ai-ghi-chu">
            ${ic("check-circle")} <span>Hỗ trợ nhận dạng <strong>54 lớp biển báo</strong> thông dụng được huấn luyện theo đồ án.</span>
          </div>
          <div class="tc-ai-nut-hang">
            <button type="button" class="nut chinh tc-nut-lon" id="tc-btn-trai-nghiem-ai">
              ${ic("camera")} Trải nghiệm AI ngay
            </button>
          </div>
        </div>
        <div class="tc-ai-banner-phai">
          <div class="tc-ai-quy-trinh">
            <div class="tc-ai-buoc">
              <div class="tc-buoc-so">01</div>
              <div class="tc-buoc-ic">${ic("image")}</div>
              <div class="tc-buoc-ten">Ảnh giao thông</div>
              <div class="tc-buoc-phu">Ảnh tải lên / Webcam</div>
            </div>
            <div class="tc-ai-mui-ten">${ic("arrow-right")}</div>
            <div class="tc-ai-buoc">
              <div class="tc-buoc-so">02</div>
              <div class="tc-buoc-ic">${ic("scan")}</div>
              <div class="tc-buoc-ten">Phát hiện vị trí</div>
              <div class="tc-buoc-phu">Mô hình YOLO11n</div>
            </div>
            <div class="tc-ai-mui-ten">${ic("arrow-right")}</div>
            <div class="tc-ai-buoc">
              <div class="tc-buoc-so">03</div>
              <div class="tc-buoc-ic">${ic("bulb")}</div>
              <div class="tc-buoc-ten">Phân loại biển</div>
              <div class="tc-buoc-phu">Mạng nơron CNN</div>
            </div>
            <div class="tc-ai-mui-ten">${ic("arrow-right")}</div>
            <div class="tc-ai-buoc">
              <div class="tc-buoc-so">04</div>
              <div class="tc-buoc-ic">${ic("check-circle")}</div>
              <div class="tc-buoc-ten">Kết quả chi tiết</div>
              <div class="tc-buoc-phu">Tên, ý nghĩa & mức tin</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer link to Landing Page -->
    <div class="tc-chan-trang">
      <a href="/" class="lien-ket">
        ${ic("home")} Xem trang giới thiệu đồ án (Landing Page)
      </a>
    </div>
  </section>`;

  // Gan su kien cho cac nut Hero
  $("#tc-nut-bat-dau")?.addEventListener("click", () => diToi("#/hoc"));
  $("#tc-nut-luyen-tap")?.addEventListener("click", () => diToi("#/bai-tap"));
  $("#tc-btn-trai-nghiem-ai")?.addEventListener("click", () => diToi("#/nhan-dang"));

  // Gan su kien cho 5 nhom bien bao
  $$(".tc-the-nhom").forEach(card => {
    const loai = card.dataset.loai;
    const moNhom = () => {
      TV.loai = loai;
      TV.tu = "";
      TV.ai = false;
      diToi("#/hoc");
    };
    card.addEventListener("click", moNhom);
    card.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        moNhom();
      }
    });
  });

  // Khoi tao Background Slideshow, Scroll Reveal va Du lieu Tiep tuc hoc
  khoiTaoHeroSlideshow(token);
  khoiTaoHieuUngCuon(token);
  await capNhatKhuTiepTuc(tkGoogle, token);
}

async function capNhatKhuTiepTuc(tkGoogle, token = tcRenderToken) {
  if (token !== tcRenderToken) return;
  const container = $("#tc-khu-tiep-tuc");
  if (!container) return;

  const daHocLocal = typeof soDaHoc === "function" ? soDaHoc() : 0;
  const tenNguoiDung = tkGoogle ? (tkGoogle.ten || tkGoogle.username || tkGoogle.email || "Học viên") : "";

  if (!tkGoogle) {
    // Truong hop CHUA dang nhap
    container.innerHTML = `
      <div class="tc-hop-khach">
        <div class="tc-khach-trai">
          <div class="tc-khach-icon">${ic("user")}</div>
          <div>
            <h3 class="tc-khach-tieu-de">Lưu trữ và đồng bộ kết quả học tập</h3>
            <p class="tc-khach-mo-ta">Đăng nhập tài khoản để tự động lưu lịch sử bài tập vào cơ sở dữ liệu SQLite, theo dõi tỷ lệ chính xác và đồng bộ tiến độ học tập trên mọi thiết bị.</p>
            ${daHocLocal > 0 ? `<div class="tc-khach-luu-y">${ic("info")} <span>Trình duyệt của bạn đang lưu tạm <strong>${daHocLocal} biển</strong> đã tương tác (chưa đồng bộ vào tài khoản).</span></div>` : ""}
          </div>
        </div>
        <div class="tc-khach-phai">
          <a href="/login?next=/app" class="nut chinh tc-nut-lon">${ic("user")} Đăng nhập / Đăng ký</a>
          <button type="button" class="nut tc-nut-lon" id="tc-btn-hoc-khach">${ic("book")} Khám phá biển báo</button>
        </div>
      </div>
    `;
    $("#tc-btn-hoc-khach")?.addEventListener("click", () => diToi("#/hoc"));
    return;
  }

  // Truong hop DA dang nhap Google -> Lay du lieu thuc tu /api/learning/overview
  try {
    const res = await fetch("/api/learning/overview", {
      credentials: "same-origin",
      cache: "no-store"
    });
    if (!res.ok) throw new Error("Không thể tải thống kê");
    const data = await res.json();
    if (token !== tcRenderToken) return;

    if (data.completed_attempts && data.completed_attempts > 0) {
      // Co du lieu lam bai tap
      const tyLeDung = data.overall_accuracy_percent != null
        ? data.overall_accuracy_percent.toFixed(1) + "%"
        : (data.average_score_percent != null ? data.average_score_percent.toFixed(1) + "%" : "0%");
      const tgGanNhat = data.last_attempt_at ? ngayGio(data.last_attempt_at) : "Chưa có";

      container.innerHTML = `
        <div class="tc-hop-thong-ke">
          <div class="tc-luoi-chi-so">
            <div class="tc-o-chi-so">
              <span class="tc-chi-so-nhan">Bài tập đã nộp</span>
              <strong class="tc-chi-so-so mau-chinh">${data.completed_attempts} <small>bài</small></strong>
              <span class="tc-chi-so-phu">Lưu trữ trên SQLite</span>
            </div>
            <div class="tc-o-chi-so">
              <span class="tc-chi-so-nhan">Tỷ lệ chính xác</span>
              <strong class="tc-chi-so-so mau-luc">${tyLeDung}</strong>
              <span class="tc-chi-so-phu">${data.correct_answers || 0}/${data.total_questions || 0} câu đúng</span>
            </div>
            <div class="tc-o-chi-so">
              <span class="tc-chi-so-nhan">Thời gian gần nhất</span>
              <strong class="tc-chi-so-so tc-so-nho">${tgGanNhat}</strong>
              <span class="tc-chi-so-phu">Hoạt động nộp bài cuối</span>
            </div>
            <div class="tc-o-chi-so">
              <span class="tc-chi-so-nhan">Biển đã học</span>
              <strong class="tc-chi-so-so mau-cam">${daHocLocal} <small>biển</small></strong>
              <span class="tc-chi-so-phu">Ghi nhớ trên trình duyệt</span>
            </div>
          </div>
          <div class="tc-thong-ke-nut-hang">
            <button type="button" class="nut chinh" id="tc-btn-tiep-tuc-lt">
              ${ic("target")} Tiếp tục luyện tập
            </button>
            <button type="button" class="nut" id="tc-btn-xem-thong-ke">
              ${ic("chart")} Xem kết quả chi tiết
            </button>
          </div>
        </div>
      `;
      $("#tc-btn-tiep-tuc-lt")?.addEventListener("click", () => diToi("#/bai-tap"));
      $("#tc-btn-xem-thong-ke")?.addEventListener("click", () => diToi("#/thong-ke"));
    } else {
      // Da dang nhap nhung chua lam bai nao (empty state)
      container.innerHTML = `
        <div class="tc-hop-trong">
          <div class="tc-trong-icon">${ic("target")}</div>
          <h3 class="tc-trong-tieu-de">Chưa có dữ liệu bài tập gần đây</h3>
          <p class="tc-trong-mo-ta">Bạn đã đăng nhập nhưng chưa hoàn thành bài luyện tập nào trên hệ thống. Hãy làm bài kiểm tra đầu tiên để củng cố kiến thức và ghi nhận thành tích nhé!</p>
          ${daHocLocal > 0 ? `<div class="tc-trong-ghi-chu">${ic("bookmark")} <span>Bạn đã tương tác với <strong>${daHocLocal} biển</strong> trong thư viện trình duyệt.</span></div>` : ""}
          <div class="tc-trong-nut">
            <button type="button" class="nut chinh tc-nut-lon" id="tc-btn-lam-dau-tien">
              ${ic("target")} Làm bài đầu tiên
            </button>
          </div>
        </div>
      `;
      $("#tc-btn-lam-dau-tien")?.addEventListener("click", () => diToi("#/bai-tap"));
    }
  } catch (err) {
    // Fallback an toan
    container.innerHTML = `
      <div class="tc-hop-trong">
        <p class="tc-trong-mo-ta">Tài khoản: <strong>${esc(tenNguoiDung)}</strong> • Hãy tiếp tục bài luyện tập để nâng cao kiến thức.</p>
        <div class="tc-trong-nut">
          <button type="button" class="nut chinh" id="tc-btn-fallback-bt">${ic("target")} Luyện tập ngay</button>
        </div>
      </div>
    `;
    $("#tc-btn-fallback-bt")?.addEventListener("click", () => diToi("#/bai-tap"));
  }
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
const BT = { dangLam: false, cau: [], i: 0, ten: "", xem: "ngay", batDau: 0, ketQua: null, thuGon: false, lanTruoc: null, lanNop: null,
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
  Object.assign(BT, { dangLam: true, cau, i: 0, ten: o.ten, xem: "cuoi", batDau: Date.now(), ketQua: null, thuGon: false, lanTruoc: o, lanNop: null });
  diToi("#/bai-tap/lam");
}

function kieuMoTa(ht) {
  if (ht === "nhom") return "Luyện tập theo từng nhóm biển báo: Cấm, Nguy hiểm, Hiệu lệnh, Chỉ dẫn, Biển phụ.";
  if (ht === "hang") return "Bộ câu hỏi phân theo hạng GPLX chuẩn Luật Trật tự an toàn giao thông 2024.";
  if (ht === "tong-hop") return "Trộn ngẫu nhiên câu hỏi từ tất cả các nhóm biển báo để đánh giá toàn diện.";
  return "Hệ thống tự động tổng hợp các biển báo bạn từng làm sai để củng cố kiến thức.";
}

function veBaiTap(phan) {
  if (phan === "lam") { if (BT.dangLam) veCauHoi(); else diToi("#/bai-tap"); return; }
  if (phan === "ket-qua") { veKetQuaBaiTap(); return; }
  if (HINH_THUC[phan]) { veThietLap(phan); return; }
  const soSai = bienSaiNhieu().length, daLam = BT.cau.filter(c => c.chon !== null).length;
  const tienDoDangLam = BT.cau.length ? Math.round(daLam / BT.cau.length * 100) : 0;
  main.innerHTML = `
  <div class="dau-trang bt-tong-quan-dau">
    <div class="bt-tq-trai">
      <div class="bt-tq-badge">${ic("target")}<span>Hệ thống luyện tập thông minh</span></div>
      <h1>${ic("target")}Luyện tập biển báo</h1>
      <p class="mo-ta">Rèn luyện phản xạ nhận biết và ghi nhớ hệ thống biển báo đường bộ Việt Nam theo quy chuẩn QCVN 41:2024/BGTVT.</p>
    </div>
    <div class="bt-tq-stats">
      <div class="bt-tq-stat-item"><b>${S.bien.filter(hopLe).length}+</b><span>Biển chuẩn</span></div>
      <div class="bt-tq-stat-item"><b>4</b><span>Chế độ luyện</span></div>
      <div class="bt-tq-stat-item"><b>${D.bai_tap.length}</b><span>Lượt đã làm</span></div>
    </div>
  </div>
  ${BT.dangLam ? `<div class="the bt-do-dang">
    <div class="bt-do-dang-info">
      <span class="bt-pulse-dot"></span>
      ${ic("clock", "ic mau-xanh")}
      <div>
        <div class="bt-do-dang-tieude"><b>${esc(BT.ten)}</b> <span class="bt-do-dang-tag">Đang làm dở</span></div>
        <p class="phu nho-chu">Đã làm <b>${daLam}/${BT.cau.length} câu</b> (${tienDoDangLam}%) · Thời gian ${mmss(Math.round((Date.now() - BT.batDau) / 1000))}</p>
      </div>
    </div>
    <div class="bt-do-dang-tien-do">
      <div class="thanh-tien-do-mini"><span style="width:${tienDoDangLam}%"></span></div>
      <a class="nut chinh" href="#/bai-tap/lam">${ic("play")}Làm tiếp</a>
    </div>
  </div>` : ""}
  <div class="bt-hinh-thuc">${Object.entries(HINH_THUC).map(([k, h]) => `
    <a class="the bt-ht mau-${h.mau}" href="#/bai-tap/${k}">
      <span class="bt-so">${h.so}</span>
      <div class="bt-ht-top">
        <span class="bt-bieu-tuong">${ic(h.icon)}</span>
        <span class="bt-ht-tag">${k === "on-sai" ? (soSai ? `${soSai} biển cần ôn` : "Sẵn sàng") : k === "hang" ? "6 hạng GPLX" : k === "nhom" ? "5 nhóm chính" : "Toàn bộ"}</span>
      </div>
      <b>${h.ten}</b>
      <span class="phu">${k === "on-sai" ? (soSai ? `${soSai} biển báo bạn từng làm sai cần ôn luyện lại` : "Tuyệt vời, bạn chưa có câu sai nào") : h.ngan}</span>
      <div class="bt-ht-footer"><span>Bắt đầu luyện tập</span>${ic("arrow-right")}</div>
    </a>`).join("")}
  </div>
  <div class="the bt-ls-the">
    <div class="bt-ls-dau">
      <div class="bt-ls-tieu-de">${ic("calendar")}<h2>Bài làm gần đây</h2></div>
      <span class="phu nho-chu">Kết quả được lưu tự động trên hệ thống</span>
    </div>
    ${bangLichSuBT(5)}
  </div>`;
}

function veThietLap(ht) {
  const ch = BT.cauHinh, h = HINH_THUC[ht], hl = S.bien.filter(hopLe);
  const coLoai = Object.keys(TEN_LOAI).filter(k => hl.some(b => kyHieu(b.ma) === k));
  const sai = ht === "on-sai" ? bienSaiNhieu() : [];
  main.innerHTML = `
  <header class="bt-tl-dau bt-tl-header">
    <div class="bt-tl-nav-row">
      <a class="quay-lai bt-tl-quay-lai" href="#/bai-tap" aria-label="Quay lại danh sách bài tập">
        ${ic("arrow-left")}
        <span>Quay lại</span>
      </a>
      <div class="bt-tl-tag bt-tl-badge mau-${h.mau}">
        ${ic(h.icon)}
        <span>Chế độ: ${h.so}</span>
      </div>
    </div>
    <div class="bt-tl-title-row">
      <h1 class="bt-tl-title">${h.ten}</h1>
    </div>
    <div class="bt-tl-desc-row">
      <p class="mo-ta bt-tl-desc">${kieuMoTa(ht)}</p>
    </div>
  </header>
  <div class="tl-khung">
    <div class="the tl-cai-dat">
      ${ht === "nhom" ? `<div class="tl-muc"><div class="tl-muc-dau"><h3>1. Chọn nhóm biển báo</h3><span class="phu nho-chu">Chọn nhóm bạn muốn tập trung ôn luyện</span></div><div class="chip-loc tl-chip-loai">
        ${coLoai.map(k => `<button type="button" data-loai="${k}" aria-pressed="${ch.loai === k}"><span class="tl-chip-ten">${TEN_LOAI[k]}</span><span class="dem">${hl.filter(b => kyHieu(b.ma) === k).length} biển</span></button>`).join("")}</div></div>` : ""}
      ${ht === "hang" ? `<div class="tl-muc"><div class="tl-muc-dau"><h3>1. Chọn hạng giấy phép lái xe</h3><span class="phu nho-chu">Phân loại câu hỏi theo quy chuẩn GPLX 2024</span></div><div class="tl-hang">
        ${HANG.map(x => `<button type="button" data-hang="${x.ma}" aria-pressed="${ch.hang === x.ma}" title="${x.ma === "E" ? "BE, C1E, CE, D1E, D2E, DE" : x.ten}">
          <div class="tl-hang-top"><span class="tl-hang-ma">Hạng ${x.ma}</span><span class="tl-hang-check">${ic("check")}</span></div>
          <b>${x.ten}</b>
          <span class="phu nho-chu">${x.ngan}</span>
        </button>`).join("")}</div></div>` : ""}
      ${ht === "on-sai" ? `<div class="tl-muc"><div class="tl-muc-dau"><h3>1. Danh sách biển báo cần ôn lại</h3><span class="phu nho-chu">Các biển bạn từng trả lời sai trong các bài tập trước</span></div>${sai.length
        ? `<div class="tl-sai-khung"><div class="tl-sai">${sai.slice(0, 18).map(b => `<a href="#/hoc/${encodeURIComponent(b.ma)}" title="${esc(b.ma)}: ${esc(b.ten)}">${anhBien(b.ma, b.ma)}<span class="tl-sai-ma">${esc(b.ma)}</span></a>`).join("")}</div>${sai.length > 18 ? `<div class="tl-sai-them">+${sai.length - 18} biển khác trong kho ôn</div>` : ""}</div>`
        : `<div class="tl-sai-trong">${ic("check-circle", "ic mau-la")}<div><b>Chưa có câu hỏi sai!</b><p class="phu nho-chu">Bạn đã hoàn thành tốt các bài luyện tập trước đó. Hãy chọn chế độ khác để thử thách tiếp!</p></div></div>`}</div>` : ""}
      <div class="tl-muc">
        <div class="tl-muc-dau"><h3>${ht === "tong-hop" ? "1" : "2"}. Dạng câu hỏi</h3><span class="phu nho-chu">Tùy chỉnh phương thức kiểm tra để rèn luyện phản xạ</span></div>
        <div class="tl-dang">
          ${[
            ["nhin-anh", "image", "Nhìn hình chọn tên", "Quan sát hình ảnh biển báo và chọn ý nghĩa đúng."],
            ["doc-ten", "grid", "Đọc tên chọn hình", "Đọc tên/ý nghĩa biển báo và chọn hình ảnh phù hợp."],
            ["ket-hop", "shuffle", "Kết hợp linh hoạt", "Xen kẽ ngẫu nhiên cả 2 dạng câu hỏi để tối ưu hiệu quả."]
          ].map(([v, i, ten, mota]) =>
            `<button type="button" data-dang="${v}" aria-pressed="${ch.dang === v}">
              <div class="tl-dang-dau"><span class="tl-dang-ic">${ic(i)}</span><span class="tl-dang-radio"></span></div>
              <b>${ten}</b>
              <span class="phu nho-chu">${mota}</span>
            </button>`).join("")}
        </div>
      </div>
      <div class="tl-muc">
        <div class="tl-muc-dau"><h3>${ht === "tong-hop" ? "2" : "3"}. Số lượng câu hỏi</h3><span class="phu nho-chu">Chọn quy mô bài tập phù hợp với thời gian của bạn</span></div>
        <div class="chip-loc tl-so-cau-grid" id="so-cau"></div>
      </div>
    </div>
    <aside class="the tl-tom-tat mau-${h.mau}">
      <div class="tl-tt-header">
        <span class="bt-bieu-tuong">${ic(h.icon)}</span>
        <div>
          <span class="phu nho-chu">Cấu hình bài tập</span>
          <b id="tt-ten"></b>
        </div>
      </div>
      <div class="tl-tt-danh-sach">
        <div class="tl-tt-dong"><span>Hình thức</span><b id="tt-hinh-thuc">${h.ten}</b></div>
        <div class="tl-tt-dong"><span>Chi tiết</span><b id="tt-chi-tiet"></b></div>
        <div class="tl-tt-dong"><span>Chế độ chấm</span><b>Sau khi nộp bài</b></div>
        <div class="tl-tt-dong"><span>Lưu kết quả</span><b>Tự động lưu</b></div>
      </div>
      <button class="nut chinh tl-nut-bat-dau" id="bat-dau" type="button">${ic("play")} Bắt đầu làm bài</button>
      <p class="phu nho-chu tl-tt-luu-y">${ic("info")}Bạn có thể nộp bài bất kỳ lúc nào hoặc làm đủ số câu.</p>
    </aside>
  </div>`;
  const capNhat = () => {
    const n = nguonCauHoi(ht).length, cacSo = [5, 10, 20, 30].filter(x => x <= n);
    if (n && n < 5) cacSo.push(n);
    if (!cacSo.includes(ch.so)) ch.so = cacSo.length ? cacSo[Math.min(1, cacSo.length - 1)] : 0;
    $("#so-cau").innerHTML = cacSo.map(x => `<button type="button" data-so="${x}" aria-pressed="${ch.so === x}">${x} câu</button>`).join("")
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
  if (!ds.length) return `<div class="trong">${ic("calendar")}<p>Chưa có bài làm nào. Hãy chọn một chế độ luyện tập bên trên để bắt đầu thử sức!</p></div>`;
  return `<div class="bt-bang-cuon"><table class="bang bt-bang-ls"><thead><tr><th>Thời gian</th><th>Bài</th><th>Kết quả</th><th>Thời gian làm</th></tr></thead><tbody>
    ${ds.map(l => {
      const ti = l.tong ? (l.dung / l.tong) : 0;
      const dat = ti >= 0.8;
      return `<tr>
        <td><span class="bt-ls-gio">${ngayGio(l.thoi_gian)}</span></td>
        <td><div class="bt-ls-ten-bai"><b>${esc(l.ten)}</b></div></td>
        <td><div class="bt-ls-diem-badge ${dat ? "tot" : "kem"}"><span>${l.dung}/${l.tong}</span><small>(${pct1(ti)})</small><span class="bt-ls-tag ${dat ? "dat" : "on"}">${dat ? "Đạt" : "Cần ôn"}</span></div></td>
        <td><span class="bt-ls-thoi-luong">${ic("clock")}${l.giay ? mmss(l.giay) : "–"}</span></td>
      </tr>`;
    }).join("")}</tbody></table></div>`;
}

/* ---------- man hinh lam bai ---------- */
function khoiPhuongAn(c, khoa) {
  const nhin = c.kieu === "nhin-anh";
  return `<div class="phuong-an ${nhin ? "" : "luoi-anh"}" role="group" aria-label="Các phương án">${c.lua_chon.map((x, j) => {
    const lop = khoa ? (x === c.dap_an ? "dung" : j === c.chon ? "sai" : "") : (j === c.chon ? "da-chon" : "");
    const chu = "ABCD"[j];
    return `<button type="button" data-j="${j}" class="${lop}" ${khoa ? "disabled" : ""} aria-pressed="${j === c.chon}">
      <span class="o-radio"><span class="chu-pa">${chu}</span></span>${nhin ? `<span class="pa-ten">${esc(x.ten)}</span>` : `<div class="pa-anh-wrap"><img src="${x.anh}" alt="Phương án ${chu}"></div>`}</button>`;
  }).join("")}</div>`;
}
function giaiThich(c) {
  const d = dungCau(c), b = c.dap_an;
  return `<div class="giai-thich ${d ? "dung" : "sai"}">
    <div class="gt-dau">
      <span class="gt-icon">${ic(d ? "check-circle" : "alert")}</span>
      <b>${d ? "Chính xác!" : c.chon === null ? "Bạn đã bỏ qua câu hỏi này." : "Chưa chính xác!"}</b>
    </div>
    <div class="gt-noi-dung">
      <p>Đáp án đúng: <span class="nhan-ma">${esc(b.ma)}</span> <b>${esc(b.ten)}</b></p>
      ${b.y_nghia ? `<p class="gt-y-nghia">${esc(b.y_nghia)}</p>` : ""}
    </div>
    <div class="gt-chan">
      <a class="lien-ket" href="#/hoc/${encodeURIComponent(b.ma)}">${ic("book")} Xem chi tiết biển ${esc(b.ma)}</a>
    </div>
  </div>`;
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
    <div class="bt-dau">
      <div class="bt-dau-trai">
        <span class="bt-cau-badge">Câu ${BT.i + 1} / ${n}</span>
        <div>
          <h1>Luyện nhận biết biển báo</h1>
          <p class="phu nho-chu">${esc(BT.ten)}</p>
        </div>
      </div>
      <div class="bt-dau-phai">
        <span class="dong-ho" id="dong-ho">${ic("clock")}<span>00:00</span></span>
      </div>
    </div>
    <div class="bt-tien-trinh-khung">
      <div class="thanh-tien-do" role="progressbar" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${daLam}"><span style="width:${(daLam / n) * 100}%"></span></div>
      <div class="bt-tien-trinh-chu"><span class="phu nho-chu">Tiến độ làm bài: <b>${daLam}/${n} câu</b></span><span class="phu nho-chu">${dd ? `<span class="bt-tag-dd">${ic("bookmark")} ${dd} đánh dấu</span>` : ""}</span></div>
    </div>
    <div class="bt-cau ${nhin ? "" : "doc"}">
      ${nhin ? `<div class="bt-anh"><div class="bt-anh-wrap"><img src="${c.dap_an.anh}" alt="Biển báo cần nhận biết"></div><span class="bt-anh-hint">Quan sát hình ảnh để chọn đáp án</span></div>` : ""}
      <div class="bt-phai">
        <div class="bt-hoi">
          <h2>${nhin ? "Biển báo này có ý nghĩa gì?" : `Biển nào có ý nghĩa “${esc(c.dap_an.ten)}”?`}</h2>
          <button type="button" class="nut-danh-dau" id="danh-dau" aria-pressed="${c.danh_dau}">${ic("bookmark")}<span>${c.danh_dau ? "Đã đánh dấu" : "Đánh dấu"}</span></button>
        </div>
        ${khoiPhuongAn(c, khoa)}
        ${khoa ? giaiThich(c) : ""}
        <div class="bt-dieu-huong">
          <button class="nut" id="truoc" type="button" ${BT.i === 0 ? "disabled" : ""}>${ic("arrow-left")}Câu trước</button>
          <div class="bt-dh-giua"><span class="phu nho-chu">Câu ${BT.i + 1} / ${n}</span></div>
          ${BT.i < n - 1 ? `<button class="nut ${c.chon === null ? "den" : "chinh"}" id="sau" type="button">${c.chon === null ? "Bỏ qua" : "Câu tiếp theo"}${ic("arrow-right")}</button>` : `<button class="nut chinh" id="nop-nhanh" type="button">${ic("check-circle")}Nộp bài</button>`}
        </div>
      </div>
    </div>
    <div class="bt-theo-doi">
      <button type="button" class="bt-theo-doi-dau" id="thu-gon-bang" aria-expanded="${!BT.thuGon}">
        <span class="bt-td-ic">${ic("grid")}</span>
        <b>Bảng theo dõi câu hỏi</b>
        <span class="bt-td-count">${daLam}/${n} đã làm</span>
        <span class="bt-td-chevron">${ic(BT.thuGon ? "chevron-down" : "chevron-up")}</span>
      </button>
      ${BT.thuGon ? "" : `<div class="bt-o-so">${BT.cau.map((x, k) => `<button type="button" data-den="${k}" class="${lopO(x, k)}"
          aria-label="Câu ${k + 1}${x.chon !== null ? ", đã trả lời" : ", chưa trả lời"}${x.danh_dau ? ", đã đánh dấu" : ""}">${k + 1}${x.danh_dau ? ic("bookmark", "ic co") : ""}</button>`).join("")}</div>
        <div class="bt-chu-giai">
          <span><i class="o-mau da-lam"></i> Đã trả lời (${daLam})</span>
          <span><i class="o-mau"></i> Chưa trả lời (${n - daLam})</span>
          <span>${ic("bookmark", "ic co")} Đã đánh dấu (${dd})</span>
        </div>`}
    </div>
    <div class="bt-nop-vung">
      <button class="nut nop-bai" id="nop" type="button">${ic("check-circle")} Nộp bài luyện tập</button>
    </div>
  </div>
  <dialog class="hop-nop" id="hop-nop"></dialog>`;
  $$("[data-j]").forEach(b => b.onclick = () => chonDapAn(+b.dataset.j));
  $("#danh-dau").onclick = () => { c.danh_dau = !c.danh_dau; veCauHoi(); };
  $("#truoc").onclick = () => { BT.i--; veCauHoi(); };
  const sau = $("#sau"); if (sau) sau.onclick = () => { BT.i++; veCauHoi(); };
  const nopNhanh = $("#nop-nhanh"); if (nopNhanh) nopNhanh.onclick = hoiNopBai;
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
  hop.innerHTML = `
    <div class="hop-nop-dau">
      <div class="hop-nop-icon">${ic("alert")}</div>
      <div>
        <h3>Xác nhận nộp bài luyện tập</h3>
        <p class="phu nho-chu">Kiểm tra trạng thái bài làm trước khi hoàn thành</p>
      </div>
    </div>
    <div class="hop-nop-stats">
      <div class="hop-nop-stat da-lam"><span class="hop-nop-so">${daLam}/${n}</span><span>Đã làm</span></div>
      <div class="hop-nop-stat chua-lam ${chua ? "co-canh-bao" : ""}"><span class="hop-nop-so">${chua}</span><span>Chưa làm</span></div>
      <div class="hop-nop-stat danh-dau ${dd ? "co-danh-dau" : ""}"><span class="hop-nop-so">${dd}</span><span>Đánh dấu</span></div>
    </div>
    <p class="hop-nop-mo-ta">${chua ? `Bạn vẫn còn <b>${chua} câu chưa trả lời</b>.` : "Bạn đã trả lời đầy đủ các câu hỏi."} ${dd ? ` Có <b>${dd} câu</b> bạn đã đánh dấu để kiểm tra lại.` : ""} Bạn có chắc chắn muốn nộp bài ngay?</p>
    <div class="hang-nut hop-nop-nut">
      <button class="nut" id="quay-lai-kt" type="button">${ic("arrow-left")} Tiếp tục làm bài</button>
      <button class="nut chinh" id="xac-nhan-nop" type="button">${ic("check-circle")} Nộp bài</button>
    </div>`;
  hop.showModal();
  $("#quay-lai-kt").onclick = () => hop.close();
  $("#xac-nhan-nop").onclick = () => { hop.close(); ketThucBaiTap(); };
}
// Chỉ lưu lần nộp mới trong tab này để retry/khôi phục kết quả sau F5.
// Không duyệt hoặc đồng bộ lịch sử localStorage cũ.
const KHO_BAI_NOP = "hbb_bai_nop_v1";
function nhoBaiNop(lan) {
  if (BT.lanNop !== lan) return;
  try { sessionStorage.setItem(KHO_BAI_NOP, JSON.stringify({ ...lan, dangGui: false })); }
  catch { /* Hết bộ nhớ: vẫn giữ lần nộp trong RAM để thử lại. */ }
}
function khoiPhucBaiNop() {
  try {
    const lan = JSON.parse(sessionStorage.getItem(KHO_BAI_NOP));
    if (!lan?.payload?.submission_id || !Array.isArray(lan.cau) || !lan.cau.length || !lan.ketQua) return;
    lan.cau = lan.cau.map(c => ({ ...c, dap_an: c.lua_chon.find(x => x.ma === c.dap_an.ma) }));
    if (lan.cau.some(c => !c.dap_an)) return;
    lan.ketQua = D.bai_tap.find(x => x.submission_id === lan.payload.submission_id) || lan.ketQua;
    if (lan.trangThai === "dang-luu") {
      lan.trangThai = "loi"; lan.loi = "Chưa xác nhận được kết quả lưu. Bạn có thể thử lưu lại.";
    }
    Object.assign(BT, { dangLam: false, lanNop: lan, cau: lan.cau, ten: lan.ketQua.ten,
      xem: "cuoi", ketQua: lan.ketQua, lanTruoc: { hinh_thuc: lan.payload.quiz_type, dang: lan.dang } });
  } catch { /* Bản lưu hỏng không ảnh hưởng bài tập. */ }
}
function veTrangThaiLuuBai() {
  const o = $("#trang-thai-luu"), lan = BT.lanNop;
  if (!o || !lan) return;
  if (lan.trangThai === "da-luu") o.textContent = "Đã lưu kết quả học tập theo tài khoản Google.";
  else if (lan.trangThai === "khach") o.textContent = "Kết quả đã lưu trên trình duyệt. Đăng nhập Google để lưu các bài làm tiếp theo theo tài khoản.";
  else if (lan.dangGui) o.textContent = "Đang lưu kết quả học tập…";
  else {
    o.innerHTML = `<p>${esc(lan.loi || "Chưa lưu được kết quả theo tài khoản.")} Kết quả cục bộ vẫn được giữ.</p>
      <button class="nut" type="button" id="thu-luu-lai">Thử lưu lại</button>`;
    $("#thu-luu-lai").onclick = () => luuBaiNopGoogle(lan);
  }
}
async function luuBaiNopGoogle(lan) {
  if (lan.dangGui || lan.trangThai === "da-luu") return;
  lan.dangGui = true; lan.trangThai = "dang-luu";
  nhoBaiNop(lan); veTrangThaiLuuBai();
  try {
    const phien = await window.layPhienGoogle();
    if (!phien.da_dang_nhap) {
      if (lan.userId) throw new Error("Phiên đăng nhập đã kết thúc. Hãy đăng nhập lại đúng tài khoản rồi thử lưu lại.");
      lan.trangThai = "khach";
      return;
    }
    if (lan.userId && lan.userId !== phien.user.id) throw new Error("Tài khoản đã thay đổi. Hãy đăng nhập lại tài khoản đã nộp bài để thử lưu lại.");
    lan.userId = phien.user.id;
    nhoBaiNop(lan);
    if (typeof lan.payload.bank_version !== "string" || !/^[0-9a-f]{64}$/.test(lan.payload.bank_version)) {
      throw new Error("Máy chủ chưa cung cấp phiên bản dữ liệu bài tập. Hãy khởi động lại Flask và tải lại trang để làm bài mới; bài hiện tại vẫn được giữ cục bộ.");
    }
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 15000);
    let response, data;
    try {
      response = await fetch("/api/quiz/submit", { method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": phien.csrf_token || "" },
        body: JSON.stringify(lan.payload), signal: controller.signal });
      // Flask cũ trả trang HTML 404/405: vẫn phải báo đúng lỗi HTTP,
      // không để lỗi đọc JSON che mất nguyên nhân API chưa được nạp.
      data = await response.json().catch(() => null);
    } finally { clearTimeout(timeout); }
    if (!response.ok) {
      if ([404, 405].includes(response.status)) {
        throw new Error(`API lưu bài tập chưa được nạp (HTTP ${response.status}). Hãy khởi động lại Flask và tải lại trang.`);
      }
      throw new Error(data?.loi || `Máy chủ trả HTTP ${response.status}, chưa xác nhận lưu được kết quả. Hãy thử lưu lại.`);
    }
    if (!data?.da_luu || data.answers?.length !== lan.cau.length || !data.attempt) throw new Error("Phản hồi lưu kết quả không đầy đủ. Hãy thử lại.");
    // Hiển thị kết quả/đáp án đã được server kiểm chứng, giữ nguyên thứ tự đề.
    lan.cau = data.answers.map(a => ({ kieu: a.question_snapshot.kieu, lua_chon: a.options_snapshot,
      dap_an: a.options_snapshot[a.correct_answer], chon: a.selected_answer, danh_dau: a.marked_for_review }));
    Object.assign(lan.ketQua, { dung: data.attempt.correct_count, tong: data.attempt.question_count,
      giay: data.attempt.duration_seconds, attempt_id: data.attempt.id,
      cau: data.answers.map(a => ({ ma: a.sign_code, dung: a.status === "correct" })) });
    lan.trangThai = "da-luu"; lan.loi = null; lan.vuaMoiLuu = true;
    if (BT.lanNop === lan) { BT.cau = lan.cau; BT.ketQua = lan.ketQua; }
    luuKho();
    thongBao("Đã lưu kết quả học tập", true);
  } catch (error) {
    lan.trangThai = "loi";
    lan.loi = error.name === "AbortError" ? "Kết nối quá thời gian chờ. Bạn có thể thử lưu lại an toàn."
      : error.message || "Không thể kết nối máy chủ. Hãy thử lưu lại.";
    thongBao(lan.loi, true);
  } finally {
    lan.dangGui = false;
    nhoBaiNop(lan);
    if (BT.lanNop === lan) {
      if (location.hash === "#/bai-tap/ket-qua") veKetQuaBaiTap();
      else veTrangThaiLuuBai();
    }
  }
}
async function ketThucBaiTap() {
  if (!BT.dangLam) return;
  BT.dangLam = false; // Khóa lần nộp ngay, kể cả khi mạng chậm hoặc nhấn hai lần.
  const ketThuc = Date.now(), tong = BT.cau.length, dung = BT.cau.filter(dungCau).length, giay = Math.round((ketThuc - BT.batDau) / 1000);
  const submissionId = crypto.randomUUID();
  const banGhi = { thoi_gian: ketThuc, ten: BT.ten, xem: BT.xem, dung, tong, giay, submission_id: submissionId, cau: BT.cau.map(c => ({ ma: c.dap_an.ma, dung: dungCau(c) })) };
  D.bai_tap = [...D.bai_tap, banGhi].slice(-200);
  BT.cau.forEach(c => { if (dungCau(c) && !D.da_hoc[c.dap_an.ma]) D.da_hoc[c.dap_an.ma] = Date.now(); });
  ghiNgay(); luuKho();
  BT.ketQua = banGhi;
  const lan = { payload: { submission_id: submissionId,
    quiz_type: BT.lanTruoc?.hinh_thuc || (BT.lanTruoc?.batBuoc ? "bien-don" : "on-sai"),
    quiz_title: BT.ten, bank_version: S.quizBankVersion, started_at: BT.batDau, submitted_at: ketThuc,
    questions: BT.cau.map(c => ({ question_id: `${c.kieu}:${c.dap_an.ma}`, option_codes: c.lua_chon.map(x => x.ma),
      selected_answer: c.chon, marked_for_review: c.danh_dau })) },
    cau: BT.cau.map(c => ({ ...c, lua_chon: [...c.lua_chon] })), dang: BT.lanTruoc?.dang,
    ketQua: banGhi, userId: window.TAI_KHOAN_GOOGLE?.id || null, trangThai: "dang-luu", dangGui: false };
  BT.lanNop = lan;
  $$(".bt-khung button").forEach(b => { b.disabled = true; });
  const nop = $("#nop"); if (nop) nop.textContent = "Đang kiểm tra và lưu kết quả…";
  await luuBaiNopGoogle(lan);
  if (BT.lanNop === lan && ["#/bai-tap/lam", "#/bai-tap/ket-qua"].includes(location.hash)) diToi("#/bai-tap/ket-qua");
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
    <div class="hop-cau-dau">
      <div class="hop-cau-dau-trai">
        <span class="hop-cau-so">Câu ${i + 1} / ${n}</span>
        <span class="kq-tt ${tt.lop}">${ic(tt.icon)}${tt.nhan}</span>
        ${c.danh_dau ? `<span class="nhan-ma nhan-dd">${ic("bookmark")} Đã đánh dấu</span>` : ""}
      </div>
      <button class="quay-lai" type="button" id="dong-cau" aria-label="Đóng">${ic("x")}</button>
    </div>
    <div class="bt-cau ${nhin ? "" : "doc"}">
      ${nhin ? `<div class="bt-anh"><div class="bt-anh-wrap"><img src="${c.dap_an.anh}" alt="Biển báo của câu hỏi"></div></div>` : ""}
      <div class="bt-phai">
        <div class="bt-hoi"><h2>${nhin ? "Biển báo này có ý nghĩa gì?" : `Biển nào có ý nghĩa “${esc(c.dap_an.ten)}”?`}</h2></div>
        ${khoiPhuongAn(c, true)}
        ${giaiThich(c)}
      </div>
    </div>
    <div class="bt-dieu-huong hop-cau-dh">
      <button class="nut" type="button" id="cau-truoc" ${i === 0 ? "disabled" : ""}>${ic("arrow-left")} Câu trước</button>
      <span class="phu nho-chu">Câu ${i + 1} trên ${n}</span>
      <button class="nut chinh" type="button" id="cau-sau" ${i === n - 1 ? "disabled" : ""}>Câu sau ${ic("arrow-right")}</button>
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
  const loiKhen = ti >= 0.9 ? "Xuất sắc! Bạn đã nắm rất vững kiến thức biển báo!" : ti >= 0.7 ? "Tốt lắm! Bạn đã hoàn thành bài luyện tập đạt yêu cầu!" : "Cần ôn luyện thêm! Xem đáp án chi tiết bên dưới để rút kinh nghiệm.";
  main.innerHTML = `
  <div class="dau-trang kq-dau-trang">
    <div class="kq-dau-trai">
      <div class="kq-badge">${ic("check-circle")}<span>Hoàn thành bài luyện tập</span></div>
      <h1>${ic("target")}Kết quả bài tập</h1>
      <p class="mo-ta">${esc(r.ten)}</p>
    </div>
  </div>
  <div id="trang-thai-luu" class="phu nho-chu" role="status" aria-live="polite"></div>
  <div class="the kq-hero-the">
    <div class="ket-qua-bt">
      <div class="cup">
        ${CUP}
        <div class="ruy-bang ${ti >= 0.8 ? "" : "thap"}">${r.dung} / ${r.tong} Điểm</div>
        <h2>${loiKhen}</h2>
      </div>
      <div class="kq-chi-tiet-grid">
        <div class="kq-chi-tiet-card mau-la">
          <div class="kq-ct-icon">${ic("check-circle")}</div>
          <div class="kq-ct-info"><span class="phu nho-chu">Số câu đúng</span><b>${r.dung} câu</b></div>
        </div>
        <div class="kq-chi-tiet-card mau-do">
          <div class="kq-ct-icon">${ic("x-circle")}</div>
          <div class="kq-ct-info"><span class="phu nho-chu">Sai hoặc bỏ trống</span><b>${r.tong - r.dung} câu</b></div>
        </div>
        <div class="kq-chi-tiet-card mau-xanh">
          <div class="kq-ct-icon">${ic("percent")}</div>
          <div class="kq-ct-info"><span class="phu nho-chu">Độ chính xác</span><b>${pct1(ti)}</b></div>
        </div>
        <div class="kq-chi-tiet-card mau-tim">
          <div class="kq-ct-icon">${ic("clock")}</div>
          <div class="kq-ct-info"><span class="phu nho-chu">Thời gian làm bài</span><b>${mmss(r.giay)}</b></div>
        </div>
      </div>
    </div>
    <div class="hang-nut kq-nut-hang">
      ${sai.length ? `<button class="nut cam" id="on-sai" type="button">${ic("refresh")}Ôn lại ${sai.length} câu sai</button>` : ""}
      <button class="nut" id="lam-lai" type="button">${ic("refresh")}Làm lại bài này</button>
      <button class="nut chinh" id="bai-khac" type="button">${ic("target")}Luyện bài tập khác</button>
    </div>
  </div>
  <section class="the kq-dap-an-the">
    <div class="kq-dau">
      <div class="kq-dap-an-tieu-de">
        <h2>${ic("grid")} Chi tiết đáp án & giải thích</h2>
        <p class="phu nho-chu">Nhấn vào từng câu hỏi để xem hình ảnh phóng to, đáp án và giải thích quy chuẩn QCVN 41.</p>
      </div>
      <div class="chip-loc" role="group" aria-label="Lọc câu">
        <button type="button" data-loc="tat-ca" aria-pressed="true">Tất cả (${r.tong})</button>
        <button type="button" data-loc="sai" aria-pressed="false">Câu sai (${r.tong - r.dung})</button>
        <button type="button" data-loc="dung" aria-pressed="false">Câu đúng (${r.dung})</button>
      </div>
    </div>
    <div class="kq-luoi">${BT.cau.map((c, i) => {
      const tt = trangThaiCau(c), dungIdx = c.lua_chon.indexOf(c.dap_an);
      return `<button type="button" class="kq-o ${tt.lop}" data-xem="${i}" aria-label="Câu ${i + 1}: ${tt.nhan}">
        <div class="kq-o-top">
          <span class="kq-so">Câu ${i + 1}</span>
          ${c.danh_dau ? `<span class="kq-flag-tag">${ic("bookmark", "ic co")}</span>` : ""}
        </div>
        <div class="kq-o-anh">${anhBien(c.dap_an.ma)}</div>
        <span class="kq-tt ${tt.lop}">${ic(tt.icon)}${tt.nhan}</span>
        <div class="kq-o-lua-chon"><span class="phu nho-chu">Chọn: <b>${c.chon === null ? "–" : "ABCD"[c.chon]}</b></span><span class="phu nho-chu">Đúng: <b class="kq-dap-an-chu">${"ABCD"[dungIdx]}</b></span></div>
      </button>`;
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
    Object.assign(BT, { dangLam: true, i: 0, batDau: Date.now(), ketQua: null, lanNop: null });
    diToi("#/bai-tap/lam");
  };
  $("#bai-khac").onclick = () => { BT.ketQua = null; diToi("#/bai-tap"); };
  veTrangThaiLuuBai();
  if (BT.lanNop?.trangThai === "da-luu" && BT.lanNop?.vuaMoiLuu) {
    BT.lanNop.vuaMoiLuu = false;
    window.kiemTraVaHienThiKhaoSatNhanh?.({ attemptId: BT.lanNop.ketQua?.attempt_id });
  }
}

/* =========================== 8. THONG KE =========================== */
function chuoiNgay() {
  const co = new Set(D.ngay), d = new Date();
  if (!co.has(ngayStr(d))) d.setDate(d.getDate() - 1);
  let n = 0;
  while (co.has(ngayStr(d))) { n++; d.setDate(d.getDate() - 1); }
  return n;
}
function veThongKe() {
  window.hienThiThongKe({ main, ic, esc, S });
}



/* =========================== 9. NGUOI HOC =========================== */
async function veNguoiHoc(dangSua = false, denDanhGia = false) {
  window.dongKhaoSat?.();
  const n = soDaHoc(), cd = D.cai_dat;
  const tongBien = S.bien.length;
  const phanTram = tongBien ? Math.round((n / tongBien) * 100) : 0;
  const tk = window.TAI_KHOAN_GOOGLE || null;
  const dangChinhSua = dangSua && !tk;

  const tenHienThi = tk ? (tk.ten || tk.username || "Học viên") : (D.ten || "Người học");
  const chuCaiDau = (tenHienThi.trim().split(/\s+/).pop()?.[0] || tenHienThi.trim()[0] || "H").toUpperCase();

  main.innerHTML = `
  <div class="dau-trang"><h1>${ic("user")}Thông tin người học</h1></div>
  <div class="nh-dashboard">
    <!-- KHU VUC A: HO SO NGUOI HOC -->
    <section class="nh-card nh-profile-card" aria-label="Hồ sơ người học">
      <div class="nh-profile-left">
        <span class="nh-avatar" id="ho-so-avatar">
          ${tk && tk.anh_dai_dien
              ? `<img src="${esc(tk.anh_dai_dien)}"
                      alt="Ảnh đại diện"
                      referrerpolicy="no-referrer"
                      onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'nh-avatar-chu',textContent:${JSON.stringify(chuCaiDau)}}))">`
              : `<span class="nh-avatar-chu">${esc(chuCaiDau)}</span>`}
        </span>
        <div class="nh-profile-meta">
          <div class="nh-profile-name-row">
            ${tk
                ? `<h2 class="nh-profile-name">${esc(tenHienThi)}</h2>`
                : dangChinhSua
                    ? `<input id="ten" class="nh-profile-name-input" value="${esc(D.ten)}" maxlength="40" aria-label="Tên người học">`
                    : `<h2 class="nh-profile-name">${esc(tenHienThi)}</h2>
                       <button type="button" class="nut nut-phu-nho nh-btn-outline" id="sua" aria-label="Sửa tên hiển thị">${ic("edit")} Đổi tên</button>`
            }
          </div>
          <div class="nh-profile-badges">
            <span class="nh-badge-role" id="nh-badge-loai-tk">
              ${tk ? "Tài khoản học viên" : "Chế độ khách"}
            </span>
            ${tk
                ? `<span class="huy-hieu-xanh">${ic("check")} Đang hoạt động</span>`
                : `<span class="huy-hieu-xam">Lưu trên trình duyệt</span>`
            }
          </div>
        </div>
      </div>

      <div class="nh-profile-right">
        <div class="nh-progress-block">
          <div class="nh-progress-head">
            <span class="nh-progress-label">Tiến độ học biển báo</span>
            <span class="nh-progress-val">${n}/${tongBien} biển (${phanTram}%)</span>
          </div>
          <div class="nh-progress-track">
            <span class="nh-progress-fill" style="width:${phanTram}%"></span>
          </div>
          <div class="nh-progress-sub" id="nh-tien-do-quiz">
            ${tk ? "Đang đồng bộ thống kê bài tập..." : "Tiến độ đang lưu cục bộ trên trình duyệt này."}
          </div>
        </div>
        <div class="nh-profile-actions">
          ${tk
              ? `<button class="nut nh-btn-outline" id="dang-xuat-google" type="button">
                   ${ic("logout")} Đăng xuất
                 </button>`
              : dangChinhSua
                  ? `<button class="nut chinh nut-phu-nho" id="luu-ten" type="button">${ic("check")} Lưu</button>
                     <button class="nut nut-phu-nho nh-btn-outline" id="huy-sua" type="button">Hủy</button>`
                  : `<a class="nut chinh nut-phu-nho" href="/login?next=/app%23/nguoi-hoc">Đăng nhập / Đăng ký</a>`
          }
        </div>
      </div>
    </section>

    <!-- KHU VUC B: BAO MAT & DANG NHAP -->
    <section class="nh-card" id="khu-vuc-bao-mat" aria-labelledby="td-bao-mat">
      <div class="nh-card-head">
        <div>
          <h2 class="nh-card-title" id="td-bao-mat">${ic("shield")}Bảo mật & Đăng nhập</h2>
          <p class="nh-card-desc">Quản lý thông tin và phương thức đăng nhập của bạn.</p>
        </div>
      </div>
      <div id="noi-dung-bao-mat">
        <p class="phu nho-chu">Đang tải thông tin bảo mật...</p>
      </div>
    </section>

    <!-- KHU VUC C: CAI DAT UNG DUNG -->
    <section class="nh-card" id="khu-vuc-cai-dat" aria-labelledby="td-cai-dat">
      <div class="nh-card-head">
        <div>
          <h2 class="nh-card-title" id="td-cai-dat">${ic("sun")}Cài đặt ứng dụng</h2>
          <p class="nh-card-desc">Tùy chỉnh âm thanh, thông báo và giao diện hiển thị.</p>
        </div>
      </div>
      <div class="nh-list">
        <div class="nh-row">
          <div class="nh-row-left">
            <span class="nh-row-ic">${ic("volume")}</span>
            <div class="nh-row-text">
              <span class="nh-row-label">Âm thanh</span>
              <span class="nh-row-val">Phát âm thanh phản hồi khi trả lời câu hỏi</span>
            </div>
          </div>
          <div class="nh-row-right">
            <label class="cong-tac"><input type="checkbox" id="am" ${cd.am_thanh ? "checked" : ""} aria-label="Âm thanh khi trả lời"><span></span></label>
          </div>
        </div>

        <div class="nh-row">
          <div class="nh-row-left">
            <span class="nh-row-ic">${ic("bell")}</span>
            <div class="nh-row-text">
              <span class="nh-row-label">Thông báo</span>
              <span class="nh-row-val">Hiển thị thông báo nhỏ khi lưu hoặc hoàn tất thao tác</span>
            </div>
          </div>
          <div class="nh-row-right">
            <label class="cong-tac"><input type="checkbox" id="tb" ${cd.thong_bao ? "checked" : ""} aria-label="Hiện thông báo nhỏ"><span></span></label>
          </div>
        </div>

        <div class="nh-row">
          <div class="nh-row-left">
            <span class="nh-row-ic">${ic("sun")}</span>
            <div class="nh-row-text">
              <span class="nh-row-label">Giao diện</span>
              <span class="nh-row-val">Chọn chế độ Sáng, Tối hoặc tự động theo thiết bị</span>
            </div>
          </div>
          <div class="nh-row-right">
            <div class="nhom-nut" role="group" aria-label="Giao diện">
              ${[["sang", "Sáng"], ["toi", "Tối"], ["tu-dong", "Tự động"]].map(([v, t]) => `<button type="button" data-gd="${v}" aria-pressed="${cd.giao_dien === v}">${t}</button>`).join("")}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- KHU VUC D: QUAN LY DU LIEU HOC TAP -->
    <section class="nh-card" id="khu-vuc-du-lieu" aria-labelledby="td-du-lieu">
      <div class="nh-card-head">
        <div>
          <h2 class="nh-card-title" id="td-du-lieu">${ic("database")}Quản lý dữ liệu học tập</h2>
          <p class="nh-card-desc">${tk
              ? "Bài tập mới nộp được lưu theo tài khoản trên máy chủ. Tiến độ đánh dấu biển báo và lịch sử nhận dạng dưới đây được lưu trên trình duyệt này."
              : "Dữ liệu học tập và lịch sử nhận dạng hiện chỉ được lưu cục bộ trên trình duyệt này."}</p>
        </div>
      </div>
      <div class="nh-list">
        <div class="nh-row">
          <div class="nh-row-left">
            <span class="nh-row-ic subtle">${ic("trash")}</span>
            <div class="nh-row-text">
              <span class="nh-row-label">Xóa lịch sử nhận dạng</span>
              <span class="nh-row-val">Hiện có ${D.nhan_dang.length} mục lịch sử nhận dạng đã lưu trên trình duyệt</span>
            </div>
          </div>
          <div class="nh-row-right">
            <button class="nut nut-phu-nho nh-btn-outline" id="xoa-nd" type="button">Xóa lịch sử</button>
          </div>
        </div>

        <div class="nh-row">
          <div class="nh-row-left">
            <span class="nh-row-ic warn">${ic("alert")}</span>
            <div class="nh-row-text">
              <span class="nh-row-label">Xóa toàn bộ dữ liệu học tập</span>
              <span class="nh-row-val">Đặt lại danh sách biển đã học và lịch sử trên trình duyệt (không xóa tài khoản)</span>
            </div>
          </div>
          <div class="nh-row-right">
            <button class="nut nut-phu-nho nh-btn-danger-outline" id="xoa-het" type="button">Đặt lại dữ liệu</button>
          </div>
        </div>
      </div>
    </section>

    <!-- Khu vuc Danh gia ung dung -->
    <div class="danh-gia-card" id="khu-vuc-danh-gia">
      <div class="danh-gia-card-head">
        <div class="danh-gia-card-info">
          <span class="danh-gia-card-ic">${ic("edit")}</span>
          <div>
            <h3>Đánh giá ứng dụng</h3>
            <p>Chia sẻ trải nghiệm và góp ý để cải thiện ứng dụng.</p>
          </div>
        </div>
        <div class="danh-gia-card-actions" id="danh-gia-actions">
          <button class="nut vien-xanh" type="button" id="nut-mo-khao-sat">
            ${ic("edit")}<span id="chu-nut-khao-sat">Đang tải…</span>
          </button>
        </div>
      </div>
      <section class="the ks-section danh-gia-card-form" id="danh-gia-ung-dung" aria-labelledby="ks-title" ${denDanhGia ? "" : "hidden"}></section>
    </div>
  </div>
  <div id="nh-modal-root"></div>`;

  // Helper Modal dung chung cho trang Nguoi hoc
  const modalRoot = $("#nh-modal-root");
  let dongModalHienTai = null;
  function dongModal() {
    if (dongModalHienTai) {
      dongModalHienTai();
      dongModalHienTai = null;
    }
    if (modalRoot) modalRoot.innerHTML = "";
  }
  function moModal({ title, icon = "shield", desc = "", bodyHtml = "", onMount }) {
    dongModal();
    if (!modalRoot) return;
    modalRoot.innerHTML = `
      <div class="nh-modal-backdrop" id="nh-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="nh-modal-title">
        <div class="nh-modal">
          <div class="nh-modal-head">
            <h3 class="nh-modal-title" id="nh-modal-title">${ic(icon)}<span>${esc(title)}</span></h3>
            <button type="button" class="nh-modal-close" id="nh-modal-close" aria-label="Đóng hộp thoại">${ic("x")}</button>
          </div>
          ${desc ? `<p class="nh-modal-desc">${esc(desc)}</p>` : ""}
          <div id="nh-modal-err" class="nh-modal-err" hidden></div>
          <div id="nh-modal-body">${bodyHtml}</div>
        </div>
      </div>
    `;
    const errBox = $("#nh-modal-err");
    const setModalErr = (msg) => {
      if (!errBox) return;
      if (msg) {
        errBox.textContent = msg;
        errBox.hidden = false;
      } else {
        errBox.textContent = "";
        errBox.hidden = true;
      }
    };
    const onKeyDown = (ev) => {
      if (ev.key === "Escape") dongModal();
    };
    document.addEventListener("keydown", onKeyDown);
    dongModalHienTai = () => document.removeEventListener("keydown", onKeyDown);

    $("#nh-modal-close").onclick = dongModal;
    $("#nh-modal-backdrop").onclick = (ev) => {
      if (ev.target && ev.target.id === "nh-modal-backdrop") dongModal();
    };
    onMount?.({ setModalErr, dongModal, modalRoot });
  }

  // Khoi tao khao sat trong section
  const formKhaoSat = $("#danh-gia-ung-dung");
  window.hienThiKhaoSat({ root: formKhaoSat, ic, esc });

  // Kiem tra thong bao tu redirect OAuth hoac lien ket Google
  const urlSearch = new URLSearchParams(window.location.search);
  const hashSearch = window.location.hash.includes("?")
    ? new URLSearchParams(window.location.hash.split("?")[1])
    : null;
  const getParam = (key) => urlSearch.get(key) || (hashSearch && hashSearch.get(key));

  if (getParam("linked") === "google_success") {
    thongBao("Đã liên kết tài khoản Google thành công!", true);
    history.replaceState(null, "", window.location.pathname + window.location.hash.split("?")[0]);
  } else if (getParam("error") === "google_already_linked") {
    thongBao("Tài khoản Google này đã được liên kết với một tài khoản khác.", true);
    history.replaceState(null, "", window.location.pathname + window.location.hash.split("?")[0]);
  } else if (getParam("error") === "link_invalid_session" || getParam("error") === "link_failed") {
    thongBao("Liên kết Google không thành công. Vui lòng thử lại.", true);
    history.replaceState(null, "", window.location.pathname + window.location.hash.split("?")[0]);
  }

  // Tai du lieu bai tap thuc te tu API neu da dang nhap
  if (tk) {
    fetch("/api/learning/overview", { credentials: "same-origin", cache: "no-store" })
      .then(r => r.ok ? r.json() : null)
      .then(ov => {
        const el = $("#nh-tien-do-quiz");
        if (!el) return;
        if (!ov) {
          el.textContent = "Đã kết nối tài khoản học tập.";
          return;
        }
        const soBai = Number(ov.completed_attempts ?? ov.total_attempts ?? 0);
        if (soBai > 0) {
          const chinhXac = Number(ov.overall_accuracy_percent ?? ov.accuracy_percent ?? 0).toFixed(1).replace(".", ",");
          el.textContent = `Đã hoàn thành ${soBai} lượt bài tập • Độ chính xác ${chinhXac}%`;
        } else {
          el.textContent = "Chưa có lượt bài tập nào được ghi nhận trên máy chủ.";
        }
      })
      .catch(() => {
        const el = $("#nh-tien-do-quiz");
        if (el) el.textContent = "Không thể tải thống kê bài tập từ máy chủ.";
      });
  }

  // Xu ly khu vuc Bao mat & Dang nhap
  const boxBaoMat = $("#noi-dung-bao-mat");

  if (!tk) {
    if (boxBaoMat) {
      boxBaoMat.innerHTML = `
        <div class="nh-guest-box">
          <div>
            <div class="nh-row-label">Bạn đang học ở chế độ khách</div>
            <div class="nh-row-val">Đăng nhập để quản lý tên tài khoản, liên kết email khôi phục, mật khẩu và đồng bộ bài tập.</div>
          </div>
          <div class="hang-nut">
            <a class="nut chinh nut-phu-nho" href="/login?next=/app%23/nguoi-hoc">Đăng nhập / Đăng ký</a>
            <a class="nut vien-xanh nut-phu-nho" href="/auth/google">Tiếp tục với Google</a>
          </div>
        </div>
      `;
    }
  } else {
    fetch("/api/auth/methods", { credentials: "same-origin", cache: "no-store" })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data || !data.methods) {
          if (boxBaoMat) boxBaoMat.innerHTML = `<p class="phu nho-chu">Không thể tải thông tin phương thức xác thực.</p>`;
          return;
        }
        const m = data.methods;
        const csrf = data.csrf_token || "";

        // Cap nhat nhan loai tai khoan tren the Ho so theo du lieu that
        const badgeLoai = $("#nh-badge-loai-tk");
        if (badgeLoai) {
          if (m.has_google && m.has_password) badgeLoai.textContent = "Tài khoản Google & Mật khẩu";
          else if (m.has_google) badgeLoai.textContent = "Tài khoản Google";
          else badgeLoai.textContent = "Tài khoản học viên";
        }

        const coEmail = !!(m.has_email && m.email);
        boxBaoMat.innerHTML = `
          <div class="nh-list">
            <!-- 1. Ten tai khoan -->
            <div class="nh-row">
              <div class="nh-row-left">
                <span class="nh-row-ic">${ic("at")}</span>
                <div class="nh-row-text">
                  <div class="nh-row-label-line">
                    <span class="nh-row-label">Tên tài khoản</span>
                    <span class="huy-hieu-xanh">${ic("check")} Đã kích hoạt</span>
                  </div>
                  <span class="nh-row-val" id="nh-val-username">${esc(m.username || "Chưa thiết lập")}</span>
                </div>
              </div>
              <div class="nh-row-right">
                <button type="button" class="nut nut-phu-nho nh-btn-outline" id="btn-open-edit-username">Đổi tên</button>
              </div>
            </div>

            <!-- 2. Dia chi email -->
            <div class="nh-row">
              <div class="nh-row-left">
                <span class="nh-row-ic ${coEmail ? "" : "warn"}">${ic("mail")}</span>
                <div class="nh-row-text">
                  <div class="nh-row-label-line">
                    <span class="nh-row-label">Địa chỉ email</span>
                    ${coEmail
                      ? (m.email_verified
                          ? `<span class="huy-hieu-xanh">${ic("check")} Đã xác minh</span>`
                          : `<span class="huy-hieu-vang">${ic("alert")} Chưa xác minh</span>`)
                      : `<span class="huy-hieu-xam">Chưa liên kết</span>`}
                  </div>
                  <span class="nh-row-val">${coEmail ? esc(m.email) : "Chưa liên kết email"}</span>
                  ${!coEmail
                    ? `<span class="nh-row-hint">Bạn chưa liên kết email. Hãy thêm email để khôi phục tài khoản khi quên mật khẩu.</span>`
                    : ""}
                </div>
              </div>
              <div class="nh-row-right">
                ${coEmail
                  ? `<button type="button" class="nut nut-phu-nho nh-btn-outline" id="btn-open-link-email">Thay đổi</button>`
                  : `<button type="button" class="nut nut-phu-nho chinh" id="btn-open-link-email">Liên kết email</button>`}
              </div>
            </div>

            <!-- 3. Tai khoan Google -->
            <div class="nh-row">
              <div class="nh-row-left">
                <span class="nh-row-ic">${ic("globe")}</span>
                <div class="nh-row-text">
                  <div class="nh-row-label-line">
                    <span class="nh-row-label">Tài khoản Google</span>
                    ${m.has_google
                      ? `<span class="huy-hieu-xanh">${ic("check")} Đã liên kết</span>`
                      : `<span class="huy-hieu-xam">Chưa liên kết</span>`}
                  </div>
                  <span class="nh-row-val">${m.has_google
                    ? (m.has_password ? "Đã liên kết với tài khoản Google" : "Phương thức đăng nhập duy nhất — hãy tạo mật khẩu trước khi hủy")
                    : "Chưa liên kết tài khoản Google"}</span>
                </div>
              </div>
              <div class="nh-row-right">
                ${m.has_google
                  ? (m.has_password
                      ? `<button type="button" class="nut nut-phu-nho nh-btn-danger-outline" id="btn-unlink-google">Hủy liên kết</button>`
                      : `<button type="button" class="nut nut-phu-nho nh-btn-outline" disabled title="Cần tạo mật khẩu cá nhân trước khi hủy">Không thể hủy</button>`)
                  : `<a class="nut nut-phu-nho vien-xanh" href="/auth/link-google">Liên kết Google</a>`}
              </div>
            </div>

            <!-- 4. Mat khau ca nhan -->
            <div class="nh-row">
              <div class="nh-row-left">
                <span class="nh-row-ic">${ic("lock")}</span>
                <div class="nh-row-text">
                  <div class="nh-row-label-line">
                    <span class="nh-row-label">Mật khẩu cá nhân</span>
                    ${m.has_password
                      ? `<span class="huy-hieu-xanh">${ic("check")} Đã thiết lập</span>`
                      : `<span class="huy-hieu-xam">Chưa thiết lập</span>`}
                  </div>
                  <span class="nh-row-val">${m.has_password ? "Đã thiết lập mật khẩu đăng nhập" : "Chưa thiết lập mật khẩu cá nhân"}</span>
                </div>
              </div>
              <div class="nh-row-right">
                ${m.has_password
                  ? `<button type="button" class="nut nut-phu-nho nh-btn-outline" id="btn-open-change-pw">Đổi mật khẩu</button>`
                  : `<button type="button" class="nut nut-phu-nho chinh" id="btn-open-set-pw">Thiết lập mật khẩu</button>`}
              </div>
            </div>
          </div>
        `;

        // 1. Modal Doi ten tai khoan
        const btnEditUsername = $("#btn-open-edit-username");
        if (btnEditUsername) {
          btnEditUsername.onclick = () => {
            moModal({
              title: "Đổi tên tài khoản",
              icon: "at",
              desc: "Tên tài khoản dùng để đăng nhập (3–30 ký tự, gồm chữ cái, số, dấu gạch dưới _ và dấu chấm .).",
              bodyHtml: `
                <form id="form-inapp-set-username">
                  <div class="nh-field">
                    <label for="inapp-new-username">Tên tài khoản mới</label>
                    <input type="text" id="inapp-new-username" class="nh-input" required minlength="3" maxlength="30" value="${esc(m.username || "")}" placeholder="Ví dụ: hocvien_ai">
                  </div>
                  <div class="nh-modal-foot">
                    <button type="button" class="nut nh-btn-outline" id="btn-cancel-username">Hủy</button>
                    <button type="submit" class="nut chinh" id="btn-save-username">${ic("check")} Lưu tên tài khoản</button>
                  </div>
                </form>
              `,
              onMount({ setModalErr, dongModal }) {
                const inp = $("#inapp-new-username");
                if (inp) { inp.focus(); inp.select(); }
                $("#btn-cancel-username").onclick = dongModal;
                $("#form-inapp-set-username").onsubmit = async (ev) => {
                  ev.preventDefault();
                  setModalErr("");
                  const newU = inp.value.trim();
                  if (!/^[a-zA-Z0-9_.]{3,30}$/.test(newU)) {
                    setModalErr("Tên tài khoản phải từ 3–30 ký tự, chỉ gồm chữ cái, số, dấu _ và dấu .");
                    return;
                  }
                  const btn = $("#btn-save-username");
                  btn.disabled = true;
                  btn.textContent = "Đang lưu...";
                  try {
                    const res = await fetch("/api/auth/set-username", {
                      method: "POST",
                      credentials: "same-origin",
                      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
                      body: JSON.stringify({ username: newU })
                    });
                    const rData = await res.json();
                    if (res.ok && rData.thanh_cong) {
                      if (window.TAI_KHOAN_GOOGLE) window.TAI_KHOAN_GOOGLE.username = rData.username || newU;
                      dongModal();
                      thongBao("Cập nhật tên tài khoản thành công!", true);
                      veNguoiHoc();
                    } else {
                      setModalErr(rData.thong_bao || "Không thể cập nhật tên tài khoản.");
                      btn.disabled = false;
                      btn.textContent = "Lưu tên tài khoản";
                    }
                  } catch {
                    setModalErr("Lỗi kết nối khi cập nhật tên tài khoản.");
                    btn.disabled = false;
                    btn.textContent = "Lưu tên tài khoản";
                  }
                };
              }
            });
          };
        }

        // 2. Modal Lien ket / Thay doi email (2 buoc + OTP)
        const btnLinkEmail = $("#btn-open-link-email");
        if (btnLinkEmail) {
          btnLinkEmail.onclick = () => {
            function moBuocNhapEmail() {
              moModal({
                title: coEmail ? "Thay đổi địa chỉ email" : "Liên kết địa chỉ email",
                icon: "mail",
                desc: "Nhập địa chỉ email mới. Hệ thống sẽ gửi mã OTP gồm 6 chữ số để xác minh quyền sở hữu.",
                bodyHtml: `
                  <form id="form-inapp-link-email">
                    <div class="nh-field">
                      <label for="inapp-new-email">Địa chỉ email mới</label>
                      <input type="email" id="inapp-new-email" class="nh-input" required placeholder="example@gmail.com">
                    </div>
                    ${m.has_password ? `
                    <div class="nh-field">
                      <label for="inapp-email-current-pw">Mật khẩu hiện tại (xác nhận bảo mật)</label>
                      <input type="password" id="inapp-email-current-pw" class="nh-input" required placeholder="Nhập mật khẩu hiện tại">
                    </div>` : ""}
                    <div class="nh-modal-foot">
                      <button type="button" class="nut nh-btn-outline" id="btn-cancel-link-email">Hủy</button>
                      <button type="submit" class="nut chinh" id="btn-send-link-otp">${ic("mail")} Gửi mã xác minh</button>
                    </div>
                  </form>
                `,
                onMount({ setModalErr, dongModal }) {
                  const emailInp = $("#inapp-new-email");
                  if (emailInp) emailInp.focus();
                  $("#btn-cancel-link-email").onclick = dongModal;
                  $("#form-inapp-link-email").onsubmit = async (ev) => {
                    ev.preventDefault();
                    setModalErr("");
                    const newEmail = emailInp.value.trim();
                    const curPw = m.has_password ? $("#inapp-email-current-pw").value : "";
                    if (!newEmail) { setModalErr("Vui lòng nhập địa chỉ email."); return; }
                    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newEmail)) {
                      setModalErr("Địa chỉ email không đúng định dạng.");
                      return;
                    }
                    if (m.has_password && !curPw) {
                      setModalErr("Vui lòng nhập mật khẩu hiện tại để xác nhận.");
                      return;
                    }
                    const btnSend = $("#btn-send-link-otp");
                    btnSend.disabled = true;
                    btnSend.textContent = "Đang gửi mã...";
                    try {
                      const res = await fetch("/api/auth/link-email", {
                        method: "POST",
                        credentials: "same-origin",
                        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
                        body: JSON.stringify({ email: newEmail, mat_khau_hien_tai: curPw })
                      });
                      const rData = await res.json();
                      if (res.ok && rData.thanh_cong) {
                        moBuocNhapOtp(newEmail, rData.email_da_che || newEmail);
                      } else {
                        setModalErr(rData.thong_bao || "Không thể gửi mã xác minh.");
                        btnSend.disabled = false;
                        btnSend.textContent = "Gửi mã xác minh";
                      }
                    } catch {
                      setModalErr("Lỗi kết nối khi gửi yêu cầu liên kết email.");
                      btnSend.disabled = false;
                      btnSend.textContent = "Gửi mã xác minh";
                    }
                  };
                }
              });
            }

            function moBuocNhapOtp(targetEmail, maskedEmail) {
              moModal({
                title: "Xác thực mã OTP email",
                icon: "mail",
                bodyHtml: `
                  <div class="nh-modal-info">
                    Mã xác nhận 6 chữ số đã được gửi tới <strong>${esc(maskedEmail)}</strong> (hiệu lực 5 phút).
                  </div>
                  <form id="form-inapp-verify-email-otp">
                    <div class="nh-field">
                      <label for="inapp-email-otp">Nhập mã OTP 6 chữ số</label>
                      <input type="text" id="inapp-email-otp" class="nh-input nh-otp-input" required maxlength="6" pattern="[0-9]{6}" inputmode="numeric" placeholder="••••••">
                    </div>
                    <div class="nh-modal-foot">
                      <button type="button" class="nut nh-btn-outline" id="btn-cancel-link-otp">Hủy</button>
                      <button type="submit" class="nut chinh" id="btn-submit-verify-link">${ic("check")} Xác nhận</button>
                    </div>
                  </form>
                `,
                onMount({ setModalErr, dongModal }) {
                  const otpInp = $("#inapp-email-otp");
                  if (otpInp) otpInp.focus();
                  $("#btn-cancel-link-otp").onclick = dongModal;
                  $("#form-inapp-verify-email-otp").onsubmit = async (ev) => {
                    ev.preventDefault();
                    setModalErr("");
                    const otp = otpInp.value.trim();
                    if (!/^\d{6}$/.test(otp)) {
                      setModalErr("Vui lòng nhập đúng 6 chữ số mã OTP.");
                      return;
                    }
                    const btnV = $("#btn-submit-verify-link");
                    btnV.disabled = true;
                    btnV.textContent = "Đang xác thực...";
                    try {
                      const res = await fetch("/api/auth/verify-link-email", {
                        method: "POST",
                        credentials: "same-origin",
                        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
                        body: JSON.stringify({ email: targetEmail, otp })
                      });
                      const rData = await res.json();
                      if (res.ok && rData.thanh_cong) {
                        if (window.TAI_KHOAN_GOOGLE) {
                          window.TAI_KHOAN_GOOGLE.email = rData.email || targetEmail;
                          window.TAI_KHOAN_GOOGLE.email_verified = true;
                        }
                        dongModal();
                        thongBao("Đã liên kết email thành công!", true);
                        veNguoiHoc();
                      } else {
                        setModalErr(rData.thong_bao || "Mã xác thực không chính xác hoặc đã hết hạn.");
                        btnV.disabled = false;
                        btnV.textContent = "Xác nhận";
                      }
                    } catch {
                      setModalErr("Lỗi kết nối khi xác thực OTP.");
                      btnV.disabled = false;
                      btnV.textContent = "Xác nhận";
                    }
                  };
                }
              });
            }

            moBuocNhapEmail();
          };
        }

        // 3. Modal Huy lien ket Google
        const btnUnlink = $("#btn-unlink-google");
        if (btnUnlink) {
          btnUnlink.onclick = () => {
            moModal({
              title: "Hủy liên kết tài khoản Google",
              icon: "globe",
              desc: "Sau khi hủy liên kết Google, bạn vẫn có thể đăng nhập bằng tên tài khoản (hoặc email đã xác minh) và mật khẩu cá nhân.",
              bodyHtml: `
                <div class="nh-modal-foot">
                  <button type="button" class="nut nh-btn-outline" id="btn-cancel-unlink">Hủy</button>
                  <button type="button" class="nut nh-btn-danger-outline" id="btn-confirm-unlink">Xác nhận hủy liên kết</button>
                </div>
              `,
              onMount({ setModalErr, dongModal }) {
                $("#btn-cancel-unlink").onclick = dongModal;
                $("#btn-confirm-unlink").onclick = async () => {
                  const btn = $("#btn-confirm-unlink");
                  btn.disabled = true;
                  btn.textContent = "Đang xử lý...";
                  try {
                    const res = await fetch("/api/auth/unlink-google", {
                      method: "POST",
                      credentials: "same-origin",
                      headers: { "X-CSRF-Token": csrf }
                    });
                    const rData = await res.json();
                    if (res.ok && rData.thanh_cong) {
                      dongModal();
                      thongBao("Đã hủy liên kết Google thành công!", true);
                      veNguoiHoc();
                    } else {
                      setModalErr(rData.thong_bao || "Hủy liên kết thất bại.");
                      btn.disabled = false;
                      btn.textContent = "Xác nhận hủy liên kết";
                    }
                  } catch {
                    setModalErr("Lỗi kết nối khi hủy liên kết.");
                    btn.disabled = false;
                    btn.textContent = "Xác nhận hủy liên kết";
                  }
                };
              }
            });
          };
        }

        // 4. Modal Doi mat khau
        const btnChangePw = $("#btn-open-change-pw");
        if (btnChangePw) {
          btnChangePw.onclick = () => {
            moModal({
              title: "Đổi mật khẩu cá nhân",
              icon: "lock",
              desc: "Sử dụng mật khẩu tối thiểu 8 ký tự, kết hợp chữ cái và số để tăng cường bảo mật.",
              bodyHtml: `
                <form id="form-inapp-doi-mk">
                  <div class="nh-field">
                    <label for="inapp-old-pw">Mật khẩu hiện tại</label>
                    <input type="password" id="inapp-old-pw" class="nh-input" required placeholder="Nhập mật khẩu hiện tại">
                  </div>
                  <div class="nh-field">
                    <label for="inapp-new-pw">Mật khẩu mới (tối thiểu 8 ký tự)</label>
                    <input type="password" id="inapp-new-pw" class="nh-input" required placeholder="Nhập mật khẩu mới">
                  </div>
                  <div class="nh-field">
                    <label for="inapp-confirm-pw">Xác nhận mật khẩu mới</label>
                    <input type="password" id="inapp-confirm-pw" class="nh-input" required placeholder="Nhập lại mật khẩu mới">
                  </div>
                  <div class="nh-modal-foot">
                    <button type="button" class="nut nh-btn-outline" id="btn-cancel-doi-mk">Hủy</button>
                    <button type="submit" class="nut chinh" id="btn-save-doi-mk">${ic("check")} Lưu mật khẩu mới</button>
                  </div>
                </form>
              `,
              onMount({ setModalErr, dongModal }) {
                $("#inapp-old-pw")?.focus();
                $("#btn-cancel-doi-mk").onclick = dongModal;
                $("#form-inapp-doi-mk").onsubmit = async (ev) => {
                  ev.preventDefault();
                  setModalErr("");
                  const oldPw = $("#inapp-old-pw").value;
                  const newPw = $("#inapp-new-pw").value;
                  const cfPw = $("#inapp-confirm-pw").value;
                  if (!oldPw || !newPw) { setModalErr("Vui lòng nhập đầy đủ thông tin."); return; }
                  if (newPw.length < 8) { setModalErr("Mật khẩu mới phải có tối thiểu 8 ký tự."); return; }
                  if (newPw !== cfPw) { setModalErr("Mật khẩu xác nhận không khớp."); return; }

                  const btn = $("#btn-save-doi-mk");
                  btn.disabled = true;
                  btn.textContent = "Đang lưu...";
                  try {
                    const res = await fetch("/api/auth/change-password", {
                      method: "POST",
                      credentials: "same-origin",
                      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
                      body: JSON.stringify({ mat_khau_cu: oldPw, mat_khau_moi: newPw, xac_nhan_mat_khau: cfPw })
                    });
                    const rData = await res.json();
                    if (res.ok && rData.thanh_cong) {
                      dongModal();
                      thongBao("Đã đổi mật khẩu thành công!", true);
                      veNguoiHoc();
                    } else {
                      setModalErr(rData.thong_bao || "Đổi mật khẩu thất bại.");
                      btn.disabled = false;
                      btn.textContent = "Lưu mật khẩu mới";
                    }
                  } catch {
                    setModalErr("Lỗi kết nối khi đổi mật khẩu.");
                    btn.disabled = false;
                    btn.textContent = "Lưu mật khẩu mới";
                  }
                };
              }
            });
          };
        }

        // 5. Modal Thiet lap mat khau
        const btnSetPw = $("#btn-open-set-pw");
        if (btnSetPw) {
          btnSetPw.onclick = () => {
            moModal({
              title: "Thiết lập mật khẩu cho tài khoản",
              icon: "lock",
              desc: "Sau khi thiết lập, bạn có thể đăng nhập bằng tên tài khoản (hoặc email) và mật khẩu bên cạnh Google.",
              bodyHtml: `
                <form id="form-inapp-set-mk">
                  <div class="nh-field">
                    <label for="inapp-set-new-pw">Mật khẩu mới (tối thiểu 8 ký tự)</label>
                    <input type="password" id="inapp-set-new-pw" class="nh-input" required placeholder="Tối thiểu 8 ký tự">
                  </div>
                  <div class="nh-field">
                    <label for="inapp-set-confirm-pw">Xác nhận lại mật khẩu</label>
                    <input type="password" id="inapp-set-confirm-pw" class="nh-input" required placeholder="Nhập lại mật khẩu">
                  </div>
                  <div class="nh-modal-foot">
                    <button type="button" class="nut nh-btn-outline" id="btn-cancel-set-mk">Hủy</button>
                    <button type="submit" class="nut chinh" id="btn-save-set-mk">${ic("check")} Thiết lập mật khẩu</button>
                  </div>
                </form>
              `,
              onMount({ setModalErr, dongModal }) {
                $("#inapp-set-new-pw")?.focus();
                $("#btn-cancel-set-mk").onclick = dongModal;
                $("#form-inapp-set-mk").onsubmit = async (ev) => {
                  ev.preventDefault();
                  setModalErr("");
                  const newPw = $("#inapp-set-new-pw").value;
                  const cfPw = $("#inapp-set-confirm-pw").value;
                  if (!newPw) { setModalErr("Vui lòng nhập mật khẩu mới."); return; }
                  if (newPw.length < 8) { setModalErr("Mật khẩu mới phải có tối thiểu 8 ký tự."); return; }
                  if (newPw !== cfPw) { setModalErr("Mật khẩu xác nhận không khớp."); return; }

                  const btn = $("#btn-save-set-mk");
                  btn.disabled = true;
                  btn.textContent = "Đang xử lý...";
                  try {
                    const res = await fetch("/api/auth/set-password", {
                      method: "POST",
                      credentials: "same-origin",
                      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
                      body: JSON.stringify({ mat_khau_moi: newPw, xac_nhan_mat_khau: cfPw })
                    });
                    const rData = await res.json();
                    if (res.ok && rData.thanh_cong) {
                      dongModal();
                      thongBao("Đã thiết lập mật khẩu thành công!", true);
                      veNguoiHoc();
                    } else {
                      setModalErr(rData.thong_bao || "Thiết lập mật khẩu thất bại.");
                      btn.disabled = false;
                      btn.textContent = "Thiết lập mật khẩu";
                    }
                  } catch {
                    setModalErr("Lỗi kết nối khi thiết lập mật khẩu.");
                    btn.disabled = false;
                    btn.textContent = "Thiết lập mật khẩu";
                  }
                };
              }
            });
          };
        }
      })
      .catch(() => {
        if (boxBaoMat) boxBaoMat.innerHTML = `<p class="phu nho-chu">Không thể kết nối đến máy chủ bảo mật.</p>`;
      });
  }

  const nutMo = $("#nut-mo-khao-sat");
  const chuNut = $("#chu-nut-khao-sat");
  let daKhaoSat = false;

  // Kiem tra trang thai phieu khao sat cua user
  fetch("/api/survey/me", { credentials: "same-origin", cache: "no-store" })
    .then(r => r.ok ? r.json() : null)
    .then(data => {
      daKhaoSat = !!data?.has_response;
      capNhatNutKhaoSat();
    })
    .catch(() => {
      capNhatNutKhaoSat();
    });

  function capNhatNutKhaoSat() {
    if (!chuNut) return;
    const dangMo = !formKhaoSat.hidden;
    if (dangMo) {
      chuNut.textContent = "Thu gọn biểu mẫu";
    } else {
      chuNut.textContent = daKhaoSat ? "Xem / Chỉnh sửa đánh giá" : "Đánh giá ngay";
    }
  }

  capNhatNutKhaoSat();

  if (nutMo) {
    nutMo.onclick = () => {
      formKhaoSat.hidden = !formKhaoSat.hidden;
      capNhatNutKhaoSat();
      if (!formKhaoSat.hidden) {
        formKhaoSat.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    };
  }

  if (denDanhGia) {
    formKhaoSat.hidden = false;
    capNhatNutKhaoSat();
    setTimeout(() => {
      formKhaoSat.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }
  if (dangChinhSua) {
    const o = $("#ten"); o.focus(); o.select();
    const luu = () => { D.ten = o.value.trim() || "Người học"; luuKho(); capNhatTenNho(); veNguoiHoc(); thongBao("Đã lưu tên."); };
    $("#luu-ten").onclick = luu; $("#huy-sua").onclick = () => veNguoiHoc();
    o.onkeydown = e => { if (e.key === "Enter") luu(); if (e.key === "Escape") veNguoiHoc(); };
  } else if ($("#sua")) {
    $("#sua").onclick = () => veNguoiHoc(true);
  }

  const nutDangXuat = $("#dang-xuat-google");
  if (nutDangXuat) {
    nutDangXuat.onclick = () => {
      window.dangXuatGoogle();
    };
  }

  $("#am").onchange = e => { cd.am_thanh = e.target.checked; luuKho(); if (e.target.checked) phatAm(true); };
  $("#tb").onchange = e => { cd.thong_bao = e.target.checked; luuKho(); thongBao("Đã bật thông báo."); };
  $$("[data-gd]").forEach(b => b.onclick = () => {
    cd.giao_dien = b.dataset.gd; luuKho(); apGiaoDien();
    $$("[data-gd]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
  });

  // Modal xac nhan Xoa lich su nhan dang
  $("#xoa-nd").onclick = () => {
    moModal({
      title: "Xóa lịch sử nhận dạng",
      icon: "trash",
      desc: "Thao tác này sẽ xóa toàn bộ lịch sử ảnh nhận dạng AI đang lưu cục bộ trên trình duyệt.",
      bodyHtml: `
        <div class="nh-modal-scope">
          <strong>Chi tiết thao tác:</strong>
          <ul>
            <li><strong>Sẽ bị xóa:</strong> ${D.nhan_dang.length} bản ghi lịch sử nhận dạng trên trình duyệt.</li>
            <li><strong>Được giữ nguyên:</strong> Tiến độ học biển báo, tài khoản và lịch sử bài tập trên máy chủ.</li>
          </ul>
        </div>
        <div class="nh-modal-foot">
          <button type="button" class="nut nh-btn-outline" id="btn-cancel-xoa-nd">Hủy</button>
          <button type="button" class="nut nh-btn-danger-outline" id="btn-confirm-xoa-nd">Xác nhận xóa</button>
        </div>
      `,
      onMount({ dongModal }) {
        $("#btn-cancel-xoa-nd").onclick = dongModal;
        $("#btn-confirm-xoa-nd").onclick = () => {
          D.nhan_dang = [];
          luuKho();
          dongModal();
          veNguoiHoc();
          thongBao("Đã xóa lịch sử nhận dạng trên trình duyệt.", true);
        };
      }
    });
  };

  // Modal xac nhan Xoa toan bo du lieu hoc tap
  $("#xoa-het").onclick = () => {
    moModal({
      title: "Xóa toàn bộ dữ liệu học tập?",
      icon: "alert",
      desc: "Thao tác này không thể hoàn tác. Vui lòng kiểm tra kỹ phạm vi dữ liệu bị ảnh hưởng.",
      bodyHtml: `
        <div class="nh-modal-scope">
          <strong>Sẽ bị xóa trên trình duyệt này:</strong>
          <ul>
            <li>Danh sách ${n} biển báo đã đánh dấu học.</li>
            <li>Toàn bộ lịch sử nhận dạng (${D.nhan_dang.length} mục) và bài tập lưu cục bộ.</li>
          </ul>
          <strong style="display:block;margin-top:10px">Được giữ nguyên an toàn:</strong>
          <ul>
            <li>Tài khoản đăng nhập, email và liên kết Google của bạn.</li>
            <li>Cài đặt âm thanh, thông báo, giao diện và lịch sử bài tập đã lưu trên máy chủ.</li>
          </ul>
        </div>
        <div class="nh-modal-foot">
          <button type="button" class="nut nh-btn-outline" id="btn-cancel-xoa-het">Hủy</button>
          <button type="button" class="nut nh-btn-danger-outline" id="btn-confirm-xoa-het">Xác nhận đặt lại</button>
        </div>
      `,
      onMount({ dongModal }) {
        $("#btn-cancel-xoa-het").onclick = dongModal;
        $("#btn-confirm-xoa-het").onclick = () => {
          D = { ...macDinh(), cai_dat: cd };
          luuKho();
          capNhatTenNho();
          dongModal();
          veNguoiHoc();
          thongBao("Đã xóa toàn bộ dữ liệu học tập trên trình duyệt.", true);
        };
      }
    });
  };
}

/* =========================== KHOI DONG =========================== */
(async function khoiDong() {
  apGiaoDien(); capNhatTenNho(); apThuGon();
  try {
    const d = await (await fetch("/api/bien")).json();
    S.bien = d.bien; S.nguong = d.nguong; S.quizBankVersion = d.quiz_bank_version;
    S.bien.forEach(b => { S.theoMa[b.ma] = b; });
  } catch {
    main.innerHTML = `<div class="the"><p class="loi">Không kết nối được máy chủ. Hãy chạy lại chay_ung_dung.bat rồi tải lại trang.</p></div>`;
    return;
  }
  window.addEventListener("hashchange", dieuHuong);
  if (location.hash === "#/bai-tap/ket-qua") khoiPhucBaiNop();
  dieuHuong();
})();
