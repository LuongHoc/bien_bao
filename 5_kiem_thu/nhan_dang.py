# -*- coding: utf-8 -*-
"""
nhan_dang.py - Chay thu mo hinh tren may (khong can PyTorch, chi can onnxruntime + OpenCV).

  python nhan_dang.py --anh duong_dan.jpg
  python nhan_dang.py --video duong_dan.mp4 [--luu ket_qua.mp4]
  python nhan_dang.py --camera 0
  python nhan_dang.py --thu_muc ..\\1_du_lieu\\anh_tu_chup      (danh gia DOC LAP tren anh tu chup)

Mo hinh doc tu thu muc ..\\3_mo_hinh: phat_hien.onnx, phan_loai.onnx, lop.json, nguong.json,
(tuy chon) y_nghia.json dang {"P.102": {"ten": "Cam di nguoc chieu", "y_nghia": "..."}}.
"""
import os, sys, json, csv, glob, time, argparse
from collections import Counter, defaultdict
import numpy as np
import cv2
import onnxruntime as ort

GOC = os.path.dirname(os.path.abspath(__file__))
DUOI_ANH = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')


class NhanDang:
    def __init__(self, thu_muc_mo_hinh, nguong_phat_hien=0.25):
        tm = thu_muc_mo_hinh
        nhacc = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if 'CUDAExecutionProvider' in ort.get_available_providers() else ['CPUExecutionProvider']
        self.det = ort.InferenceSession(os.path.join(tm, 'phat_hien.onnx'), providers=nhacc)
        self.cls = ort.InferenceSession(os.path.join(tm, 'phan_loai.onnx'), providers=nhacc)
        self.lop = json.load(open(os.path.join(tm, 'lop.json'), encoding='utf-8'))
        cfg = json.load(open(os.path.join(tm, 'nguong.json'), encoding='utf-8'))
        self.nguong, self.T, self.co, self.pad = cfg['nguong'], cfg['nhiet_do_T'], cfg['co_anh'], cfg['pad']
        self.lop_nen = cfg.get('lop_nen', 'KHONG_PHAI_BIEN')
        p = os.path.join(tm, 'y_nghia.json')
        self.y_nghia = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {}
        ip = self.det.get_inputs()[0]
        self.det_in = ip.name
        self.det_sz = ip.shape[2] if isinstance(ip.shape[2], int) else 640
        self.nguong_det = nguong_phat_hien

    # ---------- phat hien (YOLO, 1 lop)
    def phat_hien(self, img):
        H, W = img.shape[:2]; s = self.det_sz
        r = min(s / H, s / W); nh, nw = int(round(H * r)), int(round(W * r))
        pad_y, pad_x = (s - nh) // 2, (s - nw) // 2
        canvas = np.full((s, s, 3), 114, np.uint8)
        canvas[pad_y:pad_y + nh, pad_x:pad_x + nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        x = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        out = self.det.run(None, {self.det_in: x})[0][0]          # (4+1, N)
        out = out.T
        diem = out[:, 4]
        m = diem >= self.nguong_det
        if not m.any():
            return []
        b, diem = out[m, :4], diem[m]
        x1 = (b[:, 0] - b[:, 2] / 2 - pad_x) / r; y1 = (b[:, 1] - b[:, 3] / 2 - pad_y) / r
        w, h = b[:, 2] / r, b[:, 3] / r
        idx = cv2.dnn.NMSBoxes(np.stack([x1, y1, w, h], 1).tolist(), diem.tolist(), self.nguong_det, 0.5)
        kq = []
        for i in np.array(idx).reshape(-1)[:30]:          # toi da 30 bien/anh (NMS da sap xep theo diem)
            xa, ya = max(0, x1[i]), max(0, y1[i]); xb, yb = min(W, x1[i] + w[i]), min(H, y1[i] + h[i])
            if xb - xa > 2 and yb - ya > 2:
                kq.append((float(xa), float(ya), float(xb), float(yb), float(diem[i])))
        return kq

    # ---------- phan loai (CNN tu huan luyen) - cat anh GIONG HET luc huan luyen
    def phan_loai(self, img, hop):
        H, W = img.shape[:2]; anh = []
        for (x1, y1, x2, y2, _) in hop:
            px, py = (x2 - x1) * self.pad, (y2 - y1) * self.pad
            a, b = int(max(0, x1 - px)), int(max(0, y1 - py))
            c, d = int(min(W, x2 + px)), int(min(H, y2 + py))
            cr = cv2.resize(img[b:d, a:c], (self.co, self.co), interpolation=cv2.INTER_AREA)
            anh.append(cv2.cvtColor(cr, cv2.COLOR_BGR2RGB))
        if not anh:
            return []
        x = (np.stack(anh).astype(np.float32) / 255.0 - 0.5) / 0.5
        logits = self.cls.run(None, {self.cls.get_inputs()[0].name: x.transpose(0, 3, 1, 2)})[0] / self.T
        e = np.exp(logits - logits.max(1, keepdims=True)); p = e / e.sum(1, keepdims=True)
        return [(self.lop[int(i)], float(p[k, i])) for k, i in enumerate(p.argmax(1))]

    def xu_ly(self, img):
        hop = self.phat_hien(img)
        kq = []
        for h, (ma, tc) in zip(hop, self.phan_loai(img, hop)):
            if ma == self.lop_nen:
                continue                                   # bo phat hien nham (khong phai bien)
            kq.append({"hop": h[:4], "diem_phat_hien": h[4], "ma": ma, "do_tin_cay": tc,
                       "chac_chan": tc >= self.nguong})
        return kq

    def ten(self, ma):
        v = self.y_nghia.get(ma)
        return f"{ma} {v['ten']}" if isinstance(v, dict) and v.get('ten') else ma


# ---------------------------------------------------------------- ve ket qua
def _font(co=20):
    try:
        from PIL import ImageFont
        for f in ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
            if os.path.isfile(f):
                return ImageFont.truetype(f, co)
    except Exception:
        pass
    return None


FONT = _font()


def ve(img, kq, nd):
    out = img.copy(); chu = []
    for r in kq:
        x1, y1, x2, y2 = map(int, r["hop"])
        mau = (0, 200, 0) if r["chac_chan"] else (0, 165, 255)
        cv2.rectangle(out, (x1, y1), (x2, y2), mau, 2)
        nhan = f"{nd.ten(r['ma'])} {r['do_tin_cay']:.0%}" if r["chac_chan"] else f"? {r['ma']} {r['do_tin_cay']:.0%}"
        chu.append((x1, max(0, y1 - 24), nhan, mau))
    if FONT is not None and chu:
        from PIL import Image, ImageDraw
        pil = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB)); dr = ImageDraw.Draw(pil)
        for x, y, t, m in chu:
            dr.rectangle(dr.textbbox((x, y), t, font=FONT), fill=(m[2], m[1], m[0])); dr.text((x, y), t, font=FONT, fill=(255, 255, 255))
        out = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    else:
        for x, y, t, m in chu:
            cv2.putText(out, t.encode('ascii', 'ignore').decode(), (x, y + 18), 0, 0.6, m, 2)
    return out


