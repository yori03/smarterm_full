// ─── Toast Notification ───────────────────────────────────────────────────────
(function initToast() {
  if (!document.getElementById("toast-container")) {
    const c = document.createElement("div");
    c.id = "toast-container";
    document.body.appendChild(c);
  }
})();

export function showToast(message, type = "info", duration = 3500) {
  const container = document.getElementById("toast-container");
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || "ℹ️"}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = "slideOut 0.3s forwards";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ─── Loading Overlay ──────────────────────────────────────────────────────────
let overlay = null;
export function showLoading(text = "Memproses...") {
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.className = "loading-overlay";
    document.body.appendChild(overlay);
  }
  overlay.innerHTML = `
    <div class="spinner dark"></div>
    <p>${text}</p>
  `;
  overlay.style.display = "flex";
}
export function hideLoading() {
  if (overlay) overlay.style.display = "none";
}

// ─── Konfirmasi Dialog ────────────────────────────────────────────────────────
export function confirmDialog(message) {
  return window.confirm(message);
}

// ─── Buka / Tutup Modal ───────────────────────────────────────────────────────
export function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("open");
}
export function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("open");
}

// ─── Format tanggal Indonesia ─────────────────────────────────────────────────
export function formatDate(dateStr) {
  if (!dateStr) return "-";
  try {
    return new Date(dateStr).toLocaleDateString("id-ID", {
      day: "numeric", month: "long", year: "numeric"
    });
  } catch { return dateStr; }
}

// ─── Format datetime ──────────────────────────────────────────────────────────
export function formatDateTime(dateStr) {
  if (!dateStr) return "-";
  try {
    return new Date(dateStr).toLocaleString("id-ID", {
      day: "numeric", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit"
    });
  } catch { return dateStr; }
}

// ─── Hitung umur dari tanggal lahir ──────────────────────────────────────────
export function hitungUmur(tanggalLahir) {
  if (!tanggalLahir) return "-";
  const today = new Date();
  const dob = new Date(tanggalLahir);
  let age = today.getFullYear() - dob.getFullYear();
  const m = today.getMonth() - dob.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) age--;
  return `${age} tahun`;
}

// ─── Render Sidebar dengan link aktif ────────────────────────────────────────
export function highlightActiveNav() {
  const currentFile = window.location.pathname.split("/").pop();
  document.querySelectorAll(".sidebar-link").forEach(link => {
    const href = link.getAttribute("href") || "";
    if (href.includes(currentFile)) link.classList.add("active");
  });
}