# -*- coding: utf-8 -*-
"""
xu_ly_du_lieu.py - Gop nhieu bo du lieu bien bao (dinh dang YOLO) thanh:
  (1) bo du lieu PHAT HIEN: 1 lop "bien_bao" cho YOLO
  (2) bo du lieu PHAN LOAI: anh cat tung bien, moi thu muc la 1 ma QCVN 41:2024
Cac buoc: quet nguon -> anh xa nhan -> khu trung lap -> chia tap -> cat anh.
Tap KIEM THU lay tu NGUON DOC LAP (khong tron vao huan luyen), tranh loi
"train/test cung nguon" ma giao vien da nhan xet.
"""
import os, re, csv, json, glob, random, shutil, unicodedata
from collections import defaultdict, Counter
import numpy as np
import cv2
import yaml

DUOI_ANH = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
PAD = 0.15          # le them quanh hop bao khi cat bien (PHAI giong luc nhan dang)
CO_ANH_PL = 64      # kich thuoc anh dau vao bo phan loai
CANH_MIN = 12       # bo hop bao nho hon 12 px (qua nho de nhan dang)
LOP_NEN = "KHONG_PHAI_BIEN"

# ---------------------------------------------------------------- anh xa nhan
MA_RE = re.compile(r'(?<![A-Za-z])(DP|[PRWIS])[\s._\-]*(\d{3})([a-z](?![a-z]))?(?!\d)', re.I)

# Chi ghi nhung ten chac chan; ten khac se dua vao anh_xa_nhan.csv de nguoi dung tu dien.
TU_DIEN = {
    "no entry": "P.102", "cam di nguoc chieu": "P.102",
    "no passing": "P.125", "cam vuot": "P.125",
    "stop": "P.122", "dung lai": "P.122",
    "no stop or parking": "P.130", "no stopping and parking": "P.130", "cam dung va do xe": "P.130",
    "no parking": "P.131a", "cam do xe": "P.131a",
    "no vehicles": "P.101", "duong cam": "P.101",
    "vehicle no turn right": "P.103b", "vehicle no turn left": "P.103c",
    "no turn left": "P.123a", "no left turn": "P.123a", "cam re trai": "P.123a",
    "no turn right": "P.123b", "no right turn": "P.123b", "cam re phai": "P.123b",
    "pedestrians (warning)": "W.224", "children crossing": "W.225", "tre em": "W.225",
}
TU_BO = ("traffic light", "den giao thong", "person", "car", "motorbike", "vehicle_obj")


def bo_dau(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.replace('đ', 'd').replace('Đ', 'D')


def chuan_hoa_ten(s):
    return re.sub(r'[\s_\-]+', ' ', bo_dau(s).lower()).strip()


def doan_ma(ten_lop):
    """Tra ve (ma, cach) voi cach = 'ma_trong_ten' | 'tu_dien' | 'bo' | ''."""
    m = MA_RE.search(str(ten_lop))
    if m:
        ma = f"{m.group(1).upper()}.{m.group(2)}{(m.group(3) or '').lower()}"
        if ma == "P.127":  # bien toc do: tach theo so km/h
            con = MA_RE.sub(' ', str(ten_lop))
            v = re.search(r'(?<!\d)(\d{2,3})(?!\d)', con)
            if v:
                ma += f"({int(v.group(1))})"
        return ma, "ma_trong_ten"
    k = chuan_hoa_ten(ten_lop)
    if k in TU_DIEN:
        return TU_DIEN[k], "tu_dien"
    v = re.search(r'(?<!\d)(\d{2,3})(?!\d)', k)
    if v and any(t in k for t in ("speed limit", "toc do toi da", "gioi han toc do", "max speed")):
        return f"P.127({int(v.group(1))})", "tu_dien"
    if k in TU_BO:
        return "BO", "bo"
    return "", ""


# ---------------------------------------------------------------- doc nguon YOLO
def doc_ten_lop(goc):
    for p in sorted(glob.glob(os.path.join(goc, '**', '*.y*ml'), recursive=True)):
        try:
            d = yaml.safe_load(open(p, encoding='utf-8'))
        except Exception:
            continue
        if isinstance(d, dict) and 'names' in d:
            n = d['names']
            if isinstance(n, dict):
                return [str(n[k]) for k in sorted(n, key=lambda x: int(x))]
            return [str(x) for x in n]
    for ten in ('classes.txt', 'obj.names', '_darknet.labels', 'classes.names'):
        for p in glob.glob(os.path.join(goc, '**', ten), recursive=True):
            return [l.strip() for l in open(p, encoding='utf-8') if l.strip()]
    return None


def _tim_nhan(duong_anh):
    goc, _ = os.path.splitext(duong_anh)
    ung_vien = [goc + '.txt']
    parts = duong_anh.replace('\\', '/').split('/')
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].lower() in ('images', 'image', 'imgs', 'jpegimages'):
            q = parts[:i] + ['labels'] + parts[i + 1:]
            ung_vien.append(os.path.splitext('/'.join(q))[0] + '.txt')
            break
    for u in ung_vien:
        if os.path.isfile(u):
            return u
    return None


