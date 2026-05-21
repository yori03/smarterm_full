// * BASE_URL kosong karena frontend dan backend dilayani dari server FastAPI yang sama
const BASE_URL = "";

// ─── Helper: ambil token dari localStorage ───────────────────────────────────
function getToken() {
  return localStorage.getItem("access_token");
}

// ─── Helper: header default dengan token ─────────────────────────────────────
function authHeaders(extraHeaders = {}) {
  return {
    "Authorization": `Bearer ${getToken()}`,
    "Content-Type": "application/json",
    ...extraHeaders
  };
}

// ─── Helper: fetch dengan error handling terpusat ────────────────────────────
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
 * Login untuk admin maupun dokter
 * FastAPI pakai form-data (OAuth2PasswordRequestForm), bukan JSON
 * Response: { access_token, token_type, role, nama_lengkap }
 */
export async function login(username, password) {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);

  const res = await fetch(`${BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Login gagal");
  return data;
}

/**
 * Register admin baru (langsung nonaktif, butuh aktivasi admin lain)
 * Body: { username, password, nama_lengkap }
 */
export async function registerAdmin(username, password, nama_lengkap) {
  return apiFetch("/register-admin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, nama_lengkap })
  });
}

// =============================================================================
// ADMIN
// =============================================================================

/** GET /admin/list-dokter → { total, data: [...] } */
export async function listDokter() {
  return apiFetch("/admin/list-dokter", {
    headers: authHeaders()
  });
}

/** GET /admin/pending-aktivasi → { total_pending, data: [...] } */
export async function pendingAktivasi() {
  return apiFetch("/admin/pending-aktivasi", {
    headers: authHeaders()
  });
}

/** PUT /admin/activate/{user_id} → aktifkan akun */
export async function aktivasiUser(user_id) {
  return apiFetch(`/admin/activate/${user_id}`, {
    method: "PUT",
    headers: authHeaders()
  });
}

/**
 * POST /admin/create-dokter
 * Body: { username, password, nama_lengkap, spesialisasi, no_str }
 */
export async function createDokter(data) {
  return apiFetch("/admin/create-dokter", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data)
  });
}

// =============================================================================
// DOKTER - PASIEN
// =============================================================================

/**
 * POST /dokter/pasien → daftarkan pasien baru
 * Body: CreatePasienSchema
 */
export async function daftarPasien(data) {
  return apiFetch("/dokter/pasien", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data)
  });
}

/** GET /dokter/pasien/{no_rm} → data pasien + riwayat */
export async function getPasien(no_rekam_medis) {
  return apiFetch(`/dokter/pasien/${encodeURIComponent(no_rekam_medis)}`, {
    headers: authHeaders()
  });
}

/** GET /dokter/cari-pasien?nama=... → hasil pencarian */
export async function cariPasien(nama) {
  return apiFetch(`/dokter/cari-pasien?nama=${encodeURIComponent(nama)}`, {
    headers: authHeaders()
  });
}

// =============================================================================
// MEDICAL / AI
// =============================================================================

/**
 * POST /medical/transcribe
 * Upload file audio (multipart/form-data)
 * Response: { status, dokter, transkrip_asli, data_medis }
 * CATATAN: Tidak pakai Content-Type JSON karena ini file upload
 */
export async function transcribeAudio(audioBlob, filename = "rekaman.webm") {
  const formData = new FormData();
  formData.append("file", audioBlob, filename);

  const res = await fetch(`${BASE_URL}/medical/transcribe`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${getToken()}` },
    // Content-Type TIDAK diset manual — browser otomatis set multipart boundary
    body: formData
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Gagal proses AI");
  return data;
}

/**
 * POST /medical/simpan-rm
 * Body: SimpanRMSchema (no_rekam_medis wajib, sisanya optional)
 * Response: { msg, id_record, pasien, dokter, waktu }
 */
export async function simpanRekamMedis(data) {
  return apiFetch("/medical/simpan-rm", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data)
  });
}

/** GET /medical/rekam-medis/{id_record} → detail satu rekam medis */
export async function getRekamMedis(id_record) {
  return apiFetch(`/medical/rekam-medis/${id_record}`, {
    headers: authHeaders()
  });
}