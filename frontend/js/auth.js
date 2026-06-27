export function saveSession(tokenData) {
  localStorage.setItem("access_token", tokenData.access_token);
  localStorage.setItem("role", tokenData.role);
  localStorage.setItem("nama_lengkap", tokenData.nama_lengkap);
}
export function getSession() {
  return {
    token: localStorage.getItem("access_token"),
    role: localStorage.getItem("role"),
    nama: localStorage.getItem("nama_lengkap")
  };
}
export function isLoggedIn() {
  return !!localStorage.getItem("access_token");
}
export function clearSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("role");
  localStorage.removeItem("nama_lengkap");
}
export function guardPage(requiredRole = null) {
  if (!isLoggedIn()) {
    window.location.href = "../index.html";
    return false;
  }
  if (requiredRole && getSession().role !== requiredRole) {
    const role = getSession().role;
    if (role === "admin") window.location.href = "dashboard-admin.html";
    else if (role === "dokter") window.location.href = "dashboard-dokter.html";
    else window.location.href = "../index.html";
    return false;
  }
  return true;
}
export function renderUserInfo(elementId = "user-name") {
  const el = document.getElementById(elementId);
  if (el) el.textContent = getSession().nama || "Pengguna";
}
export function logout() {
  clearSession();
  window.location.href = "../index.html";
}