def doc_hop_bao(duong_nhan):
    """Doc nhan YOLO; ho tro ca dong polygon (chuyen thanh hop bao)."""
    hop = []
    for l in open(duong_nhan, encoding='utf-8', errors='ignore'):
        v = l.split()
        if len(v) < 5:
            continue
        try:
            c = int(float(v[0])); so = [float(x) for x in v[1:]]
        except ValueError:
            continue
        if len(so) == 4:
            cx, cy, w, h = so
        else:  # polygon x1 y1 x2 y2 ...
            xs, ys = so[0::2], so[1::2]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            w, h = max(xs) - min(xs), max(ys) - min(ys)
        if w > 0 and h > 0:
            hop.append((c, cx, cy, w, h))
    return hop


def quet_nguon(ten_nguon, goc):
    """Tra ve dict: ten_lop (list|None), anh: list(duong_anh, hop_bao)."""
    ten_lop = doc_ten_lop(goc)
    anh = []
    for p in glob.glob(os.path.join(goc, '**', '*'), recursive=True):
        if not p.lower().endswith(DUOI_ANH):
            continue
        n = _tim_nhan(p)
        if n is None:
            continue
        anh.append((p, doc_hop_bao(n)))
    anh.sort(key=lambda t: t[0])
    return {"nguon": ten_nguon, "goc": goc, "ten_lop": ten_lop, "anh": anh}


# ---------------------------------------------------------------- bang anh xa
def tao_bang_anh_xa(ds_nguon, duong_csv, thu_muc_mau, so_mau=6):
    """Ghi anh_xa_nhan.csv (nguon, id_lop, ten_lop, so_hop, ma_qcvn, cach) va anh mau cho lop chua ro."""
    cu = {}
    if os.path.isfile(duong_csv):  # giu lai phan nguoi dung da sua
        for r in csv.DictReader(open(duong_csv, encoding='utf-8-sig')):
            cu[(r['nguon'], r['id_lop'])] = r
    dem = Counter(); mau = defaultdict(list)
    for ng in ds_nguon:
        for p, hop in ng['anh']:
            for h in hop:
                k = (ng['nguon'], str(h[0])); dem[k] += 1
                if len(mau[k]) < so_mau:
                    mau[k].append((p, h))
    dong = []
    for ng in ds_nguon:
        ids = sorted({int(k[1]) for k in dem if k[0] == ng['nguon']})
        for i in ids:
            k = (ng['nguon'], str(i))
            ten = ng['ten_lop'][i] if ng['ten_lop'] and i < len(ng['ten_lop']) else f"lop_{i}"
            if k in cu:  # da co trong bang -> giu nguyen phan nguoi dung da sua
                ma, cach = cu[k]['ma_qcvn'], cu[k].get('cach', '')
            else:
                ma, cach = doan_ma(ten)
            dong.append({"nguon": k[0], "id_lop": k[1], "ten_lop": ten, "so_hop": dem[k],
                         "ma_qcvn": ma, "cach": cach})
            if not ma:  # luu anh mau de nguoi dung nhin va dien ma
                d = os.path.join(thu_muc_mau, f"{k[0]}__{i}__{re.sub(r'[^A-Za-z0-9]+', '_', bo_dau(ten))[:40]}")
                os.makedirs(d, exist_ok=True)
                for j, (p, h) in enumerate(mau[k]):
                    img = cv2.imread(p)
                    if img is not None:
                        c = cat_bien(img, h[1:])
                        if c is not None:
                            cv2.imwrite(os.path.join(d, f"{j}.png"), cv2.resize(c, (128, 128)))
    with open(duong_csv, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(dong[0].keys()) if dong else ["nguon"])
        w.writeheader(); w.writerows(dong)
    return dong


