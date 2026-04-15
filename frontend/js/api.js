/* ── API Wrapper ──────────────────────────────────────── */
const api = {
  async request(method, path, body = null, silent = false) {
    const url = CONFIG.API_BASE_URL.replace(/\/$/, "") + path;
    const headers = { "Content-Type": "application/json" };
    const token = localStorage.getItem(CONFIG.TOKEN_KEY);
    if (token) headers["Authorization"] = "Bearer " + token;

    const startTime = Date.now();
    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    try {
      const res = await fetch(url, options);
      const elapsed = Date.now() - startTime;
      let data = {};
      try { data = await res.json(); } catch (e) { /* empty body */ }

      logApiCall(method, path, res.status, elapsed);

      if (!res.ok) {
        if (!silent) showToast(data.error || `Error ${res.status}`, "error");
        const err = new Error(data.error || `HTTP ${res.status}`);
        err.status = res.status;
        err.data = data;
        throw err;
      }
      if (!silent) showToast(`${method} ${path} \u2192 ${res.status} (${elapsed}ms)`, "success");
      return data;
    } catch (err) {
      if (!err.status) {
        logApiCall(method, path, 0, Date.now() - startTime);
        if (!silent) showToast("Network error", "error");
      }
      throw err;
    }
  },

  get(path, silent) { return this.request("GET", path, null, silent); },
  post(path, body) { return this.request("POST", path, body); },
  put(path, body, silent) { return this.request("PUT", path, body, silent); },
  del(path, silent) { return this.request("DELETE", path, null, silent); },
};

/* ── S3 Direct Upload ─────────────────────────────────── */
async function uploadToS3(presignedUrl, file, contentType) {
  try {
    const res = await fetch(presignedUrl, {
      method: "PUT",
      body: file,
      headers: { "Content-Type": contentType },
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      console.error("S3 upload error:", res.status, text);
      showToast("S3 upload failed: " + res.status, "error");
      throw new Error("S3 upload failed: " + res.status);
    }
    return true;
  } catch (err) {
    if (!err.message.includes("S3 upload failed")) {
      console.error("S3 upload CORS/network error:", err);
      showToast("S3 upload error (CORS/network): " + err.message, "error");
    }
    throw err;
  }
}

/* ── API Activity Log ─────────────────────────────────── */
function logApiCall(method, path, status, elapsed) {
  const entries = document.getElementById("api-log-entries");
  if (!entries) return;

  const now = new Date();
  const ts = now.toLocaleTimeString("en-US", { hour12: false });
  const statusClass = status >= 400 || status === 0 ? "status-err" : "status-ok";

  const entry = document.createElement("div");
  entry.className = "api-log-entry";
  entry.innerHTML = `
    <span class="ts">[${ts}]</span>
    <span class="method">${method}</span>
    <span class="path">${path}</span>
    <span class="${statusClass}">${status || "ERR"}</span>
    <span class="time">${elapsed}ms</span>`;
  entries.prepend(entry);

  const countEl = document.getElementById("api-log-count");
  if (countEl) countEl.textContent = entries.children.length;
}
