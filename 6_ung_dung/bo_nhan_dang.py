# -*- coding: utf-8 -*-
"""
bo_nhan_dang.py - Bo nhan dang 2 tang dung cho ung dung:
  tang 1: YOLO (phat_hien.onnx) tim vi tri bien bao
  tang 2: CNN tu huan luyen (phan_loai.onnx) xac dinh ma bien, tra ve 3 goi y
Tien xu ly GIONG HET luc huan luyen (le 15%, anh 64x64, RGB, (x/255-0.5)/0.5).
"""
import os, json
import numpy as np
import cv2
import onnxruntime as ort


class BoNhanDang:
    def __init__(self, thu_muc_mo_hinh, nguong_phat_hien=0.25, toi_da_bien=20):
        tm = thu_muc_mo_hinh
        nhacc = [p for p in ("CUDAExecutionProvider", "CPUExecutionProvider") if p in ort.get_available_providers()]
        self.det = ort.InferenceSession(os.path.join(tm, "phat_hien.onnx"), providers=nhacc)
        self.cls = ort.InferenceSession(os.path.join(tm, "phan_loai.onnx"), providers=nhacc)
        self.lop = json.load(open(os.path.join(tm, "lop.json"), encoding="utf-8"))
        cfg = json.load(open(os.path.join(tm, "nguong.json"), encoding="utf-8"))
        self.nguong, self.T = float(cfg["nguong"]), float(cfg["nhiet_do_T"])
        self.co, self.pad = int(cfg["co_anh"]), float(cfg["pad"])
        self.lop_nen = cfg.get("lop_nen", "KHONG_PHAI_BIEN")
        p = os.path.join(tm, "y_nghia.json")
        self.y_nghia = json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}
        ip = self.det.get_inputs()[0]
        self.det_in = ip.name
        self.det_sz = ip.shape[2] if isinstance(ip.shape[2], int) else 640
        self.cls_in = self.cls.get_inputs()[0].name
        self.nguong_det, self.toi_da = nguong_phat_hien, toi_da_bien
        self.i_nen = self.lop.index(self.lop_nen) if self.lop_nen in self.lop else -1

    def ten(self, ma):
        v = self.y_nghia.get(ma)
        return v.get("ten", ma) if isinstance(v, dict) else ma

    # ---------- tang 1: phat hien
    def phat_hien(self, img):
        H, W = img.shape[:2]; s = self.det_sz
        r = min(s / H, s / W); nh, nw = int(round(H * r)), int(round(W * r))
        py, px = (s - nh) // 2, (s - nw) // 2
        nen = np.full((s, s, 3), 114, np.uint8)
        nen[py:py + nh, px:px + nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        x = cv2.cvtColor(nen, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        out = self.det.run(None, {self.det_in: x})[0][0].T          # (N, 5): cx, cy, w, h, diem
        m = out[:, 4] >= self.nguong_det
        if not m.any():
            return []
        b, diem = out[m, :4], out[m, 4]
        x1 = (b[:, 0] - b[:, 2] / 2 - px) / r; y1 = (b[:, 1] - b[:, 3] / 2 - py) / r
        w, h = b[:, 2] / r, b[:, 3] / r
        idx = cv2.dnn.NMSBoxes(np.stack([x1, y1, w, h], 1).tolist(), diem.tolist(), self.nguong_det, 0.5)
        kq = []
        for i in np.array(idx).reshape(-1)[:self.toi_da]:
            a, c = max(0.0, x1[i]), max(0.0, y1[i])
            bb, d = min(W, x1[i] + w[i]), min(H, y1[i] + h[i])
            if bb - a > 2 and d - c > 2:
                kq.append((float(a), float(c), float(bb), float(d), float(diem[i])))
        return kq

    # ---------- tang 2: phan loai, tra ve xac suat day du
    def phan_loai(self, img, hop):
        H, W = img.shape[:2]; anh = []
        for (x1, y1, x2, y2, _) in hop:
            px, py = (x2 - x1) * self.pad, (y2 - y1) * self.pad
            a, b = int(max(0, x1 - px)), int(max(0, y1 - py))
            c, d = int(min(W, x2 + px)), int(min(H, y2 + py))
            cr = cv2.resize(img[b:d, a:c], (self.co, self.co), interpolation=cv2.INTER_AREA)
            anh.append(cv2.cvtColor(cr, cv2.COLOR_BGR2RGB))
        if not anh:
            return np.zeros((0, len(self.lop)), np.float32)
        x = ((np.stack(anh).astype(np.float32) / 255.0 - 0.5) / 0.5).transpose(0, 3, 1, 2)
        z = self.cls.run(None, {self.cls_in: x})[0] / self.T
        e = np.exp(z - z.max(1, keepdims=True))
        return e / e.sum(1, keepdims=True)

    def xu_ly(self, img, so_goi_y=3):
        hop = self.phat_hien(img)
        P = self.phan_loai(img, hop)
        kq = []
        for h, p in zip(hop, P):
            if int(p.argmax()) == self.i_nen:
                continue                                    # phat hien nham: khong phai bien
            thu_tu = [int(i) for i in np.argsort(-p) if int(i) != self.i_nen][:so_goi_y]
            goi_y = [{"ma": self.lop[i], "ten": self.ten(self.lop[i]), "p": round(float(p[i]), 4)} for i in thu_tu]
            kq.append({"hop": [round(v, 1) for v in h[:4]], "diem_phat_hien": round(h[4], 4),
                       "ma": goi_y[0]["ma"], "ten": goi_y[0]["ten"], "do_tin_cay": goi_y[0]["p"],
                       "chac_chan": goi_y[0]["p"] >= self.nguong, "goi_y": goi_y})
        kq.sort(key=lambda r: -r["diem_phat_hien"] * r["do_tin_cay"])
        return kq
