// US-14: Django Website - Basic JavaScript

document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ Django website loaded successfully!");
  console.log("US-14: Basic Django setup complete");

  // Token management UI (runs only on dashboard where elements exist)
  const accessEl = document.getElementById("accessToken");
  const validateBtn = document.getElementById("validateBtn");
  const refreshBtn = document.getElementById("refreshBtn");
  const saveBtn = document.getElementById("saveBtn");
  const tokenStatus = document.getElementById("tokenStatus");
  const tokenMeta = document.getElementById("tokenMeta");
  const actionLog = document.getElementById("actionLog");
  const refreshEl = document.getElementById("refreshToken");

  // Read backend URL from template (exposed as a global meta tag or element)
  const BACKEND_URL = window.BACKEND_URL || null;

  function logAction(message, ok = true) {
    const time = new Date().toLocaleTimeString();
    const el = document.createElement("div");
    el.textContent = `[${time}] ${message}`;
    el.style.marginBottom = "6px";
    if (!ok) el.style.color = "#ef4444";
    actionLog.prepend(el);
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
  }

  async function validateToken() {
    if (!accessEl) return;
    const token = accessEl.value.trim();
    if (!token) {
      logAction("No access token provided", false);
      return;
    }
    try {
      const res = await fetch(`${BACKEND_URL || ""}/token/validate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        tokenStatus.textContent = "Valid";
        tokenStatus.style.background = "#dcfce7";
        tokenStatus.style.color = "#166534";
        tokenMeta.textContent = `User: ${data.user} · Expires: ${new Date(data.exp * 1000).toLocaleString()}`;
        logAction("Token is valid");
      } else {
        const data = await res.json().catch(() => ({ msg: res.statusText }));
        tokenStatus.textContent = "Invalid";
        tokenStatus.style.background = "#fee2e2";
        tokenStatus.style.color = "#991b1b";
        tokenMeta.textContent = data.msg || "Invalid token";
        logAction(`Validation failed: ${data.msg || res.statusText}`, false);
      }
    } catch (e) {
      logAction(`Validation error: ${e.message}`, false);
    }
  }

  async function refreshToken() {
    if (!refreshEl) return;
    const refresh = refreshEl.value.trim();
    if (!refresh) {
      logAction("No refresh token available", false);
      return;
    }
    try {
      const res = await fetch(`${BACKEND_URL || ""}/refresh`, {
        method: "POST",
        headers: { Authorization: `Bearer ${refresh}` },
      });
      if (res.ok) {
        const data = await res.json();
        const newAccess = data.access_token;
        accessEl.value = newAccess;

        // Save the new token to session via Django view
        const csrftoken = getCookie("csrftoken");
        await fetch("/dashboard/update-token/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify({ access_token: newAccess }),
        });

        tokenStatus.textContent = "Refreshed";
        tokenStatus.style.background = "#ecfeff";
        tokenStatus.style.color = "#064e3b";
        tokenMeta.textContent = `New token saved to session`;
        logAction("Token refreshed and saved");
      } else {
        const data = await res.json().catch(() => ({ msg: res.statusText }));
        logAction(`Refresh failed: ${data.msg || res.statusText}`, false);
      }
    } catch (e) {
      logAction(`Refresh error: ${e.message}`, false);
    }
  }

  async function saveToken() {
    if (!accessEl) return;
    const token = accessEl.value.trim();
    if (!token) {
      logAction("No token to save", false);
      return;
    }
    const csrftoken = getCookie("csrftoken");
    try {
      const res = await fetch("/dashboard/update-token/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ access_token: token }),
      });
      const data = await res.json();
      if (res.ok) {
        logAction("Token saved to session");
        tokenStatus.textContent = "Saved";
        tokenStatus.style.background = "#eff6ff";
        tokenStatus.style.color = "#1d4ed8";
      } else {
        logAction(`Save failed: ${data.message || res.statusText}`, false);
      }
    } catch (e) {
      logAction(`Save error: ${e.message}`, false);
    }
  }

  if (validateBtn) validateBtn.addEventListener("click", validateToken);
  if (refreshBtn) refreshBtn.addEventListener("click", refreshToken);
  if (saveBtn) saveBtn.addEventListener("click", saveToken);
});
