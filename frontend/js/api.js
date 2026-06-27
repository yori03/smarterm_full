/**
 * api.js — SmartERM Frontend API Client
 BASE_URL kosong karena frontend & backend dilayani dari server FastAPI yang sama.
 */

const BASE_URL = "";
function getToken() {
  return localStorage.getItem("access_token");
}
function authHeaders(extra = {}) {
  return {
    "Authorization": `Bearer ${getToken()}`,
    "Content-Type": "application/json",
    ...extra,
  };
}export async function login(username, password) {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);
  const res = await fetch(`${BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Login gagal");
  return data;
}
export async function registerAdmin(username, password, nama_lengkap) {
  return apiFetch("/register-admin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, nama_lengkap }),
  });
}
export async function listDokter() {
  return apiFetch("/admin/list-dokter", { headers: authHeaders() });
}
export async function createDokter(data) {
  return apiFetch("/admin/create-dokter", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}
export async function editDokter(user_id, data) {
  return apiFetch(`/admin/edit-dokter/${user_id}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}
export async function hapusDokter(user_id) {
  return apiFetch(`/admin/hapus-dokter/${user_id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}
export async function listAdmin() {
  return apiFetch("/admin/list-admin", { headers: authHeaders() });
}
export async function createAdmin(data) {
  return apiFetch("/admin/create-admin", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}
export async function editAdmin(user_id, data) {
  return apiFetch(`/admin/edit-admin/${user_id}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}
export async function hapusAdmin(user_id) {
  return apiFetch(`/admin/hapus-admin/${user_id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}
export async function pendingAktivasi() {
  return apiFetch("/admin/pending-aktivasi", { headers: authHeaders() });
}
export async function aktivasiUser(user_id) {
  return apiFetch(`/admin/activate/${user_id}`, {
    method: "PUT",
    headers: authHeaders(),
  });
}
export async function daftarPasien(data) {
  return apiFetch("/dokter/pasien", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}
export async function getPasien(no_rekam_medis) {
  return apiFetch(`/dokter/pasien/${encodeURIComponent(no_rekam_medis)}`, {
    headers: authHeaders(),
  });
}
export async function cariPasien(nama) {
  return apiFetch(`/dokter/cari-pasien?nama=${encodeURIComponent(nama)}`, {
    headers: authHeaders(),
  });
}
export async function transcribeAudio(audioBlob, filename = "rekaman.webm") {
  const token = getToken();
  const form = new FormData();
  form.append("file", audioBlob, filename);
  const res = await fetch(`${BASE_URL}/medical/transcribe`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Transkripsi gagal");
  return data;
}
export async function simpanRekamMedis(data) {
  return apiFetch("/medical/simpan-rm", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}
export async function getRekamMedis(id_record) {
  return apiFetch(`/medical/rekam-medis/${id_record}`, {
    headers: authHeaders(),
  });
}