def doc_bang_anh_xa(duong_csv):
    """(nguon,id) -> ma. Dong do nguoi dung sua: dat cach='nguoi_dung' hoac chi can sua ma_qcvn."""
    bang = {}
    for r in csv.DictReader(open(duong_csv, encoding='utf-8-sig')):
        ma = (r.get('ma_qcvn') or '').strip()
        if ma.upper() in ('BO', 'KHAC'):
            ma = ma.upper()
        elif ma:
            ma = doan_ma(ma)[0] or ma
        bang[(r['nguon'], r['id_lop'])] = ma
    return bang


# ---------------------------------------------------------------- cat anh
def cat_bien(img, xywh, pad=PAD):
    H, W = img.shape[:2]
    cx, cy, w, h = xywh
    x1, x2 = (cx - w / 2) * W, (cx + w / 2) * W
    y1, y2 = (cy - h / 2) * H, (cy + h / 2) * H
    if min(x2 - x1, y2 - y1) < CANH_MIN:
        return None
    px, py = (x2 - x1) * pad, (y2 - y1) * pad
    x1, y1 = int(max(0, x1 - px)), int(max(0, y1 - py))
    x2, y2 = int(min(W, x2 + px)), int(min(H, y2 + py))
    if x2 - x1 < 4 or y2 - y1 < 4:
        return None
    return img[y1:y2, x1:x2]


# ---------------------------------------------------------------- khu trung lap
def dhash(duong):
    g = cv2.imread(duong, cv2.IMREAD_GRAYSCALE)
    if g is None:
        return None
    g = cv2.resize(g, (9, 8), interpolation=cv2.INTER_AREA)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    return np.packbits(bits).view('>u8')[0].astype(np.uint64)


def _popcount(x):
    if hasattr(np, 'bitwise_count'):
        return np.bitwise_count(x)
    return np.unpackbits(x.view(np.uint8).reshape(-1, 8), axis=1).sum(1).reshape(x.shape)


def gan_trung(h_kt, h_hl, nguong=6, khoi=512):
    """Mask: anh kiem thu nao gan trung (Hamming <= nguong) voi bat ky anh huan luyen nao."""
    h_kt = np.asarray(h_kt, dtype=np.uint64); h_hl = np.asarray(h_hl, dtype=np.uint64)
    trung = np.zeros(len(h_kt), bool)
    for i in range(0, len(h_kt), khoi):
        d = _popcount(np.bitwise_xor(h_kt[i:i + khoi, None], h_hl[None, :]))
        trung[i:i + khoi] = (d <= nguong).any(1)
    return trung


