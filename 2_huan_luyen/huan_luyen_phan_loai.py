# -*- coding: utf-8 -*-
"""
huan_luyen_phan_loai.py - Huan luyen mang no-ron tich chap (CNN) phan loai bien bao
bang thuat toan LAN TRUYEN NGUOC (Back Propagation) + toi uu AdamW.

Dau vao : <du_lieu>/phan_loai/{train,val,test}/<ma_bien>/*.png  (anh mau 64x64)
Dau ra  : <ra>/phan_loai.pt, phan_loai.onnx, lop.json, nguong.json,
          lich_su.csv, bieu_do_huan_luyen.png, bao_cao_<tap>.csv, ma_tran_nham_lan_<tap>.png,
          do_tin_cay.png, kiem_tra_gradient.txt, anh_sai_<tap>.png, tom_tat.json
"""
import os, json, csv, math, time, random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms
from sklearn.metrics import classification_report, confusion_matrix, f1_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CO_ANH = 64
LOP_NEN = "KHONG_PHAI_BIEN"


# ------------------------------------------------------------------ mo hinh
class MangCNN(nn.Module):
    """3 khoi [Conv3x3-BN-ReLU-Conv3x3-BN-ReLU-MaxPool] + 2 lop day du (FC). Anh mau 64x64x3."""
    def __init__(self, so_lop):
        super().__init__()
        def khoi(vao, ra):
            return nn.Sequential(
                nn.Conv2d(vao, ra, 3, padding=1, bias=False), nn.BatchNorm2d(ra), nn.ReLU(inplace=True),
                nn.Conv2d(ra, ra, 3, padding=1, bias=False), nn.BatchNorm2d(ra), nn.ReLU(inplace=True),
                nn.MaxPool2d(2))
        self.dac_trung = nn.Sequential(khoi(3, 32), khoi(32, 64), khoi(64, 128))   # 64 -> 8
        self.phan_loai = nn.Sequential(
            nn.Flatten(), nn.Dropout(0.4), nn.Linear(128 * 8 * 8, 256), nn.ReLU(inplace=True),
            nn.Dropout(0.4), nn.Linear(256, so_lop))

    def forward(self, x):
        return self.phan_loai(self.dac_trung(x))


def bang_tham_so(model):
    dong, tong = [], 0
    for ten, p in model.named_parameters():
        dong.append((ten, tuple(p.shape), p.numel())); tong += p.numel()
    return dong, tong


# ------------------------------------------------------------------ du lieu
def bien_doi(train):
    chuan = [transforms.ToTensor(), transforms.Normalize([0.5] * 3, [0.5] * 3)]
    if not train:
        return transforms.Compose([transforms.Resize((CO_ANH, CO_ANH))] + chuan)
    # KHONG lat ngang: lat se doi nghia bien (cam re trai <-> cam re phai)
    return transforms.Compose([
        transforms.Resize((CO_ANH, CO_ANH)),
        transforms.RandomAffine(degrees=10, translate=(0.08, 0.08), scale=(0.85, 1.15), shear=5),
        transforms.ColorJitter(0.4, 0.4, 0.3, 0.02),
        transforms.RandomApply([transforms.GaussianBlur(3, (0.1, 1.2))], p=0.25),
    ] + chuan + [transforms.RandomErasing(p=0.15, scale=(0.02, 0.1))])


def nap_tap(goc, lop, train=False):
    """Nap ImageFolder nhung ep thu tu lop theo danh sach `lop` cua tap train; bo lop la."""
    ds = datasets.ImageFolder(goc, transform=bien_doi(train))
    anh_xa = {i: lop.index(c) for c, i in ds.class_to_idx.items() if c in lop}
    ds.samples = [(p, anh_xa[y]) for p, y in ds.samples if y in anh_xa]
    ds.targets = [y for _, y in ds.samples]
    ds.classes, ds.class_to_idx = lop, {c: i for i, c in enumerate(lop)}
    return ds


