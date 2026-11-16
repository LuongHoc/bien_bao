/**
 * Biển Báo AI - Landing Page Interactions & Auth Integration
 */
"use strict";

(function () {
  // 1. Chuyển hướng nếu URL chứa hash ứng dụng SPA cũ
  if (location.hash && /^#\/(hoc|bai-tap|nhan-dang|thong-ke|gioi-thieu|nguoi-hoc)/.test(location.hash)) {
    location.replace("/app" + location.hash);
    return;
  }

  // State
  let csrfToken = null;
  let currentUser = null;

  // DOM Elements
  const header = document.querySelector(".site-header");
  const hamburgerBtn = document.getElementById("hamburger-btn");
  const mobileDrawer = document.getElementById("mobile-drawer");
  const mobileBackdrop = document.getElementById("mobile-backdrop");
  const mobileCloseBtn = document.getElementById("mobile-close-btn");
  const authContainer = document.getElementById("auth-container");
  const mobileAuthContainer = document.getElementById("mobile-auth-container");
  const faqItems = document.querySelectorAll(".faq-item");
  const revealElements = document.querySelectorAll(".reveal-item");

  // 2. Sticky Header Scroll Effect
  function handleScroll() {
    if (window.scrollY > 30) {
      header.classList.add("scrolled");
    } else {
      header.classList.remove("scrolled");
    }
  }
  window.addEventListener("scroll", handleScroll, { passive: true });
  handleScroll();

  // 3. Mobile Drawer Controls
  function openMobileDrawer() {
    mobileDrawer.classList.add("show");
    mobileBackdrop.classList.add("show");
    document.body.style.overflow = "hidden";
  }

  function closeMobileDrawer() {
    mobileDrawer.classList.remove("show");
    mobileBackdrop.classList.remove("show");
    document.body.style.overflow = "";
  }

  if (hamburgerBtn) hamburgerBtn.addEventListener("click", openMobileDrawer);
  if (mobileCloseBtn) mobileCloseBtn.addEventListener("click", closeMobileDrawer);
  if (mobileBackdrop) mobileBackdrop.addEventListener("click", closeMobileDrawer);

  // Close mobile drawer when clicking any link inside
  document.querySelectorAll(".mobile-nav-links a").forEach(link => {
    link.addEventListener("click", closeMobileDrawer);
  });

  // 4. FAQ Accordion
  faqItems.forEach(item => {
    const btn = item.querySelector(".faq-question-btn");
    const pane = item.querySelector(".faq-answer-pane");

    if (!btn || !pane) return;

    btn.addEventListener("click", () => {
      const isOpen = item.classList.contains("open");

      // Close other open accordions
      faqItems.forEach(other => {
        if (other !== item && other.classList.contains("open")) {
          other.classList.remove("open");
          other.querySelector(".faq-question-btn").setAttribute("aria-expanded", "false");
          other.querySelector(".faq-answer-pane").style.maxHeight = null;
        }
      });

      if (isOpen) {
        item.classList.remove("open");
        btn.setAttribute("aria-expanded", "false");
        pane.style.maxHeight = null;
      } else {
        item.classList.add("open");
        btn.setAttribute("aria-expanded", "true");
        pane.style.maxHeight = pane.scrollHeight + "px";
      }
    });
  });

  // 5. Reveal on Scroll (IntersectionObserver)
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("revealed");
          obs.unobserve(entry.target);
        }
      });
    }, {
      rootMargin: "0px 0px -40px 0px",
      threshold: 0.1
    });

    revealElements.forEach(el => observer.observe(el));
  } else {
    revealElements.forEach(el => el.classList.add("revealed"));
  }

  // 6. Interactive AI Pipeline Steps
  const stageSteps = document.querySelectorAll(".stage-step-card");
  if (stageSteps.length > 0) {
    stageSteps.forEach((step, idx) => {
      step.addEventListener("click", () => {
        stageSteps.forEach(s => s.classList.remove("active"));
        step.classList.add("active");
      });
    });
  }

  // 7. Google Auth State Sync
  async function loadAuthState() {
    try {
      const res = await fetch("/api/me", {
        credentials: "same-origin",
        cache: "no-store"
      });

      if (!res.ok) return;

      const data = await res.json();
      if (data.da_dang_nhap && data.user) {
        currentUser = data.user;
        csrfToken = data.csrf_token;
        renderLoggedInUI(currentUser);
      } else {
        renderLoggedOutUI();
      }
    } catch (e) {
      console.warn("Chưa tải được trạng thái đăng nhập:", e);
      renderLoggedOutUI();
    }
  }

  function renderLoggedInUI(user) {
    const avatarHtml = user.anh_dai_dien
      ? `<img class="user-avatar" src="${user.anh_dai_dien}" alt="${user.ten || 'Người dùng'}" referrerpolicy="no-referrer">`
      : `<span class="user-avatar">${(user.ten || "U").charAt(0).toUpperCase()}</span>`;

    const userHtml = `
      <div class="auth-user-dropdown" id="user-menu-trigger">
        <div class="user-pill" role="button" tabindex="0" aria-haspopup="true" aria-expanded="false">
          ${avatarHtml}
          <span class="user-name">${user.ten || "Người học"}</span>
          <svg class="lucide" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></svg>
        </div>
        <ul class="dropdown-menu" id="user-dropdown-menu" role="menu">
          <li>
            <a class="dropdown-item" href="/app" role="menuitem">
              <svg class="lucide" viewBox="0 0 24 24"><path d="M2 4h7a3 3 0 0 1 3 3v14a2 2 0 0 0-2-2H2z"/><path d="M22 4h-7a3 3 0 0 0-3 3v14a2 2 0 0 1 2-2h8z"/></svg>
              <span>Vào học biển báo</span>
            </a>
          </li>
          <li>
            <a class="dropdown-item" href="/app#/thong-ke" role="menuitem">
              <svg class="lucide" viewBox="0 0 24 24"><path d="M3 21h18"/><path d="M6 17v-5M11 17V7M16 17v-8M20 17V4"/></svg>
              <span>Thống kê của tôi</span>
            </a>
          </li>
          <li class="dropdown-divider"></li>
          <li>
            <button class="dropdown-item text-danger" id="logout-btn" role="menuitem" style="width:100%;text-align:left;">
              <svg class="lucide" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
              <span>Đăng xuất</span>
            </button>
          </li>
        </ul>
      </div>
      <a class="btn btn-primary btn-sm" href="/app">
        <span>Vào ứng dụng</span>
        <svg class="lucide" viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"/></svg>
      </a>
    `;

    if (authContainer) {
      authContainer.innerHTML = userHtml;
      setupDropdownToggle();
      setupLogout();
    }

    if (mobileAuthContainer) {
      mobileAuthContainer.innerHTML = `
        <div style="display:flex;align-items:center;gap:10px;padding:8px 0;margin-bottom:8px;">
          ${avatarHtml}
          <div>
            <div style="font-weight:600;font-size:0.95rem;color:var(--text-main);">${user.ten || "Người học"}</div>
            <div style="font-size:0.75rem;color:var(--text-subtle);">Đã đăng nhập Google</div>
          </div>
        </div>
        <a class="btn btn-primary" href="/app" style="width:100%;">Vào ứng dụng học tập</a>
        <button class="btn btn-secondary" id="mobile-logout-btn" style="width:100%;color:var(--traffic-red);">Đăng xuất</button>
      `;
      const mobileLogout = document.getElementById("mobile-logout-btn");
      if (mobileLogout) mobileLogout.addEventListener("click", doLogout);
    }
  }

  function renderLoggedOutUI() {
    const loggedOutHtml = `
      <a class="btn btn-secondary btn-sm" href="/login" title="Đăng nhập tài khoản để lưu kết quả">
        <span>Đăng nhập</span>
      </a>
      <a class="btn btn-primary btn-sm" href="/app">
        <span>Bắt đầu học</span>
        <svg class="lucide" viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"/></svg>
      </a>
    `;

    if (authContainer) authContainer.innerHTML = loggedOutHtml;
    if (mobileAuthContainer) {
      mobileAuthContainer.innerHTML = `
        <a class="btn btn-secondary" href="/login" style="width:100%;">
          <span>Đăng nhập</span>
        </a>
        <a class="btn btn-primary" href="/app" style="width:100%;">
          <span>Bắt đầu học miễn phí</span>
        </a>
      `;
    }
  }

  function setupDropdownToggle() {
    const trigger = document.getElementById("user-menu-trigger");
    if (!trigger) return;
    const pill = trigger.querySelector(".user-pill");
    const menu = trigger.querySelector(".dropdown-menu");

    if (!pill || !menu) return;

    pill.addEventListener("click", (e) => {
      e.stopPropagation();
      const isExpanded = pill.getAttribute("aria-expanded") === "true";
      pill.setAttribute("aria-expanded", String(!isExpanded));
      menu.classList.toggle("show");
    });

    document.addEventListener("click", (e) => {
      if (!trigger.contains(e.target)) {
        pill.setAttribute("aria-expanded", "false");
        menu.classList.remove("show");
      }
    });
  }

  function setupLogout() {
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) logoutBtn.addEventListener("click", doLogout);
  }

  async function doLogout() {
    try {
      const res = await fetch("/auth/logout", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-CSRF-Token": csrfToken || ""
        }
      });
      if (res.ok) {
        location.reload();
      } else {
        alert("Không thể đăng xuất. Vui lòng thử lại.");
      }
    } catch (e) {
      console.error("Lỗi đăng xuất:", e);
      alert("Lỗi kết nối máy chủ.");
    }
  }

  // Khởi động
  document.addEventListener("DOMContentLoaded", loadAuthState);
})();