# ---------------------------------------------------------------- xay dung bo du lieu
def xay_dung(ds_nguon, bang, nguon_kiem_thu, ra, ti_le_val=0.12, khoi_lien_tiep=40,
             min_mau=30, toi_da_moi_lop=3000, seed=0, log=print):
    """
    - nguon_kiem_thu: list ten nguon dung lam tap KIEM THU DOC LAP (vd ['charlesmld']).
    - Cac nguon con lai chia train/val theo KHOI anh lien tiep (giam ro ri khung hinh video lien ke).
    Ket qua:
      ra/phat_hien/{images,labels}/{train,val,test} + data.yaml   (YOLO 1 lop)
      ra/phan_loai/{train,val,test}/<ma>/*.png                       (anh cat 64x64)
      ra/thong_ke.json, ra/loai_bo.csv
    """
    rnd = random.Random(seed)
    if os.path.isdir(ra):
        shutil.rmtree(ra)
    loai_bo = []  # (duong, ly_do)

    # 1) hash + bo trung lap tuyet doi trong tap huan luyen
    muc = []  # (nguon, duong, hop, hash)
    for ng in ds_nguon:
        for p, hop in ng['anh']:
            h = dhash(p)
            if h is None:
                loai_bo.append((p, 'khong_doc_duoc_anh')); continue
            muc.append((ng['nguon'], p, hop, h))
    kt = [m for m in muc if m[0] in nguon_kiem_thu]
    hl_all = [m for m in muc if m[0] not in nguon_kiem_thu]
    da_thay, hl = set(), []
    for m in hl_all:
        if int(m[3]) in da_thay:
            loai_bo.append((m[1], 'trung_lap_trong_tap_huan_luyen')); continue
        da_thay.add(int(m[3])); hl.append(m)

    # 2) bo anh kiem thu gan trung voi anh huan luyen (dam bao doc lap)
    if kt and hl:
        tr = gan_trung([m[3] for m in kt], [m[3] for m in hl])
        for m, t in zip(kt, tr):
            if t:
                loai_bo.append((m[1], 'kiem_thu_gan_trung_anh_huan_luyen'))
        kt = [m for m, t in zip(kt, tr) if not t]

    # 3) chia train/val theo khoi lien tiep trong tung nguon
    tach = {}
    theo_nguon = defaultdict(list)
    for m in hl:
        theo_nguon[m[0]].append(m)
    for ng, ds in theo_nguon.items():
        # nhom anh cung goc: Roboflow dat ten anh tang cuong la <goc>.rf.<ma>.jpg
        nhom = defaultdict(list)
        for m in ds:
            nhom[os.path.basename(m[1]).split('.rf.')[0]].append(m)
        khoi, cur = [], []
        for k in sorted(nhom):
            cur += nhom[k]
            if len(cur) >= khoi_lien_tiep:
                khoi.append(cur); cur = []
        if cur:
            khoi.append(cur)
        rnd.shuffle(khoi)
        n_val = int(round(len(khoi) * ti_le_val)) if len(khoi) >= 8 else (1 if len(khoi) >= 3 else 0)
        for j, k in enumerate(khoi):
            for m in k:
                tach[m[1]] = 'val' if j < n_val else 'train'
    for m in kt:
        tach[m[1]] = 'test'
    tat_ca = hl + kt

    # 4) bo du lieu phat hien (1 lop)
    for s in ('train', 'val', 'test'):
        os.makedirs(f"{ra}/phat_hien/images/{s}", exist_ok=True)
        os.makedirs(f"{ra}/phat_hien/labels/{s}", exist_ok=True)
    tk_det = Counter()
    for i, (ng, p, hop, _) in enumerate(tat_ca):
        s = tach[p]
        dong = []
        for (c, cx, cy, w, h) in hop:
            ma = bang.get((ng, str(c)), '')
            if ma == 'BO':
                continue
            dong.append(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        ten = f"{ng}_{i:06d}"
        dich = f"{ra}/phat_hien/images/{s}/{ten}{os.path.splitext(p)[1].lower()}"
        try:
            os.link(p, dich)
        except OSError:
            shutil.copy2(p, dich)
        open(f"{ra}/phat_hien/labels/{s}/{ten}.txt", 'w').write('\n'.join(dong))
        tk_det[s] += 1
    with open(f"{ra}/phat_hien/data.yaml", 'w') as f:
        yaml.safe_dump({"path": os.path.abspath(f"{ra}/phat_hien"), "train": "images/train",
                        "val": "images/val", "test": "images/test", "names": {0: "bien_bao"}}, f)

    # 5) bo du lieu phan loai (anh cat)
    cat = defaultdict(list)   # (split, ma) -> list anh
    nen = defaultdict(list)
    for i, (ng, p, hop, _) in enumerate(tat_ca):
        s = tach[p]
        img = cv2.imread(p)
        if img is None:
            continue
        H, W = img.shape[:2]
        hop_px = []
        for j, (c, cx, cy, w, h) in enumerate(hop):
            hop_px.append(((cx - w / 2) * W, (cy - h / 2) * H, (cx + w / 2) * W, (cy + h / 2) * H))
            ma = bang.get((ng, str(c)), '')
            if not ma or ma in ('BO', 'KHAC'):
                continue
            cr = cat_bien(img, (cx, cy, w, h))
            if cr is None:
                continue
            cat[(s, ma)].append((f"{ng}_{i:06d}_{j}", cv2.resize(cr, (CO_ANH_PL, CO_ANH_PL), interpolation=cv2.INTER_AREA)))
        # 1 manh nen ngau nhien / anh (khong chong len bien nao) -> lop KHONG_PHAI_BIEN
        if hop_px and rnd.random() < 0.5:
            ws = [b[2] - b[0] for b in hop_px]
            for _ in range(10):
                kc = int(np.clip(rnd.choice(ws) * rnd.uniform(0.8, 2.0), 20, min(H, W) - 1))
                x, y = rnd.randint(0, W - kc), rnd.randint(0, H - kc)
                if all(_iou((x, y, x + kc, y + kc), b) < 0.02 for b in hop_px):
                    nen[s].append((f"{ng}_{i:06d}_nen", cv2.resize(img[y:y + kc, x:x + kc], (CO_ANH_PL, CO_ANH_PL), interpolation=cv2.INTER_AREA)))
                    break

    dem_train = Counter({ma: len(v) for (s, ma), v in cat.items() if s == 'train'})
    lop_giu = sorted([ma for ma, n in dem_train.items() if n >= min_mau])
    so_nen = int(np.median([min(dem_train[m], toi_da_moi_lop) for m in lop_giu])) if lop_giu else 0
    tk_pl = defaultdict(dict)
    for (s, ma), ds in cat.items():
        if ma not in lop_giu:
            # bien NGOAI danh sach: tu nguon kiem thu -> do kha nang tu choi (bao cao);
            # tu nguon huan luyen -> dung de CHON NGUONG (khong cham vao tap test)
            _ghi(f"{ra}/phan_loai/{'ngoai_danh_sach' if s == 'test' else 'ngoai_danh_sach_val'}/{ma}", ds)
            continue
        if s == 'train' and len(ds) > toi_da_moi_lop:
            rnd.shuffle(ds); ds = ds[:toi_da_moi_lop]
        _ghi(f"{ra}/phan_loai/{s}/{ma}", ds); tk_pl[s][ma] = len(ds)
    for s, ds in nen.items():
        rnd.shuffle(ds)
        k = so_nen if s == 'train' else int(so_nen * len(ds) / max(1, len(nen.get('train', []))))
        ds = ds[:max(k, 1)]
        _ghi(f"{ra}/phan_loai/{s}/{LOP_NEN}", ds); tk_pl[s][LOP_NEN] = len(ds)

    with open(f"{ra}/loai_bo.csv", 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['duong_anh', 'ly_do']); w.writerows(loai_bo)
    tk = {"so_anh_phat_hien": dict(tk_det), "so_anh_cat_phan_loai": {s: dict(sorted(v.items())) for s, v in tk_pl.items()},
          "so_lop_phan_loai": len(lop_giu) + 1, "lop_bi_bo_vi_it_mau(<%d)" % min_mau: sorted(set(dem_train) - set(lop_giu)),
          "ly_do_loai_bo": dict(Counter(r[1] for r in loai_bo)), "nguon_kiem_thu": list(nguon_kiem_thu)}
    json.dump(tk, open(f"{ra}/thong_ke.json", 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    log(json.dumps({k: v for k, v in tk.items() if k != "so_anh_cat_phan_loai"}, ensure_ascii=False, indent=2))
    return tk


def _ghi(d, ds):
    os.makedirs(d, exist_ok=True)
    for ten, im in ds:
        cv2.imwrite(os.path.join(d, ten + '.png'), im)


def _iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u > 0 else 0.0


# ---------------------------------------------------------------- anh tu chup
def nap_anh_tu_chup(goc):
    """Anh tu chup: goc/<ma>/*.jpg (1 bien chinh/anh, khong can khoanh hop) -> dung cho danh gia DAU-CUOI."""
    ds = []
    for d in sorted(glob.glob(os.path.join(goc, '*'))):
        if os.path.isdir(d):
            for p in sorted(glob.glob(os.path.join(d, '*'))):
                if p.lower().endswith(DUOI_ANH):
                    ds.append((p, os.path.basename(d).strip()))
    return ds