# ------------------------------------------------------------------ kiem tra lan truyen nguoc
def kiem_tra_gradient(so_lop, so_diem=12, eps=1e-6, seed=0):
    """So sanh gradient tinh bang lan truyen nguoc (autograd) voi dao ham so (sai phan trung tam)."""
    torch.manual_seed(seed)
    m = MangCNN(so_lop).double().eval()          # eval: tat dropout, BN dung thong ke co dinh
    x = torch.randn(4, 3, CO_ANH, CO_ANH, dtype=torch.double)
    y = torch.randint(0, so_lop, (4,))
    m.zero_grad(); F.cross_entropy(m(x), y).backward()
    kq = []
    with torch.no_grad():
        for ten, p in m.named_parameters():
            if p.grad is None or p.numel() == 0:
                continue
            # chon cac phan tu co |gradient| lon de sai so tuong doi co y nghia
            ung_vien = torch.randint(0, p.numel(), (min(200, p.numel()),))
            chon = ung_vien[p.grad.view(-1)[ung_vien].abs().argsort(descending=True)[:max(1, so_diem // 6)]]
            for i in chon.tolist():
                goc = p.view(-1)[i].item()
                p.view(-1)[i] = goc + eps; lp = F.cross_entropy(m(x), y).item()
                p.view(-1)[i] = goc - eps; lm = F.cross_entropy(m(x), y).item()
                p.view(-1)[i] = goc
                so = (lp - lm) / (2 * eps); bp = p.grad.view(-1)[i].item()
                sai = abs(so - bp) / max(1e-12, abs(so) + abs(bp))
                kq.append((ten, i, bp, so, sai))
    return kq


# ------------------------------------------------------------------ hieu chuan (temperature scaling)
def tim_nhiet_do(logits, nhan):
    """Tim T > 0 lam cuc tieu NLL tren tap val (Guo et al., 2017)."""
    logT = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([logT], lr=0.1, max_iter=100)
    def dong():
        opt.zero_grad(); l = F.cross_entropy(logits / logT.exp(), nhan); l.backward(); return l
    opt.step(dong)
    return float(logT.exp())


def ece(xs, dung, so_ngan=15):
    """Expected Calibration Error."""
    bien = np.linspace(0, 1, so_ngan + 1); e = 0.0
    for a, b in zip(bien[:-1], bien[1:]):
        m = (xs > a) & (xs <= b)
        if m.any():
            e += m.mean() * abs(dung[m].mean() - xs[m].mean())
    return float(e)


# ------------------------------------------------------------------ du doan
@torch.no_grad()
def du_doan(model, loader, thiet_bi):
    model.eval(); L, Y = [], []
    for x, y in loader:
        L.append(model(x.to(thiet_bi)).float().cpu()); Y.append(y)
    return torch.cat(L), torch.cat(Y)


def ve_ma_tran(cm, lop, duong, tieu_de):
    n = len(lop); kt = max(8, n * 0.28)
    cmn = cm / np.maximum(cm.sum(1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(kt, kt))
    ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(lop, rotation=90, fontsize=7); ax.set_yticklabels(lop, fontsize=7)
    ax.set_xlabel("Du doan"); ax.set_ylabel("Nhan dung"); ax.set_title(tieu_de)
    if n <= 30:
        for i in range(n):
            for j in range(n):
                if cm[i, j]:
                    ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=6,
                            color="white" if cmn[i, j] > 0.5 else "black")
    fig.tight_layout(); fig.savefig(duong, dpi=130); plt.close(fig)


def luoi_anh_sai(ds, chi_so, du, lop, duong, toi_da=48):
    chi_so = list(chi_so)[:toi_da]
    if not chi_so:
        return
    c = 8; r = math.ceil(len(chi_so) / c)
    fig, axs = plt.subplots(r, c, figsize=(c * 1.6, r * 1.9))
    axs = np.array(axs).reshape(-1)
    for a in axs:
        a.axis("off")
    for a, i in zip(axs, chi_so):
        p, y = ds.samples[i]
        a.imshow(plt.imread(p)); a.set_title(f"{lop[y]}\n->{lop[du[i]]}", fontsize=6, color="red")
    fig.tight_layout(); fig.savefig(duong, dpi=120); plt.close(fig)


def danh_gia(model, ds, ten, ra, lop, T, nguong, thiet_bi, bs=256):
    if len(ds) == 0:
        return None
    L, Y = du_doan(model, DataLoader(ds, bs, num_workers=2), thiet_bi)
    P = F.softmax(L / T, 1); conf, du = P.max(1)
    y, du, conf = Y.numpy(), du.numpy(), conf.numpy()
    nhan_co = sorted(set(y) | set(du))
    bc = classification_report(y, du, labels=nhan_co, target_names=[lop[i] for i in nhan_co],
                               output_dict=True, zero_division=0)
    with open(f"{ra}/bao_cao_{ten}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["lop", "precision", "recall", "f1", "so_mau"])
        for k, v in bc.items():
            if isinstance(v, dict):
                w.writerow([k, f"{v['precision']:.4f}", f"{v['recall']:.4f}", f"{v['f1-score']:.4f}", int(v['support'])])
    cm = confusion_matrix(y, du, labels=list(range(len(lop))))
    ve_ma_tran(cm, lop, f"{ra}/ma_tran_nham_lan_{ten}.png", f"Ma tran nham lan - tap {ten} (n={len(y)})")
    sai = np.where(du != y)[0]
    luoi_anh_sai(ds, sai, du, lop, f"{ra}/anh_sai_{ten}.png")
    # cap nham lan nhieu nhat
    cap = sorted([(int(cm[i, j]), lop[i], lop[j]) for i in range(len(lop)) for j in range(len(lop)) if i != j and cm[i, j]], reverse=True)[:15]
    nhan = conf >= nguong
    kq = {"tap": ten, "so_mau": int(len(y)), "so_dung": int((du == y).sum()),
          "accuracy": float((du == y).mean()),
          "macro_f1": float(f1_score(y, du, labels=np.unique(y), average="macro", zero_division=0)),
          "so_lop_co_trong_tap": int(len(np.unique(y))),
          "recall_tung_lop": {lop[i]: round(float(cm[i, i] / cm[i].sum()), 4) for i in np.unique(y)},
          "ty_le_chap_nhan_o_nguong": float(nhan.mean()),
          "accuracy_tren_mau_chap_nhan": float((du[nhan] == y[nhan]).mean()) if nhan.any() else None,
          "ece": ece(conf, (du == y).astype(float)), "cap_nham_lan_nhieu_nhat": cap,
          "lop_f1_duoi_0.9": sorted([(k, round(v["f1-score"], 3), int(v["support"])) for k, v in bc.items()
                                     if isinstance(v, dict) and k in lop and v["support"] > 0 and v["f1-score"] < 0.9],
                                    key=lambda t: t[1])}
    return kq


def danh_gia_tu_choi(model, goc, lop, T, nguong, thiet_bi):
    """Anh bien NGOAI danh sach lop: ly tuong la do tin cay < nguong (bi tu choi)."""
    if not os.path.isdir(goc):
        return None
    ds = datasets.ImageFolder(goc, transform=bien_doi(False))
    if len(ds) == 0:
        return None
    L, _ = du_doan(model, DataLoader(ds, 256), thiet_bi)
    conf = F.softmax(L / T, 1).max(1).values.numpy()
    return {"so_mau_ngoai_danh_sach": int(len(conf)), "ty_le_bi_tu_choi": float((conf < nguong).mean()),
            "do_tin_cay": conf}


# ------------------------------------------------------------------ chuong trinh chinh
def huan_luyen(du_lieu, ra, so_epoch_toi_da=80, kien_nhan=10, bs=128, lr=1e-3, seed=0,
               ty_le_chap_nhan_toi_thieu=0.95, log=print):
    os.makedirs(ra, exist_ok=True)
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    thiet_bi = "cuda" if torch.cuda.is_available() else "cpu"
    goc = f"{du_lieu}/phan_loai"
    lop = sorted(os.listdir(f"{goc}/train"))
    tr, va = nap_tap(f"{goc}/train", lop, True), nap_tap(f"{goc}/val", lop)
    te = nap_tap(f"{goc}/test", lop) if os.path.isdir(f"{goc}/test") else None
    log(f"Thiet bi: {thiet_bi} | so lop: {len(lop)} | train {len(tr)} | val {len(va)} | test {len(te) if te else 0}")

    # 1) kiem tra lan truyen nguoc truoc khi huan luyen
    kq_g = kiem_tra_gradient(len(lop))
    with open(f"{ra}/kiem_tra_gradient.txt", "w", encoding="utf-8") as f:
        f.write("tham_so\tchi_so\tgrad_lan_truyen_nguoc\tgrad_so\tsai_so_tuong_doi\n")
        for t in kq_g:
            f.write(f"{t[0]}\t{t[1]}\t{t[2]:.6e}\t{t[3]:.6e}\t{t[4]:.2e}\n")
    ss = np.array([t[4] for t in kq_g]); dat = int((ss < 1e-4).sum())
    with open(f"{ra}/kiem_tra_gradient.txt", "a", encoding="utf-8") as f:
        f.write(f"\n# {dat}/{len(ss)} diem co sai so tuong doi < 1e-4; trung vi = {np.median(ss):.2e}. "
                "Diem lech (neu co) do ham ReLU/MaxPool khong kha vi tai diem gay.\n")
    log(f"Kiem tra gradient: {dat}/{len(ss)} diem dat (<1e-4), trung vi sai so {np.median(ss):.2e}")

    # 2) can bang lop: lay mau theo trong so 1/sqrt(so_mau)
    dem = np.bincount(tr.targets, minlength=len(lop))
    w = 1.0 / np.sqrt(np.maximum(dem, 1))
    sampler = WeightedRandomSampler(w[tr.targets], num_samples=len(tr), replacement=True)
    dl_tr = DataLoader(tr, bs, sampler=sampler, num_workers=2, drop_last=True)
    dl_va = DataLoader(va, 256, num_workers=2)

    model = MangCNN(len(lop)).to(thiet_bi)
    ts, tong = bang_tham_so(model)
    with open(f"{ra}/so_tham_so.txt", "w", encoding="utf-8") as f:
        for t in ts:
            f.write(f"{t[0]}\t{t[1]}\t{t[2]}\n")
        f.write(f"TONG\t\t{tong}\n")
    log(f"Tong so tham so: {tong:,}")

    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sch = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="max", factor=0.5, patience=3)
    tot_nhat, epoch_tot, cho = -1.0, 0, 0
    ls = []
    t0 = time.time()
    for ep in range(1, so_epoch_toi_da + 1):
        model.train(); tl, td, tn = 0.0, 0, 0
        for x, y in dl_tr:
            x, y = x.to(thiet_bi), y.to(thiet_bi)
            out = model(x)                      # lan truyen xuoi
            loss = F.cross_entropy(out, y)      # ham mat mat
            opt.zero_grad(); loss.backward()    # lan truyen nguoc: tinh dL/dw cho moi trong so
            opt.step()                          # cap nhat trong so
            tl += loss.item() * len(y); td += (out.argmax(1) == y).sum().item(); tn += len(y)
        Lv, Yv = du_doan(model, dl_va, thiet_bi)
        vl = F.cross_entropy(Lv, Yv).item(); dv = Lv.argmax(1)
        va_acc = (dv == Yv).float().mean().item()
        va_f1 = f1_score(Yv.numpy(), dv.numpy(), labels=np.unique(Yv.numpy()), average="macro", zero_division=0)
        sch.step(va_f1)
        ls.append([ep, tl / tn, td / tn, vl, va_acc, va_f1, opt.param_groups[0]["lr"]])
        log(f"epoch {ep:3d} | loss {tl/tn:.4f} acc {td/tn:.4f} | val loss {vl:.4f} acc {va_acc:.4f} macroF1 {va_f1:.4f} | {time.time()-t0:.0f}s")
        if va_f1 > tot_nhat + 1e-4:
            tot_nhat, epoch_tot, cho = va_f1, ep, 0
            torch.save({"model": model.state_dict(), "lop": lop, "epoch": ep}, f"{ra}/phan_loai.pt")
        else:
            cho += 1
            if cho >= kien_nhan:   # DUNG SOM THUC SU: dung khi val macro-F1 khong tang sau `kien_nhan` epoch
                log(f"Dung som tai epoch {ep}; tot nhat o epoch {epoch_tot} (val macro-F1 {tot_nhat:.4f})")
                break

    with open(f"{ra}/lich_su.csv", "w", newline="") as f:
        c = csv.writer(f); c.writerow(["epoch", "loss", "acc", "val_loss", "val_acc", "val_macro_f1", "lr"]); c.writerows(ls)
    a = np.array(ls)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(a[:, 0], a[:, 1], label="train"); ax[0].plot(a[:, 0], a[:, 3], label="val"); ax[0].set_title("Ham mat mat"); ax[0].legend()
    ax[1].plot(a[:, 0], a[:, 2], label="train acc"); ax[1].plot(a[:, 0], a[:, 4], label="val acc"); ax[1].plot(a[:, 0], a[:, 5], label="val macro-F1")
    ax[1].axvline(epoch_tot, ls="--", c="gray"); ax[1].set_title("Do chinh xac"); ax[1].legend()
    for x in ax:
        x.set_xlabel("epoch")
    fig.tight_layout(); fig.savefig(f"{ra}/bieu_do_huan_luyen.png", dpi=130); plt.close(fig)

    # 3) nap trong so tot nhat, hieu chuan va chon nguong tren VAL (khong dung test)
    model.load_state_dict(torch.load(f"{ra}/phan_loai.pt", map_location=thiet_bi)["model"])
    Lv, Yv = du_doan(model, dl_va, thiet_bi)
    dung_goc = (Lv.argmax(1) == Yv).numpy().astype(float)
    ece_truoc = ece(F.softmax(Lv, 1).max(1).values.numpy(), dung_goc)
    T = tim_nhiet_do(Lv, Yv)
    ece_sau = ece(F.softmax(Lv / T, 1).max(1).values.numpy(), dung_goc)
    if ece_sau >= ece_truoc:      # hieu chuan khong cai thien ECE -> khong dung
        T = 1.0
    Pv = F.softmax(Lv / T, 1); cv, dv = Pv.max(1)
    dung_v = (dv == Yv).numpy(); cv = cv.numpy()
    tc_val = danh_gia_tu_choi(model, f"{goc}/ngoai_danh_sach_val", lop, T, 0.5, thiet_bi)  # bien la tu nguon huan luyen
    tc = danh_gia_tu_choi(model, f"{goc}/ngoai_danh_sach", lop, T, 0.5, thiet_bi)          # bien la tu nguon kiem thu (chi bao cao)
    # NGUONG = gia tri LON NHAT ma van chap nhan >= ty_le_chap_nhan_toi_thieu bien trong danh sach (tren val):
    # tu choi duoc nhieu bien la nhat ma khong tu choi qua nhieu bien quen.
    nguong = 0.30
    for t in np.round(np.arange(0.30, 0.995, 0.01), 2):
        if (cv >= t).mean() >= ty_le_chap_nhan_toi_thieu:
            nguong = float(t)
    with open(f"{ra}/bang_nguong.csv", "w", newline="") as f:   # can cu de chon nguong
        c = csv.writer(f)
        c.writerow(["nguong", "ty_le_chap_nhan_val", "do_chinh_xac_khi_chap_nhan_val",
                    "ty_le_tu_choi_bien_la_val", "ty_le_tu_choi_bien_la_test"])
        for t in sorted(set(np.round(np.arange(0.30, 1.0, 0.05), 2).tolist() + [nguong])):
            m = cv >= t
            c.writerow([t, f"{m.mean():.4f}", f"{dung_v[m].mean():.4f}" if m.any() else "",
                        f"{(tc_val['do_tin_cay'] < t).mean():.4f}" if tc_val else "",
                        f"{(tc['do_tin_cay'] < t).mean():.4f}" if tc else ""])
    for x in (tc_val, tc):
        if x:
            x["ty_le_bi_tu_choi"] = float((x["do_tin_cay"] < nguong).mean())
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(cv[dung_v], bins=40, alpha=.6, label="val - du doan dung", density=True)
    if (~dung_v).any():
        ax.hist(cv[~dung_v], bins=40, alpha=.6, label="val - du doan sai", density=True)
    if tc_val:
        ax.hist(tc_val["do_tin_cay"], bins=40, alpha=.5, label="bien la (nguon huan luyen)", density=True)
    ax.axvline(nguong, c="k", ls="--", label=f"nguong = {nguong:.2f}")
    ax.set_xlabel("Do tin cay (softmax)"); ax.legend(); fig.tight_layout()
    fig.savefig(f"{ra}/do_tin_cay.png", dpi=130); plt.close(fig)

    tom_tat = {"so_lop": len(lop), "tong_tham_so": tong, "epoch_tot_nhat": epoch_tot, "so_epoch_da_chay": len(ls),
               "nhiet_do_T": T, "ece_val_truoc_hieu_chuan": ece_truoc, "ece_val_sau_hieu_chuan": ece_sau,
               "dung_hieu_chuan": T != 1.0, "nguong": nguong,
               "quy_tac_chon_nguong": f"nguong lon nhat sao cho >= {ty_le_chap_nhan_toi_thieu:.0%} mau val duoc chap nhan"}
    for ten, ds in (("val", va), ("test", te)):
        if ds is not None:
            tom_tat[ten] = danh_gia(model, ds, ten, ra, lop, T, nguong, thiet_bi)
    if tc_val:
        tom_tat["tu_choi_bien_la_val"] = {k: v for k, v in tc_val.items() if k != "do_tin_cay"}
    if tc:
        tom_tat["tu_choi_bien_ngoai_danh_sach"] = {k: v for k, v in tc.items() if k != "do_tin_cay"}
    json.dump(lop, open(f"{ra}/lop.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"nguong": nguong, "nhiet_do_T": T, "co_anh": CO_ANH, "pad": 0.15, "lop_nen": LOP_NEN,
               "chuan_hoa": "rgb/255, (x-0.5)/0.5"}, open(f"{ra}/nguong.json", "w"), indent=2)
    json.dump(tom_tat, open(f"{ra}/tom_tat.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 4) xuat ONNX de ung dung chay khong can PyTorch
    model.eval().cpu()
    x = torch.randn(1, 3, CO_ANH, CO_ANH)
    kw = dict(input_names=["anh"], output_names=["logits"], dynamic_axes={"anh": {0: "n"}, "logits": {0: "n"}}, opset_version=17)
    try:
        torch.onnx.export(model, x, f"{ra}/phan_loai.onnx", dynamo=False, **kw)
    except TypeError:
        torch.onnx.export(model, x, f"{ra}/phan_loai.onnx", **kw)
    log(json.dumps({k: v for k, v in tom_tat.items() if k not in ("val",)}, ensure_ascii=False, indent=1, default=str)[:3000])
    return tom_tat


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--du_lieu", required=True); ap.add_argument("--ra", required=True)
    ap.add_argument("--epoch", type=int, default=80); ap.add_argument("--kien_nhan", type=int, default=10)
    a = ap.parse_args()
    huan_luyen(a.du_lieu, a.ra, a.epoch, a.kien_nhan)
