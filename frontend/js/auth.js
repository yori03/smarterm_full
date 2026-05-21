/**
 * auth.js - Manajemen sesi pengguna di frontend
 *
 * Setelah login berhasil, backend mengembalikan:
 *   { access_token, token_type, role, nama_lengkap }
 *
 * Frontend menyimpan ini di localStorage agar tidak hilang saat refresh.
 * Setiap halaman protected memanggil guardPage() di awal.
 */

// ─── Simpan data session setelah login ───────────────────────────────────────
export function saveSession(tokenData) {
  localStorage.setItem("access_token", tokenData.access_token);
  localStorage.setItem("role", tokenData.role);
  localStorage.setItem("nama_lengkap", tokenData.nama_lengkap);
}

// ─── Ambil data session ───────────────────────────────────────────────────────
export function getSession() {
  return {
    token: localStorage.getItem("access_token"),
    role: localStorage.getItem("role"),
    nama: localStorage.getItem("nama_lengkap")
  };
}

// ─── Cek apakah sudah login ───────────────────────────────────────────────────
export function isLoggedIn() {
  return !!localStorage.getItem("access_token");
}

// ─── Hapus semua session (logout) ────────────────────────────────────────────
export function clearSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("role");
  localStorage.removeItem("nama_lengkap");
}

/**
 * Guard halaman: cek login + cek role
 * Panggil di awal setiap halaman protected.
 *
 * Contoh penggunaan:
 *   guardPage("admin")   → hanya admin boleh masuk
 *   guardPage("dokter")  → hanya dokter boleh masuk
 *   guardPage()          → cukup login saja
 */
export function guardPage(requiredRole = null) {
  if (!isLoggedIn()) {
    window.location.href = "../index.html";
    return false;
  }
  if (requiredRole && getSession().role !== requiredRole) {
    // Salah role → redirect ke dashboard yang tepat
    const role = getSession().role;
    if (role === "admin") window.location.href = "dashboard-admin.html";
    else if (role === "dokter") window.location.href = "dashboard-dokter.html";
    else window.location.href = "../index.html";
    return false;
  }
  return true;
}

// ─── Tampilkan nama user di navbar ───────────────────────────────────────────
export function renderUserInfo(elementId = "user-name") {
  const el = document.getElementById(elementId);
  if (el) el.textContent = getSession().nama || "Pengguna";
}

// ─── Logout: hapus session lalu redirect ─────────────────────────────────────
export function logout() {
  clearSession();
  window.location.href = "../index.html";
}