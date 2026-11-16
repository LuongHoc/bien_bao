
"use strict";

// Thong tin tai khoan Google hien tai
window.TAI_KHOAN_GOOGLE = null;

let csrfToken = null;

// Đọc lại session trước khi lưu bài, kể cả khi thông tin menu còn đang tải.
window.layPhienGoogle = async function () {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
        const response = await fetch("/api/me", {
            credentials: "same-origin",
            cache: "no-store",
            signal: controller.signal
        });
        if (!response.ok) throw new Error("Không thể kiểm tra đăng nhập.");
        return await response.json();
    } finally {
        clearTimeout(timeout);
    }
};

// Cap nhat thanh menu ben trai
function hienThiTaiKhoanMenu() {
    const user = window.TAI_KHOAN_GOOGLE;
    const avatar = document.getElementById("avatar-menu");
    const controls = document.getElementById("auth-controls");

    if (!avatar || !controls) return;

    controls.replaceChildren();

    if (user) {
        // Anh dai dien Google thay cho icon mac dinh
        if (user.anh_dai_dien) {
            const img = document.createElement("img");
            img.src = user.anh_dai_dien;
            img.alt = "Ảnh đại diện Google";
            img.referrerPolicy = "no-referrer";

            avatar.replaceChildren(img);
        }

        // Khi dang nhap, menu khong can them nut
        // dang xuat rieng
    } else {
        // Chua dang nhap
        const link = document.createElement("a");
        link.href = "/login";
        link.className = "auth-login-small";
        link.textContent = "Đăng nhập";

        controls.appendChild(link);
    }
}

// Dang xuat
window.dangXuatGoogle = async function () {
    try {
        const response = await fetch("/auth/logout", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "X-CSRF-Token": csrfToken || ""
            }
        });

        if (!response.ok) {
            throw new Error("Đăng xuất thất bại");
        }

        csrfToken = null;
        window.TAI_KHOAN_GOOGLE = null;

        window.location.reload();

    } catch (error) {
        console.error(error);
        alert("Không thể đăng xuất. Vui lòng thử lại.");
    }
};

// Tai thong tin dang nhap
async function taiTaiKhoanGoogle() {
    try {
        const data = await window.layPhienGoogle();

        window.TAI_KHOAN_GOOGLE =
            data.da_dang_nhap ? data.user : null;

        csrfToken = data.csrf_token || null;

        hienThiTaiKhoanMenu();

        // Dong bo ten voi app.js
        if (typeof capNhatTenNho === "function") {
            capNhatTenNho();
        }

        // Neu dang mo trang nguoi hoc, ve lai
        // de hien thi thong tin Google
        if (
            window.location.hash.startsWith("#/nguoi-hoc") &&
            typeof veNguoiHoc === "function"
        ) {
            veNguoiHoc();
        }

        // Neu dang mo Trang chu, ve lai de cap nhat loi chao va tien do
        if (
            (window.location.hash === "" || window.location.hash === "#/" || window.location.hash === "#") &&
            typeof veTrangChu === "function"
        ) {
            veTrangChu();
        }

    } catch (error) {
        console.error("Lỗi tài khoản:", error);
    }
}

document.addEventListener(
    "DOMContentLoaded",
    taiTaiKhoanGoogle
);
