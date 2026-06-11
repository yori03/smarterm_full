/**
 * api.js — SmartERM Frontend API Client
 * BASE_URL kosong karena frontend & backend dilayani dari server FastAPI yang sama.
 */

const BASE_URL = "";

// ─── Token helper ─────────────────────────────────────────────────────────────
function getToken() {
  return localStorage.getItem("access_token");
}

// ─── Header helper ────────────────────────────────────────────────────────────
function authHeaders(extra = {}) {
  return {
    "Authorization": `Bearer ${getToken()}`,
    "Content-Type": "application/json",
    ...extra,
  };
}

// ─── Fetch terpusat ───────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.detail || `Error ${res.status}`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
}


// =============================================================================
// AUTH
// =============================================================================

/**
 * Login → { access_token, token_type, role, nama_lengkap }
 * FastAPI pakai form-data (OAuth2PasswordRequestForm).
 */
export async function login(username, password) {
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

/** Register admin baru — langsung nonaktif, butuh aktivasi */
export async function registerAdmin(username, password, nama_lengkap) {
  return apiFetch("/register-admin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, nama_lengkap }),
  });
}


// =============================================================================
// ADMIN — DOKTER
// =============================================================================

/** GET /admin/list-dokter → { total, data: [...] } */
export async function listDokter() {
  return apiFetch("/admin/list-dokter", { headers: authHeaders() });
}

/**
 * POST /admin/create-dokter
 * Body: { username, password, nama_lengkap, spesialisasi, no_str }
 */
export async function createDokter(data) {
  return apiFetch("/admin/create-dokter", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}

/**
 * PUT /admin/edit-dokter/{user_id}
 * Body (opsional semua): { nama_lengkap, username, spesialisasi, no_str, is_active, password }
 */
export async function editDokter(user_id, data) {
  return apiFetch(`/admin/edit-dokter/${user_id}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}

/**
 * DELETE /admin/hapus-dokter/{user_id}
 * Jika punya rekam medis → nonaktif. Jika tidak → hapus permanen.
 */
export async function hapusDokter(user_id) {
  return apiFetch(`/admin/hapus-dokter/${user_id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}


// =============================================================================
// ADMIN — ADMIN
// =============================================================================

/** GET /admin/list-admin → { total, data: [...] } */
export async function listAdmin() {
  return apiFetch("/admin/list-admin", { headers: authHeaders() });
}

/**
 * POST /admin/create-admin
 * Body: { username, password, nama_lengkap }
 */
export async function createAdmin(data) {
  return apiFetch("/admin/create-admin", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}

/**
 * PUT /admin/edit-admin/{user_id}
 * Body (opsional semua): { nama_lengkap, username, is_active, password }
 */
export async function editAdmin(user_id, data) {
  return apiFetch(`/admin/edit-admin/${user_id}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}

/**
 * DELETE /admin/hapus-admin/{user_id}
 * Permanen. Tidak bisa hapus diri sendiri (dicegah backend).
 */
export async function hapusAdmin(user_id) {
  return apiFetch(`/admin/hapus-admin/${user_id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}


// =============================================================================
// ADMIN — PENDING AKTIVASI
// =============================================================================

/** GET /admin/pending-aktivasi → { total_pending, data: [...] } */
export async function pendingAktivasi() {
  return apiFetch("/admin/pending-aktivasi", { headers: authHeaders() });
}

/** PUT /admin/activate/{user_id} */
export async function aktivasiUser(user_id) {
  return apiFetch(`/admin/activate/${user_id}`, {
    method: "PUT",
    headers: authHeaders(),
  });
}


// =============================================================================
// DOKTER — PASIEN
// =============================================================================

/** POST /dokter/pasien → daftarkan pasien baru */
export async function daftarPasien(data) {
  return apiFetch("/dokter/pasien", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}

/** GET /dokter/pasien/{no_rekam_medis} → { data_pasien, total_kunjungan, riwayat_berobat } */
export async function getPasien(no_rekam_medis) {
  return apiFetch(`/dokter/pasien/${encodeURIComponent(no_rekam_medis)}`, {
    headers: authHeaders(),
  });
}

/** GET /dokter/cari-pasien?nama=... → { total, data: [...] } */
export async function cariPasien(nama) {
  return apiFetch(`/dokter/cari-pasien?nama=${encodeURIComponent(nama)}`, {
    headers: authHeaders(),
  });
}


// =============================================================================
// MEDICAL — AI & REKAM MEDIS
// =============================================================================

/** POST /medical/transcribe — upload audio */
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

/** POST /medical/simpan-rm */
export async function simpanRekamMedis(data) {
  return apiFetch("/medical/simpan-rm", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}

/** GET /medical/rekam-medis/{id_record} */
export async function getRekamMedis(id_record) {
  return apiFetch(`/medical/rekam-medis/${id_record}`, {
    headers: authHeaders(),
  });
}