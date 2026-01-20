document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ Signup page loaded");

  //going back to previous page
  const backArrow = document.querySelector(".back-arrow");
  if (backArrow) {
    backArrow.addEventListener("click", function () {
      window.history.back();
    });
  }

  const signupForm = document.querySelector(".signup-form");
  if (signupForm) {
    signupForm.addEventListener("submit", function (e) {
      const firstName = document.querySelector('input[name="first_name"]');
      const lastName = document.querySelector('input[name="last_name"]');
      const email = document.querySelector('input[name="email"]');
      const password = document.querySelector('input[name="password"]');

      let isValid = true;
      let errorMessage = "";

      //validating the form
      if (!firstName || !firstName.value.trim()) {
        isValid = false;
        errorMessage = "First name is required";
      } else if (!lastName || !lastName.value.trim()) {
        isValid = false;
        errorMessage = "Last name is required";
      } else if (!email || !email.value.trim()) {
        isValid = false;
        errorMessage = "Email is required";
      } else if (!isValidEmail(email.value)) {
        isValid = false;
        errorMessage = "Please enter a valid email address";
      } else if (!password || password.value.length < 6) {
        isValid = false;
        errorMessage = "Password must be at least 6 characters";
      }

      if (!isValid) {
        e.preventDefault();
        showError(errorMessage);
      }
    });
  }

  //making sure email has the correct format
  function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  function showError(message) {
    let errorDiv = document.querySelector(".error");
    if (!errorDiv) {
      errorDiv = document.createElement("div");
      errorDiv.className = "error";
      const form = document.querySelector(".signup-form");
      form.insertBefore(errorDiv, form.firstChild);
    }
    errorDiv.textContent = message;
  }

  s;
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
