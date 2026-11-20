// Thin wrapper around the backend REST API.
const API = {
  token: localStorageGet("token"),

  setToken(token) {
    this.token = token;
    if (token) localStorageSet("token", token);
    else { try { localStorage.removeItem("token"); } catch {} }
  },

  async request(method, path, body, isForm = false) {
    const headers = {};
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    if (body && !isForm) headers["Content-Type"] = "application/json";
    const res = await fetch(path, {
      method, headers, body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    });
    if (res.status === 401 && path !== "/api/auth/login") {
      this.setToken(null);
      location.hash = "#/login";
    }
    if (!res.ok) {
      let msg = res.statusText;
      try { const j = await res.json(); msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch {}
      throw new Error(msg);
    }
    return res.json();
  },

  get(p) { return this.request("GET", p); },
  post(p, b) { return this.request("POST", p, b); },
  put(p, b) { return this.request("PUT", p, b); },
  patch(p, b) { return this.request("PATCH", p, b); },
  del(p) { return this.request("DELETE", p); },
  upload(p, formData) { return this.request("POST", p, formData, true); },

  async blobUrl(path) {
    const res = await fetch(path, { headers: { Authorization: `Bearer ${this.token}` } });
    if (!res.ok) throw new Error(res.statusText);
    return URL.createObjectURL(await res.blob());
  },

  async download(id, name) {
    const res = await fetch(`/api/materials/${id}/download`, { headers: { Authorization: `Bearer ${this.token}` } });
    if (!res.ok) throw new Error(res.statusText);
    const url = URL.createObjectURL(await res.blob());
    const a = Object.assign(document.createElement("a"), { href: url, download: name });
    a.click();
    URL.revokeObjectURL(url);
  },
};
