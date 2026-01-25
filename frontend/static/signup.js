document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ Signup page loaded");

  const signupSection = document.getElementById("signup-section");
  const otpSection = document.getElementById("otp-section");
  const form = document.querySelector(".signup-form");
  const otpEmailDisplay = document.getElementById("otp-email-display");
  const btnVerifyOtp = document.getElementById("btn-verify-otp");

  //going back to previous page
  const backArrow = document.querySelector(".back-arrow");
  if (backArrow) {
    backArrow.addEventListener("click", function () {
      window.history.back();
    });
  }

  // Handle Signup Form Submission
  if (form) {
    // Remove any existing event listeners by cloning logic (optional, but safer to just use capture)
    // For now, let's use a distinct handler that prevents bubbling
    form.onsubmit = async function (e) {
      e.preventDefault();
      e.stopPropagation();

      const inputs = {
        first_name: document.querySelector('input[name="first_name"]').value,
        last_name: document.querySelector('input[name="last_name"]').value,
        email: document.querySelector('input[name="email"]').value,
        password: document.querySelector('input[name="password"]').value
      };

      if (!validateForm(inputs)) return;

      try {
        const response = await fetch("", { // Empty string posts to current URL (signup view)
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
          },
          body: JSON.stringify(inputs)
        });

        const data = await response.json();

        if (response.ok) {
          if (data.verification_required) {
            // Swith to OTP section
            signupSection.style.display = "none";
            otpSection.style.display = "block";
            otpEmailDisplay.textContent = inputs.email;
            showError(""); // Clear errors
          } else if (data.redirect_url) {
            window.location.href = data.redirect_url;
          } else {
            // Should not happen in new flow, but fallback
            window.location.href = "/login/";
          }
        } else {
          showError(data.msg || data.error || "Signup failed");
        }
      } catch (err) {
        console.error(err);
        showError("An error occurred. Please try again.");
      }
    };
  }

  // Handle OTP Verification
  if (btnVerifyOtp) {
    btnVerifyOtp.addEventListener("click", async function () {
      const otp = document.getElementById("otp-code").value;
      const email = otpEmailDisplay.textContent;

      if (!otp) {
        showError("Please enter the verification code");
        return;
      }

      try {
        const response = await fetch("/verify-email/", { // Needs absolute path since we are at /signup/
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
          },
          body: JSON.stringify({ email, otp })
        });

        const data = await response.json();

        if (response.ok) {
          window.location.href = data.redirect_url || "/dashboard/";
        } else {
          showError(data.msg || "Invalid code");
        }
      } catch (err) {
        console.error(err);
        showError("Verification failed");
      }
    });
  }

  function validateForm(inputs) {
    if (!inputs.first_name.trim()) return showError("First name is required");
    if (!inputs.last_name.trim()) return showError("Last name is required");
    if (!inputs.email.trim()) return showError("Email is required");
    if (!isValidEmail(inputs.email)) return showError("Invalid email address");
    if (inputs.password.length < 6) return showError("Password must be at least 6 characters");
    return true;
  }

  function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  function showError(message) {
    if (!message) return;
    let errorDiv = document.querySelector(".error");
    if (!errorDiv) {
      errorDiv = document.createElement("div");
      errorDiv.className = "error";
      const container = document.querySelector(".signup-card");
      container.insertBefore(errorDiv, container.querySelector("form") || container.querySelector("#otp-section"));
    }
    errorDiv.textContent = message;
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + "=")) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Input styling
  const inputs = document.querySelectorAll(".field input");
  inputs.forEach((input) => {
    input.addEventListener("focus", function () {
      this.parentElement.classList.add("focused");
    });
    input.addEventListener("blur", function () {
      if (!this.value) {
        this.parentElement.classList.remove("focused");
      }
    });
  });
});
