/**
 * auth.js - Điều khiển giao diện Xác thực (Đăng nhập / Đăng ký) Biển Báo AI
 */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const loginSection = document.getElementById("login-section");
  const registerSection = document.getElementById("register-section");
  const forgotSection = document.getElementById("forgot-section");
  const resetSection = document.getElementById("reset-section");

  const switchToRegister = document.getElementById("switch-to-register");
  const switchToLogin = document.getElementById("switch-to-login");
  const btnForgotPassword = document.getElementById("btn-forgot-password");
  const forgotBackToLogin = document.getElementById("forgot-back-to-login");
  const resetBackToLogin = document.getElementById("reset-back-to-login");

  const formLogin = document.getElementById("form-login");
  const formRegister = document.getElementById("form-register");
  const formForgot = document.getElementById("form-forgot");
  const formReset = document.getElementById("form-reset");

  const btnSubmitLogin = document.getElementById("btn-submit-login");
  const btnSubmitRegister = document.getElementById("btn-submit-register");
  const btnSubmitForgot = document.getElementById("btn-submit-forgot");
  const btnSubmitReset = document.getElementById("btn-submit-reset");
  const resetTokenInput = document.getElementById("reset-token");

  const alertBox = document.getElementById("auth-alert");
  const alertContent = document.getElementById("alert-content");
  const resendWrap = document.getElementById("resend-wrap");
  const btnDoResend = document.getElementById("btn-do-resend");

  // Read URL query parameters
  const params = new URLSearchParams(window.location.search);
  const nextUrl = params.get("next") || "/app";
  let unverifiedEmail = params.get("email") || "";
  let lastRegisteredUsername = "";
  const resetToken = params.get("token") || "";
  if (resetTokenInput && resetToken) {
    resetTokenInput.value = resetToken;
  }

  // 1. Alert display helpers
  function showAlert(message, type = "error") {
    alertBox.className = `alert-box ${type}`;
    alertContent.innerHTML = message;
    alertBox.style.display = "flex";
    alertBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function hideAlert() {
    alertBox.style.display = "none";
    alertContent.innerHTML = "";
  }

  // 2. Section switching logic (Đăng nhập / Đăng ký / Quên MK / Đặt lại MK)
  function setTab(mode) {
    hideAlert();
    resendWrap.style.display = "none";

    // Ẩn tất cả các section trước
    loginSection.style.display = "none";
    loginSection.classList.remove("active");
    registerSection.style.display = "none";
    registerSection.classList.remove("active");
    if (forgotSection) {
      forgotSection.style.display = "none";
      forgotSection.classList.remove("active");
    }
    if (resetSection) {
      resetSection.style.display = "none";
      resetSection.classList.remove("active");
    }

    if (mode === "register") {
      registerSection.style.display = "block";
      registerSection.classList.add("active");
      document.title = "Đăng ký tài khoản - Biển Báo AI";
      const nameInput = document.getElementById("reg-name");
      if (nameInput) nameInput.focus();
    } else if (mode === "forgot") {
      if (forgotSection) {
        forgotSection.style.display = "block";
        forgotSection.classList.add("active");
      }
      setForgotStep(1);
    } else if (mode === "reset") {
      if (forgotSection) {
        forgotSection.style.display = "block";
        forgotSection.classList.add("active");
      }
      setForgotStep(3);
    } else {
      // Mặc định: login
      loginSection.style.display = "block";
      loginSection.classList.add("active");
      document.title = "Đăng nhập - Biển Báo AI";
      const emailInput = document.getElementById("login-email");
      if (emailInput) emailInput.focus();
    }
  }

  switchToRegister.addEventListener("click", () => {
    setTab("register");
    setRegisterStep(1);
  });
  switchToLogin.addEventListener("click", () => setTab("login"));

  if (btnForgotPassword) {
    btnForgotPassword.addEventListener("click", (e) => {
      e.preventDefault();
      setTab("forgot");
    });
  }
  if (forgotBackToLogin) {
    forgotBackToLogin.addEventListener("click", () => setTab("login"));
  }
  if (resetBackToLogin) {
    resetBackToLogin.addEventListener("click", () => setTab("login"));
  }

  // Check initial mode from URL or path
  if (
    window.location.pathname.endsWith("/reset-password") ||
    params.get("mode") === "reset" ||
    (params.get("token") && !window.location.pathname.endsWith("/verify-email"))
  ) {
    setTab("reset");
  } else if (
    window.location.pathname.endsWith("/forgot-password") ||
    params.get("mode") === "forgot" ||
    window.location.hash === "#quen-mat-khau" ||
    window.location.hash === "#forgot"
  ) {
    setTab("forgot");
  } else if (
    params.get("mode") === "register" ||
    window.location.pathname.endsWith("/register") ||
    window.location.hash === "#register"
  ) {
    setTab("register");
  } else {
    setTab("login");
  }

  if (params.get("verified") === "1") {
    showAlert("Xác minh địa chỉ email thành công! Bạn có thể đăng nhập ngay bây giờ.", "success");
  } else if (params.get("error") === "invalid_token") {
    showAlert("Liên kết xác minh không hợp lệ hoặc đã hết hạn. Vui lòng thử đăng nhập hoặc yêu cầu gửi lại.", "error");
  }

  if (params.get("email")) {
    const elLoginEmail = document.getElementById("login-email");
    if (elLoginEmail) elLoginEmail.value = params.get("email");
  }

  // 3. Toggle password visibility
  document.querySelectorAll(".btn-toggle-eye").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      const input = document.getElementById(targetId);
      const eyeOpen = btn.querySelector(".eye-open");
      const eyeClosed = btn.querySelector(".eye-closed");

      if (input.type === "password") {
        input.type = "text";
        eyeOpen.style.display = "none";
        eyeClosed.style.display = "block";
      } else {
        input.type = "password";
        eyeOpen.style.display = "block";
        eyeClosed.style.display = "none";
      }
    });
  });

  // 4. Handle Login Submission
  formLogin.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert();
    resendWrap.style.display = "none";

    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    const remember = document.getElementById("login-remember").checked;

    if (!email || !password) {
      showAlert("Vui lòng nhập đầy đủ tên tài khoản hoặc email và mật khẩu.");
      return;
    }

    setBtnLoading(btnSubmitLogin, true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tai_khoan: email, email, mat_khau: password, ghi_nho: remember })
      });

      const data = await res.json();

      if (res.ok && data.thanh_cong) {
        showAlert("Đăng nhập thành công! Đang chuyển hướng...", "success");
        setTimeout(() => {
          window.location.href = nextUrl;
        }, 800);
      } else {
        if (data.chua_xac_minh) {
          unverifiedEmail = data.email || email;
          if (data.chuyen_otp) {
            regEmail = unverifiedEmail;
            setTab("register");
            setRegisterStep(2);
            startRegResendCountdown(data.co_the_gui_lai_sau || 60);
            showAlert(data.thong_bao || "Tài khoản chưa xác minh email. Mã xác thực OTP mới đã được gửi.", "info");
          } else {
            showAlert(data.thong_bao || "Tài khoản chưa xác minh email.", "info");
            resendWrap.style.display = "block";
          }
        } else {
          showAlert(data.thong_bao || "Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.");
        }
      }
    } catch (err) {
      showAlert("Không thể kết nối đến máy chủ. Vui lòng kiểm tra mạng và thử lại.");
    } finally {
      setBtnLoading(btnSubmitLogin, false);
    }
  });

  // 5. Handle Register Submission
  formRegister.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert();
    resendWrap.style.display = "none";

    const name = document.getElementById("reg-name").value.trim();
    const username = (document.getElementById("reg-username")?.value || "").trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;
    const confirm = document.getElementById("reg-confirm").value;

    // Client-side validations
    if (!name || name.length < 2 || name.length > 50) {
      showAlert("Họ và tên phải có độ dài từ 2 đến 50 ký tự.");
      return;
    }

    if (!username) {
      showAlert("Vui lòng nhập tên tài khoản.");
      return;
    }
    if (username.length < 3 || username.length > 30) {
      showAlert("Tên tài khoản phải có độ dài từ 3 đến 30 ký tự.");
      return;
    }
    const usernameRegex = /^[a-zA-Z0-9_.]{3,30}$/;
    if (!usernameRegex.test(username)) {
      showAlert("Tên tài khoản chỉ được chứa chữ cái, chữ số, dấu gạch dưới (_) và dấu chấm (.), không chứa khoảng trắng.");
      return;
    }
    const reservedUsernames = [
      "admin", "administrator", "root", "system", "moderator",
      "bienbao", "bienbaoai", "superuser", "guest", "anonymous"
    ];
    if (reservedUsernames.includes(username.toLowerCase())) {
      showAlert("Tên tài khoản này được bảo lưu bởi hệ thống. Vui lòng chọn tên khác.");
      return;
    }

    if (email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        showAlert("Địa chỉ email không đúng định dạng.");
        return;
      }
    }

    if (!password || password.length < 8) {
      showAlert("Mật khẩu phải chứa ít nhất 8 ký tự.");
      return;
    }
    if (password.length > 128) {
      showAlert("Mật khẩu không được vượt quá 128 ký tự.");
      return;
    }
    if (password !== confirm) {
      showAlert("Mật khẩu xác nhận không khớp. Vui lòng nhập lại.");
      return;
    }

    setBtnLoading(btnSubmitRegister, true);

    try {
      const payload = {
        ten: name,
        username: username,
        email: email || null,
        mat_khau: password,
        xac_nhan_mat_khau: confirm
      };

      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (res.ok && data.thanh_cong) {
        lastRegisteredUsername = username;
        formRegister.reset();

        const successTitle = document.getElementById("reg-success-title");
        const successDesc = document.getElementById("reg-success-desc");

        if (data.can_xac_minh === false) {
          // Đăng ký không cần xác minh email
          unverifiedEmail = "";
          regEmail = "";
          if (successTitle) successTitle.textContent = "Đăng ký tài khoản thành công!";
          if (successDesc) {
            successDesc.textContent = data.thong_bao || "Tài khoản của bạn đã được tạo thành công. Bạn có thể đăng nhập ngay bằng tên tài khoản và mật khẩu vừa tạo.";
          }
          setRegisterStep(3);
        } else {
          // Đăng ký có email -> cần xác thực OTP
          unverifiedEmail = email;
          regEmail = email;
          if (successTitle) successTitle.textContent = "Kích hoạt tài khoản thành công!";
          if (successDesc) {
            successDesc.textContent = "Địa chỉ email của bạn đã được xác minh thành công. Bây giờ bạn có thể đăng nhập để bắt đầu hành trình học tập và nhận dạng biển báo AI.";
          }
          setRegisterStep(2);
          startRegResendCountdown(data.co_the_gui_lai_sau || 60);
          showAlert(data.thong_bao || "Đăng ký thành công! Vui lòng nhập mã OTP đã gửi đến email của bạn.", "success");
        }
      } else {
        if (data.chua_xac_minh) {
          unverifiedEmail = email;
          regEmail = email;
          showAlert(data.thong_bao || "Email đã đăng ký nhưng chưa xác minh.", "info");
          resendWrap.style.display = "block";
        } else {
          showAlert(data.thong_bao || "Đăng ký không thành công.");
        }
      }
    } catch (err) {
      showAlert("Lỗi kết nối khi gửi dữ liệu đăng ký. Vui lòng thử lại sau.");
    } finally {
      setBtnLoading(btnSubmitRegister, false);
    }
  });

  // 6. Resend verification email
  btnDoResend.addEventListener("click", async () => {
    if (!unverifiedEmail) {
      showAlert("Vui lòng nhập địa chỉ email trước khi yêu cầu gửi lại.", "info");
      return;
    }

    btnDoResend.disabled = true;
    const originalText = btnDoResend.textContent;
    btnDoResend.textContent = "Đang gửi...";

    try {
      const res = await fetch("/api/auth/resend-verification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: unverifiedEmail })
      });
      const data = await res.json();

      showAlert(data.thong_bao || "Đã gửi lại email xác minh.", "success");
      regEmail = unverifiedEmail;
      setTab("register");
      setRegisterStep(2);
      startRegResendCountdown(data.co_the_gui_lai_sau || 60);

      // Cooldown timer 60s
      let countdown = 60;
      const interval = setInterval(() => {
        countdown--;
        if (countdown > 0) {
          btnDoResend.textContent = `Gửi lại sau (${countdown}s)`;
        } else {
          clearInterval(interval);
          btnDoResend.disabled = false;
          btnDoResend.textContent = originalText;
        }
      }, 1000);
    } catch (err) {
      showAlert("Không thể gửi lại email vào lúc này. Vui lòng thử lại sau ít phút.");
      btnDoResend.disabled = false;
      btnDoResend.textContent = originalText;
    }
  });

  // =========================================================================
  // 5b. QUY TRÌNH XÁC THỰC OTP ĐĂNG KÝ (3 BƯỚC)
  // =========================================================================
  let regEmail = "";
  let regResendCountdownTimer = null;

  const registerStep1 = document.getElementById("register-step-1");
  const registerStep2 = document.getElementById("register-step-2");
  const registerStep3 = document.getElementById("register-step-3");

  const regOtpDisplayEmail = document.getElementById("reg-otp-display-email");
  const btnBackToRegForm = document.getElementById("btn-back-to-reg-form");
  const formVerifyRegOtp = document.getElementById("form-verify-reg-otp");
  const btnSubmitRegOtp = document.getElementById("btn-submit-reg-otp");
  const btnResendRegOtp = document.getElementById("btn-resend-reg-otp");
  const regResendCountdownSpan = document.getElementById("reg-resend-countdown");
  const regOtpDigits = document.querySelectorAll(".reg-otp-digit");
  const regOtpBackToLogin = document.getElementById("reg-otp-back-to-login");
  const btnRegSuccessToLogin = document.getElementById("btn-reg-success-to-login");

  function setRegisterStep(step) {
    hideAlert();
    if (registerStep1) registerStep1.style.display = "none";
    if (registerStep2) registerStep2.style.display = "none";
    if (registerStep3) registerStep3.style.display = "none";

    if (step === 1) {
      if (registerStep1) registerStep1.style.display = "block";
      document.title = "Đăng ký tài khoản - Biển Báo AI";
      const nameInput = document.getElementById("reg-name");
      if (nameInput) nameInput.focus();
    } else if (step === 2) {
      if (registerStep2) registerStep2.style.display = "block";
      document.title = "Kích hoạt tài khoản - Biển Báo AI";
      if (regOtpDisplayEmail && (regEmail || unverifiedEmail)) {
        const target = regEmail || unverifiedEmail;
        const parts = target.split("@");
        if (parts.length === 2) {
          const namePart = parts[0];
          const maskedName = namePart.length <= 2 ? namePart.charAt(0) + "***" : namePart.slice(0, 2) + "***";
          regOtpDisplayEmail.textContent = `${maskedName}@${parts[1]}`;
        } else {
          regOtpDisplayEmail.textContent = target;
        }
      }
      regOtpDigits.forEach(d => (d.value = ""));
      if (regOtpDigits[0]) regOtpDigits[0].focus();
    } else if (step === 3) {
      if (registerStep3) registerStep3.style.display = "block";
      document.title = "Kích hoạt thành công - Biển Báo AI";
    }
  }

  function startRegResendCountdown(seconds = 60) {
    if (regResendCountdownTimer) clearInterval(regResendCountdownTimer);
    if (!btnResendRegOtp || !regResendCountdownSpan) return;

    let countdown = seconds;
    btnResendRegOtp.disabled = true;
    regResendCountdownSpan.textContent = countdown;
    btnResendRegOtp.innerHTML = `Gửi lại mã (<span id="reg-resend-countdown">${countdown}</span>s)`;

    regResendCountdownTimer = setInterval(() => {
      countdown--;
      const span = document.getElementById("reg-resend-countdown");
      if (span) span.textContent = countdown;

      if (countdown <= 0) {
        clearInterval(regResendCountdownTimer);
        regResendCountdownTimer = null;
        btnResendRegOtp.disabled = false;
        btnResendRegOtp.innerHTML = "Gửi lại mã";
      }
    }, 1000);
  }

  // OTP inputs handling for registration
  if (regOtpDigits && regOtpDigits.length > 0) {
    regOtpDigits.forEach((digit, index) => {
      digit.addEventListener("input", () => {
        const val = digit.value.replace(/\D/g, "");
        digit.value = val ? val.charAt(val.length - 1) : "";
        if (digit.value && index < regOtpDigits.length - 1) {
          regOtpDigits[index + 1].focus();
        }
      });

      digit.addEventListener("keydown", (e) => {
        if (e.key === "Backspace") {
          if (!digit.value && index > 0) {
            regOtpDigits[index - 1].focus();
            regOtpDigits[index - 1].value = "";
          }
        } else if (e.key === "ArrowLeft" && index > 0) {
          regOtpDigits[index - 1].focus();
        } else if (e.key === "ArrowRight" && index < regOtpDigits.length - 1) {
          regOtpDigits[index + 1].focus();
        }
      });
    });

    const regInputsWrap = document.getElementById("reg-otp-inputs-wrap");
    if (regInputsWrap) {
      regInputsWrap.addEventListener("paste", (e) => {
        e.preventDefault();
        const pasteData = (e.clipboardData || window.clipboardData).getData("text").trim();
        const digitsOnly = pasteData.replace(/\D/g, "").slice(0, 6);
        if (digitsOnly) {
          digitsOnly.split("").forEach((ch, idx) => {
            if (regOtpDigits[idx]) regOtpDigits[idx].value = ch;
          });
          const nextIdx = Math.min(digitsOnly.length, regOtpDigits.length - 1);
          if (regOtpDigits[nextIdx]) regOtpDigits[nextIdx].focus();
        }
      });
    }
  }

  // Handle Verify Registration OTP form submit
  if (formVerifyRegOtp) {
    formVerifyRegOtp.addEventListener("submit", async (e) => {
      e.preventDefault();
      hideAlert();

      const otp = Array.from(regOtpDigits).map(d => d.value).join("");
      if (!otp || otp.length !== 6) {
        showAlert("Vui lòng nhập đầy đủ 6 chữ số của mã xác nhận.");
        return;
      }

      const emailToVerify = regEmail || unverifiedEmail;
      if (!emailToVerify) {
        showAlert("Không xác định được email cần kích hoạt. Vui lòng quay lại đăng ký.");
        return;
      }

      setBtnLoading(btnSubmitRegOtp, true);

      try {
        const res = await fetch("/api/auth/verify-registration-otp", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: emailToVerify, otp })
        });
        const data = await res.json();

        if (res.ok && data.thanh_cong) {
          setRegisterStep(3);
        } else {
          showAlert(data.thong_bao || "Mã xác nhận không chính xác.");
          if (data.attempts_left !== undefined && data.attempts_left <= 0) {
            regOtpDigits.forEach(d => (d.disabled = true));
            if (btnSubmitRegOtp) btnSubmitRegOtp.disabled = true;
          }
        }
      } catch (err) {
        showAlert("Không thể kết nối đến máy chủ. Vui lòng thử lại sau.");
      } finally {
        setBtnLoading(btnSubmitRegOtp, false);
      }
    });
  }

  // Resend registration OTP
  if (btnResendRegOtp) {
    btnResendRegOtp.addEventListener("click", async () => {
      const emailToResend = regEmail || unverifiedEmail;
      if (!emailToResend) {
        showAlert("Vui lòng nhập lại email cần kích hoạt.", "info");
        return;
      }

      btnResendRegOtp.disabled = true;
      btnResendRegOtp.textContent = "Đang gửi...";

      try {
        const res = await fetch("/api/auth/resend-verification", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: emailToResend })
        });
        const data = await res.json();

        if (res.ok && data.thanh_cong) {
          showAlert(data.thong_bao || "Mã kích hoạt mới đã được gửi vào email của bạn.", "success");
          startRegResendCountdown(data.co_the_gui_lai_sau || 60);
          regOtpDigits.forEach(d => {
            d.value = "";
            d.disabled = false;
          });
          if (btnSubmitRegOtp) btnSubmitRegOtp.disabled = false;
          if (regOtpDigits[0]) regOtpDigits[0].focus();
        } else {
          showAlert(data.thong_bao || "Không thể gửi lại mã vào lúc này.");
          btnResendRegOtp.disabled = false;
          btnResendRegOtp.textContent = "Gửi lại mã";
        }
      } catch (err) {
        showAlert("Lỗi kết nối khi gửi lại mã OTP.");
        btnResendRegOtp.disabled = false;
        btnResendRegOtp.textContent = "Gửi lại mã";
      }
    });
  }

  if (btnBackToRegForm) {
    btnBackToRegForm.addEventListener("click", () => setRegisterStep(1));
  }
  if (regOtpBackToLogin) {
    regOtpBackToLogin.addEventListener("click", () => setTab("login"));
  }
  if (btnRegSuccessToLogin) {
    btnRegSuccessToLogin.addEventListener("click", () => {
      setTab("login");
      const loginEmailInput = document.getElementById("login-email");
      if (loginEmailInput) {
        if (lastRegisteredUsername) {
          loginEmailInput.value = lastRegisteredUsername;
        } else if (regEmail || unverifiedEmail) {
          loginEmailInput.value = regEmail || unverifiedEmail;
        }
      }
      const loginPwInput = document.getElementById("login-password");
      if (loginPwInput) loginPwInput.focus();
    });
  }

  // =========================================================================
  // 7. QUY TRÌNH QUÊN MẬT KHẨU & XÁC THỰC OTP 3 BƯỚC
  // =========================================================================
  let forgotEmail = "";
  let currentResetGrant = "";
  let resendCountdownTimer = null;

  const forgotStep1 = document.getElementById("forgot-step-1");
  const forgotStep2 = document.getElementById("forgot-step-2");
  const forgotStep3 = document.getElementById("forgot-step-3");
  const forgotStep4 = document.getElementById("forgot-step-4");

  const otpDisplayEmail = document.getElementById("otp-display-email");
  const btnChangeEmail = document.getElementById("btn-change-email");
  const formVerifyOtp = document.getElementById("form-verify-otp");
  const btnSubmitOtp = document.getElementById("btn-submit-otp");
  const btnResendOtp = document.getElementById("btn-resend-otp");
  const resendCountdownSpan = document.getElementById("resend-countdown");
  const otpInputsWrap = document.getElementById("otp-inputs-wrap");
  const otpDigits = document.querySelectorAll(".otp-digit");

  const otpBackToLogin = document.getElementById("otp-back-to-login");
  const btnSuccessToLogin = document.getElementById("btn-success-to-login");

  // Hàm chuyển đổi các bước con trong quy trình Quên mật khẩu
  function setForgotStep(step) {
    hideAlert();

    if (forgotStep1) forgotStep1.style.display = "none";
    if (forgotStep2) forgotStep2.style.display = "none";
    if (forgotStep3) forgotStep3.style.display = "none";
    if (forgotStep4) forgotStep4.style.display = "none";

    if (step === 1) {
      if (forgotStep1) forgotStep1.style.display = "block";
      document.title = "Quên mật khẩu - Biển Báo AI";
      const input = document.getElementById("forgot-email");
      if (input) {
        if (forgotEmail) input.value = forgotEmail;
        input.focus();
      }
    } else if (step === 2) {
      if (forgotStep2) forgotStep2.style.display = "block";
      document.title = "Xác thực email - Biển Báo AI";
      // Hiển thị email đã che một phần (ví dụ ng***@gmail.com)
      if (otpDisplayEmail && forgotEmail) {
        const parts = forgotEmail.split("@");
        if (parts.length === 2) {
          const namePart = parts[0];
          const maskedName = namePart.length <= 2 ? namePart.charAt(0) + "***" : namePart.slice(0, 2) + "***";
          otpDisplayEmail.textContent = `${maskedName}@${parts[1]}`;
        } else {
          otpDisplayEmail.textContent = forgotEmail;
        }
      }
      // Reset và focus ô OTP đầu tiên
      otpDigits.forEach(d => (d.value = ""));
      if (otpDigits[0]) otpDigits[0].focus();
    } else if (step === 3) {
      if (forgotStep3) forgotStep3.style.display = "block";
      document.title = "Đặt lại mật khẩu - Biển Báo AI";
      const pwInput = document.getElementById("reset-password");
      if (pwInput) pwInput.focus();
    } else if (step === 4) {
      if (forgotStep4) forgotStep4.style.display = "block";
      document.title = "Đổi mật khẩu thành công - Biển Báo AI";
    }
  }

  // Đếm ngược thời gian gửi lại mã OTP (60 giây)
  function startResendCountdown(seconds = 60) {
    if (resendCountdownTimer) clearInterval(resendCountdownTimer);
    if (!btnResendOtp || !resendCountdownSpan) return;

    let countdown = seconds;
    btnResendOtp.disabled = true;
    resendCountdownSpan.textContent = countdown;
    btnResendOtp.innerHTML = `Gửi lại mã (<span id="resend-countdown">${countdown}</span>s)`;

    resendCountdownTimer = setInterval(() => {
      countdown--;
      const span = document.getElementById("resend-countdown");
      if (span) span.textContent = countdown;

      if (countdown <= 0) {
        clearInterval(resendCountdownTimer);
        resendCountdownTimer = null;
        btnResendOtp.disabled = false;
        btnResendOtp.innerHTML = "Gửi lại mã";
      }
    }, 1000);
  }

  // Xử lý nhập liệu các ô OTP 6 chữ số
  if (otpDigits && otpDigits.length > 0) {
    otpDigits.forEach((digit, index) => {
      // Khi gõ phím số
      digit.addEventListener("input", (e) => {
        const val = digit.value.replace(/\D/g, "");
        digit.value = val ? val.charAt(val.length - 1) : "";

        if (digit.value && index < otpDigits.length - 1) {
          otpDigits[index + 1].focus();
        }
      });

      // Điều hướng phím Backspace và mũi tên
      digit.addEventListener("keydown", (e) => {
        if (e.key === "Backspace") {
          if (!digit.value && index > 0) {
            otpDigits[index - 1].focus();
            otpDigits[index - 1].value = "";
          }
        } else if (e.key === "ArrowLeft" && index > 0) {
          otpDigits[index - 1].focus();
        } else if (e.key === "ArrowRight" && index < otpDigits.length - 1) {
          otpDigits[index + 1].focus();
        }
      });
    });

    // Hỗ trợ dán mã OTP 6 chữ số từ clipboard
    if (otpInputsWrap) {
      otpInputsWrap.addEventListener("paste", (e) => {
        e.preventDefault();
        const pasted = (e.clipboardData || window.clipboardData).getData("text") || "";
        const digits = pasted.replace(/\D/g, "").slice(0, 6);
        if (digits) {
          for (let i = 0; i < digits.length; i++) {
            if (otpDigits[i]) otpDigits[i].value = digits[i];
          }
          const nextIndex = Math.min(digits.length, otpDigits.length - 1);
          if (otpDigits[nextIndex]) otpDigits[nextIndex].focus();
        }
      });
    }
  }

  // Bước 1: Gửi yêu cầu mã OTP
  if (formForgot) {
    formForgot.addEventListener("submit", async (e) => {
      e.preventDefault();
      hideAlert();

      const dinhDanhInput = document.getElementById("forgot-email");
      const dinhDanh = dinhDanhInput ? dinhDanhInput.value.trim() : "";
      if (!dinhDanh) {
        showAlert("Vui lòng nhập tên tài khoản hoặc địa chỉ email.");
        return;
      }

      setBtnLoading(btnSubmitForgot, true);

      try {
        const res = await fetch("/api/auth/forgot-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dinh_danh: dinhDanh, email: dinhDanh })
        });
        const data = await res.json();

        if (res.ok && data.thanh_cong) {
          forgotEmail = data.email || dinhDanh;
          // Chuyển sang Bước 2 (Xác thực OTP)
          setForgotStep(2);
          startResendCountdown(data.co_the_gui_lai_sau || 60);
          showAlert(data.thong_bao || "Mã xác nhận 6 chữ số đã được gửi tới email của bạn (hiệu lực 5 phút).", "info");
        } else {
          if (data.code === "no_recovery_email") {
            showAlert(
              data.thong_bao || "Tài khoản này chưa liên kết email nên không thể nhận mã OTP khôi phục. Vui lòng liên hệ quản trị viên.",
              "error"
            );
          } else {
            showAlert(data.thong_bao || "Không thể gửi yêu cầu xác thực. Vui lòng thử lại sau.");
          }
        }
      } catch (err) {
        showAlert("Lỗi kết nối khi gửi yêu cầu. Vui lòng kiểm tra mạng và thử lại.");
      } finally {
        setBtnLoading(btnSubmitForgot, false);
      }
    });
  }

  // Gửi lại mã OTP
  if (btnResendOtp) {
    btnResendOtp.addEventListener("click", async () => {
      if (btnResendOtp.disabled || !forgotEmail) return;

      hideAlert();
      btnResendOtp.disabled = true;
      btnResendOtp.textContent = "Đang gửi...";

      try {
        const res = await fetch("/api/auth/resend-reset-otp", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: forgotEmail })
        });
        const data = await res.json();

        if (res.ok && data.thanh_cong) {
          startResendCountdown(data.co_the_gui_lai_sau || 60);
          showAlert("Mã xác nhận mới đã được gửi vào hộp thư của bạn.", "info");
          otpDigits.forEach(d => (d.value = ""));
          if (otpDigits[0]) otpDigits[0].focus();
        } else {
          btnResendOtp.disabled = false;
          btnResendOtp.textContent = "Gửi lại mã";
          showAlert(data.thong_bao || "Không thể gửi lại mã vào lúc này.");
        }
      } catch (err) {
        btnResendOtp.disabled = false;
        btnResendOtp.textContent = "Gửi lại mã";
        showAlert("Lỗi kết nối khi gửi lại mã. Vui lòng thử lại.");
      }
    });
  }

  // Quay lại Bước 1: Thay đổi email
  if (btnChangeEmail) {
    btnChangeEmail.addEventListener("click", () => {
      setForgotStep(1);
    });
  }

  // Bước 2: Xác thực mã OTP
  if (formVerifyOtp) {
    formVerifyOtp.addEventListener("submit", async (e) => {
      e.preventDefault();
      hideAlert();

      const otp = Array.from(otpDigits).map(d => d.value.trim()).join("");
      if (!otp || otp.length !== 6 || !/^\d{6}$/.test(otp)) {
        showAlert("Vui lòng nhập đầy đủ 6 chữ số mã xác nhận.");
        const emptyIndex = Array.from(otpDigits).findIndex(d => !d.value);
        if (emptyIndex !== -1 && otpDigits[emptyIndex]) {
          otpDigits[emptyIndex].focus();
        }
        return;
      }

      setBtnLoading(btnSubmitOtp, true);

      try {
        const res = await fetch("/api/auth/verify-reset-otp", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: forgotEmail, otp })
        });
        const data = await res.json();

        if (res.ok && data.thanh_cong && data.reset_grant) {
          // Lưu reset_grant an toàn trong biến JS
          currentResetGrant = data.reset_grant;
          if (resetTokenInput) resetTokenInput.value = data.reset_grant;

          // Chuyển sang Bước 3 (Đặt mật khẩu mới)
          setForgotStep(3);
        } else {
          showAlert(data.thong_bao || "Mã xác nhận không hợp lệ hoặc đã hết hạn.");
          if (data.code === "max_attempts_exceeded") {
            // Khóa mã -> cho phép gửi lại
            if (btnResendOtp) btnResendOtp.disabled = false;
          }
        }
      } catch (err) {
        showAlert("Lỗi kết nối máy chủ khi xác thực OTP. Vui lòng thử lại.");
      } finally {
        setBtnLoading(btnSubmitOtp, false);
      }
    });
  }

  // Bước 3: Đặt mật khẩu mới
  if (formReset) {
    formReset.addEventListener("submit", async (e) => {
      e.preventDefault();
      hideAlert();

      const grant = currentResetGrant || (resetTokenInput ? resetTokenInput.value.trim() : "");
      const password = document.getElementById("reset-password").value;
      const confirm = document.getElementById("reset-confirm").value;

      if (!grant) {
        showAlert("Mã xác thực không hợp lệ hoặc phiên đặt lại đã kết thúc. Vui lòng thực hiện lại từ đầu.");
        setForgotStep(1);
        return;
      }
      if (!password || password.length < 8) {
        showAlert("Mật khẩu mới phải có tối thiểu 8 ký tự.");
        return;
      }
      if (password.length > 128) {
        showAlert("Mật khẩu không được vượt quá 128 ký tự.");
        return;
      }
      if (password !== confirm) {
        showAlert("Mật khẩu xác nhận không khớp. Vui lòng nhập lại.");
        return;
      }

      setBtnLoading(btnSubmitReset, true);

      try {
        const res = await fetch("/api/auth/reset-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            reset_grant: grant,
            token: grant,
            mat_khau: password,
            xac_nhan_mat_khau: confirm
          })
        });
        const data = await res.json();

        if (res.ok && data.thanh_cong) {
          // Xóa token nhạy cảm khỏi bộ nhớ
          currentResetGrant = "";
          forgotEmail = "";
          if (resetTokenInput) resetTokenInput.value = "";
          formReset.reset();

          // Chuyển sang Bước 4 (Thông báo thành công)
          setForgotStep(4);
        } else {
          showAlert(data.thong_bao || "Đặt lại mật khẩu không thành công.");
        }
      } catch (err) {
        showAlert("Lỗi kết nối đến máy chủ. Vui lòng thử lại sau.");
      } finally {
        setBtnLoading(btnSubmitReset, false);
      }
    });
  }

  // Các nút chuyển về Đăng nhập
  if (otpBackToLogin) otpBackToLogin.addEventListener("click", () => setTab("login"));
  if (btnSuccessToLogin) btnSuccessToLogin.addEventListener("click", () => setTab("login"));


  // Helper: toggle button loading state
  function setBtnLoading(btn, isLoading) {
    if (!btn) return;
    const txt = btn.querySelector(".btn-text");
    const sp = btn.querySelector(".btn-spinner");
    btn.disabled = isLoading;
    if (txt) txt.style.display = isLoading ? "none" : "inline";
    if (sp) sp.style.display = isLoading ? "inline-block" : "none";
  }
});