# ---------------------------------------------------------------- danh gia doc lap
def danh_gia_thu_muc(nd, goc, ra_csv):
    """goc/<ma_dung>/*.jpg. Moi anh lay bien co (diem_phat_hien x do_tin_cay) cao nhat lam du doan."""
    dong, dem = [], Counter(); theo_lop = defaultdict(Counter); cap_sai = Counter()
    for d in sorted(glob.glob(os.path.join(goc, '*'))):
        if not os.path.isdir(d):
            continue
        dung = os.path.basename(d).strip()
        trong_ds = dung in nd.lop
        for p in sorted(glob.glob(os.path.join(d, '*'))):
            if not p.lower().endswith(DUOI_ANH):
                continue
            img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)   # doc duoc duong dan tieng Viet
            if img is None:
                continue
            t0 = time.time(); kq = nd.xu_ly(img); ms = (time.time() - t0) * 1000
            if not kq:
                ket = "khong_phat_hien"; du, tc = "", 0.0
            else:
                r = max(kq, key=lambda r: r["diem_phat_hien"] * r["do_tin_cay"])
                du, tc = r["ma"], r["do_tin_cay"]
                if not r["chac_chan"]:
                    ket = "tu_choi"
                else:
                    ket = "dung" if du == dung else "sai"
            if not trong_ds:     # bien ngoai danh sach: tu choi / khong phat hien la hanh vi DUNG
                ket = "ngoai_ds_" + ("tu_choi_dung" if ket in ("tu_choi", "khong_phat_hien") else "nhan_nham")
            dem[ket] += 1; theo_lop[dung][ket] += 1
            if ket == "sai":
                cap_sai[(dung, du)] += 1
            dong.append([p, dung, du, f"{tc:.3f}", ket, f"{ms:.0f}"])
    with open(ra_csv, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(["anh", "ma_dung", "ma_du_doan", "do_tin_cay", "ket_qua", "thoi_gian_ms"]); w.writerows(dong)
    n = sum(v for k, v in dem.items() if not k.startswith("ngoai_ds"))
    print(f"\n=== DANH GIA DOC LAP: {len(dong)} anh, {n} anh thuoc danh sach {len(nd.lop)-1} bien ===")
    if n:
        print(f"Dung: {dem['dung']}/{n} = {dem['dung']/n:.2%} | Sai: {dem['sai']} | Tu choi: {dem['tu_choi']} | Khong phat hien: {dem['khong_phat_hien']}")
        cn = dem['dung'] + dem['sai']
        if cn:
            print(f"Do chinh xac tren anh duoc chap nhan: {dem['dung']}/{cn} = {dem['dung']/cn:.2%}")
    m = dem['ngoai_ds_tu_choi_dung'] + dem['ngoai_ds_nhan_nham']
    if m:
        print(f"Bien ngoai danh sach: tu choi dung {dem['ngoai_ds_tu_choi_dung']}/{m}")
    if dong:
        t = np.array([float(r[5]) for r in dong])
        print(f"Thoi gian xu ly/anh: p50 = {np.percentile(t, 50):.0f} ms, p95 = {np.percentile(t, 95):.0f} ms")
    if cap_sai:
        print("Cap nham lan nhieu nhat:", cap_sai.most_common(10))
    print("Chi tiet:", ra_csv)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mo_hinh", default=os.path.join(GOC, "..", "3_mo_hinh"))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--anh"); g.add_argument("--video"); g.add_argument("--camera", type=int); g.add_argument("--thu_muc")
    ap.add_argument("--luu", help="duong dan luu anh/video ket qua")
    ap.add_argument("--bo_khung", type=int, default=2, help="video/camera: xu ly 1 trong N khung hinh")
    ap.add_argument("--nguong_phat_hien", type=float, default=0.25)
    a = ap.parse_args()
    nd = NhanDang(a.mo_hinh, a.nguong_phat_hien)

    if a.thu_muc:
        danh_gia_thu_muc(nd, a.thu_muc, os.path.join(GOC, "ket_qua_danh_gia.csv")); return
    if a.anh:
        img = cv2.imdecode(np.fromfile(a.anh, np.uint8), cv2.IMREAD_COLOR)
        kq = nd.xu_ly(img)
        for r in kq:
            v = nd.y_nghia.get(r["ma"], {})
            print(f"{nd.ten(r['ma'])} | tin cay {r['do_tin_cay']:.1%} | {'chac chan' if r['chac_chan'] else 'KHONG chac chan'}"
                  + (f"\n   -> {v.get('y_nghia')}" if isinstance(v, dict) and v.get('y_nghia') else ""))
        if not kq:
            print("Khong tim thay bien bao.")
        out = ve(img, kq, nd)
        if a.luu:
            cv2.imencode(os.path.splitext(a.luu)[1] or ".jpg", out)[1].tofile(a.luu)
        else:
            cv2.imshow("Ket qua", out); cv2.waitKey(0)
        return
    cap = cv2.VideoCapture(a.camera if a.camera is not None else a.video)
    viet = None; i = 0; kq = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % max(1, a.bo_khung) == 0:
            kq = nd.xu_ly(fr)
        i += 1
        out = ve(fr, kq, nd)
        if a.luu:
            if viet is None:
                viet = cv2.VideoWriter(a.luu, cv2.VideoWriter_fourcc(*"mp4v"), cap.get(cv2.CAP_PROP_FPS) or 25, (out.shape[1], out.shape[0]))
            viet.write(out)
        else:
            cv2.imshow("Nhan dang bien bao (q de thoat)", out)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    cap.release()
    if viet:
        viet.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
