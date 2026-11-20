// Komek Teacher frontend: simple hash router + page renderers.
const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const view = () => $("#view");
let ME = null;

// Numeric date (browsers lack Kazakh month names, which showed up as "M11").
function fmtDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
function fmtSize(b) { return b > 1048576 ? (b / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1024)) + " KB"; }
function formData(form) { return Object.fromEntries(new FormData(form).entries()); }
function emptyToNull(o) { for (const k in o) if (o[k] === "") o[k] = null; return o; }

function showModal(html) {
  const bg = document.createElement("div");
  bg.className = "modal-bg";
  bg.innerHTML = `<div class="modal">${html}<div class="actions"><button class="btn" data-close>${t("close")}</button></div></div>`;
  bg.addEventListener("click", (e) => { if (e.target === bg || e.target.dataset.close !== undefined) bg.remove(); });
  document.body.appendChild(bg);
}

// ---------------- Auth ----------------
let authMode = "login";
function renderAuth() {
  $("#app").classList.add("hidden");
  $("#auth-screen").classList.remove("hidden");
  const reg = authMode === "register";
  document.querySelectorAll(".reg-only").forEach((el) => el.classList.toggle("hidden", !reg));
  $("#auth-title").textContent = t(reg ? "register" : "login");
  $("#auth-submit").textContent = t(reg ? "register" : "login");
  $("#auth-switch-text").textContent = t(reg ? "haveAccount" : "noAccount");
  $("#auth-switch").textContent = t(reg ? "login" : "register");
  $("#auth-error").textContent = "";
}

$("#auth-switch").addEventListener("click", (e) => { e.preventDefault(); authMode = authMode === "login" ? "register" : "login"; renderAuth(); });
$("#auth-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = emptyToNull(formData(e.target));
  try {
    const res = authMode === "register"
      ? await API.post("/api/auth/register", { ...data, language: LANG })
      : await API.post("/api/auth/login", { email: data.email, password: data.password });
    API.setToken(res.token);
    ME = res.teacher;
    location.hash = "#/home";
    route();
  } catch (err) { $("#auth-error").textContent = err.message; }
});
$("#logout-btn").addEventListener("click", async () => {
  try { await API.post("/api/auth/logout"); } catch {}
  API.setToken(null); ME = null; location.hash = "#/login"; route();
});

// ---------------- Pages ----------------
const pages = {
  async home() {
    const d = await API.get("/api/dashboard");
    view().innerHTML = `
      <div class="card hero">
        <div class="ic purple">✦</div>
        <div><h2>${esc(t("welcome", { name: ME.full_name }))} 👋</h2><p class="muted" style="margin:0">${t("welcomeSub")}</p>
          <div class="chips"><span class="chip">${d.lessons} ${t("statLessons")}</span><span class="chip">${d.assignments} ${t("statAssignments")}</span><span class="chip">${d.materials} ${t("statMaterials")}</span></div>
        </div>
      </div>
      <div class="section-title">✦ ${t("aiTools")}</div>
      <div class="grid">
        <div class="card tool" data-go="#/ai?tab=plan"><div class="ic purple">▤</div><b>${t("toolLessonPlan")}</b><span class="muted">${t("toolLessonPlanDesc")}</span></div>
        <div class="card tool" data-go="#/ai?tab=quiz"><div class="ic blue">✎</div><b>${t("toolQuiz")}</b><span class="muted">${t("toolQuizDesc")}</span></div>
        <div class="card tool" data-go="#/materials"><div class="ic green">⧉</div><b>${t("toolMaterials")}</b><span class="muted">${t("toolMaterialsDesc")}</span></div>
      </div>
      <div class="card"><div class="section-title">🗓 ${t("upcoming")}</div>
        ${d.upcoming.length ? d.upcoming.map((l) => `<div class="list-item"><div class="grow"><b>${esc(l.title)}</b><div class="meta">${fmtDate(l.scheduled_at)} · ${esc(l.subject || "")} · ${esc(l.grade || "")}</div></div></div>`).join("") : `<p class="muted">${t("nothingYet")}</p>`}
      </div>`;
    view().querySelectorAll("[data-go]").forEach((el) => el.addEventListener("click", () => (location.hash = el.dataset.go)));
  },

  async ai(params) {
    const tab = params.get("tab") || "plan";
    const status = await API.get("/api/ai/status");
    const langSelect = `<label>${t("outputLang")}</label><select name="language"><option value="kk" ${LANG === "kk" ? "selected" : ""}>Қазақша</option><option value="ru" ${LANG === "ru" ? "selected" : ""}>Русский</option></select>`;
    const common = `
      <div><label>${t("subject")}</label><input name="subject" required value="${esc(ME.subject || "")}"></div>
      <div><label>${t("grade")}</label><input name="grade" required placeholder="7"></div>
      <div style="grid-column:1/-1"><label>${t("topic")}</label><input name="topic" required></div>`;
    const planForm = `
      <div class="form-grid">${common}
        <div><label>${t("duration")}</label><input name="duration_min" type="number" value="45" min="10" max="180"></div>
        <div>${langSelect}</div>
        <div style="grid-column:1/-1"><label>${t("notes")}</label><textarea name="notes"></textarea></div>
      </div>`;
    const quizForm = `
      <div class="form-grid">${common}
        <div><label>${t("kind")}</label><select name="kind"><option value="quiz">${t("quiz")}</option><option value="homework">${t("homework")}</option><option value="test">${t("test")}</option></select></div>
        <div><label>${t("count")}</label><input name="count" type="number" value="5" min="1" max="30"></div>
        <div><label>${t("difficulty")}</label><select name="difficulty"><option value="easy">${t("easy")}</option><option value="medium" selected>${t("medium")}</option><option value="hard">${t("hard")}</option></select></div>
        <div>${langSelect}</div>
      </div>`;
    view().innerHTML = `
      <div class="toolbar"><h2>✦ ${t("navAI")}</h2><span class="chip">${t("aiMode")}: ${esc(status.mode)}</span></div>
      <div class="tabs"><button class="btn ${tab === "plan" ? "active" : ""}" data-tab="plan">${t("toolLessonPlan")}</button><button class="btn ${tab === "quiz" ? "active" : ""}" data-tab="quiz">${t("toolQuiz")}</button></div>
      <div class="two-col">
        <form class="card" id="ai-form">${tab === "plan" ? planForm : quizForm}
          <div class="actions"><button class="btn primary" id="gen-btn">${t("generate")}</button></div>
          <p class="error" id="ai-error"></p>
        </form>
        <div class="card"><div class="section-title">${t("result")}</div><div class="output" id="ai-out"><span class="muted">—</span></div>
          <div class="actions"><button class="btn hidden" id="save-btn">${t("saveToLibrary")}</button></div></div>
      </div>`;
    view().querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => (location.hash = `#/ai?tab=${b.dataset.tab}`)));

    let lastReq = null;
    const endpoint = tab === "plan" ? "/api/ai/lesson-plan" : "/api/ai/assignment";
    $("#ai-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = $("#gen-btn");
      const req = formData(e.target);
      ["duration_min", "count"].forEach((k) => { if (req[k]) req[k] = Number(req[k]); });
      btn.disabled = true; btn.textContent = t("generating"); $("#ai-error").textContent = "";
      try {
        const res = await API.post(endpoint, { ...req, save: false });
        $("#ai-out").textContent = res.content;
        lastReq = req;
        $("#save-btn").classList.remove("hidden");
        $("#save-btn").disabled = false;
        $("#save-btn").textContent = t("saveToLibrary");
        $("#save-btn").dataset.content = res.content;
      } catch (err) { $("#ai-error").textContent = err.message; }
      btn.disabled = false; btn.textContent = t("generate");
    });
    // Save the already-generated text (no second AI call).
    $("#save-btn").addEventListener("click", async (e) => {
      const content = e.target.dataset.content;
      if (tab === "plan") {
        await API.post("/api/lessons", { title: lastReq.topic, subject: lastReq.subject, grade: lastReq.grade, topic: lastReq.topic, duration_min: lastReq.duration_min || 45, plan: content });
      } else {
        await API.post("/api/assignments", { title: lastReq.topic, kind: lastReq.kind, content });
      }
      e.target.textContent = t("saved"); e.target.disabled = true;
    });
  },

  async lessons() {
    const items = await API.get("/api/lessons");
    view().innerHTML = `
      <div class="toolbar"><h2>${t("navLessons")}</h2><button class="btn primary" id="add">+ ${t("newLesson")}</button></div>
      <form class="card hidden" id="new-form"><div class="form-grid">
        <div style="grid-column:1/-1"><label>${t("title")}</label><input name="title" required></div>
        <div><label>${t("subject")}</label><input name="subject" value="${esc(ME.subject || "")}"></div>
        <div><label>${t("grade")}</label><input name="grade"></div>
        <div><label>${t("scheduledAt")}</label><input name="scheduled_at" type="datetime-local"></div>
        <div style="grid-column:1/-1"><label>${t("plan")}</label><textarea name="plan"></textarea></div>
      </div><div class="actions"><button class="btn primary">${t("create")}</button></div></form>
      <div class="card">${items.length ? items.map((l) => `
        <div class="list-item"><div class="ic purple">▤</div><div class="grow"><b>${esc(l.title)}</b>
          <div class="meta">${esc(l.subject || "")} · ${esc(l.grade || "")} · ${fmtDate(l.scheduled_at)}</div></div>
          <button class="btn sm" data-open="${l.id}">${t("open")}</button><button class="btn sm danger" data-del="${l.id}">${t("delete")}</button></div>`).join("") : `<p class="muted">${t("nothingYet")}</p>`}</div>`;
    $("#add").addEventListener("click", () => $("#new-form").classList.toggle("hidden"));
    $("#new-form").addEventListener("submit", async (e) => { e.preventDefault(); await API.post("/api/lessons", emptyToNull(formData(e.target))); route(); });
    bindRowActions("/api/lessons", items, (l) => `<h2>${esc(l.title)}</h2><div class="output">${esc(l.plan || "—")}</div>`);
  },

  async assignments() {
    const items = await API.get("/api/assignments");
    view().innerHTML = `
      <div class="toolbar"><h2>${t("navAssignments")}</h2><button class="btn primary" id="add">+ ${t("newAssignment")}</button></div>
      <form class="card hidden" id="new-form"><div class="form-grid">
        <div style="grid-column:1/-1"><label>${t("title")}</label><input name="title" required></div>
        <div><label>${t("kind")}</label><select name="kind"><option value="homework">${t("homework")}</option><option value="quiz">${t("quiz")}</option><option value="test">${t("test")}</option></select></div>
        <div><label>${t("dueDate")}</label><input name="due_date" type="datetime-local"></div>
        <div style="grid-column:1/-1"><label>${t("content")}</label><textarea name="content"></textarea></div>
      </div><div class="actions"><button class="btn primary">${t("create")}</button></div></form>
      <div class="card">${items.length ? items.map((a) => `
        <div class="list-item"><div class="ic pink">✎</div><div class="grow"><b>${esc(a.title)}</b>
          <div class="meta">${t(a.kind)} · ${t("dueDate")}: ${fmtDate(a.due_date)}</div></div>
          <button class="btn sm" data-open="${a.id}">${t("open")}</button><button class="btn sm danger" data-del="${a.id}">${t("delete")}</button></div>`).join("") : `<p class="muted">${t("nothingYet")}</p>`}</div>`;
    $("#add").addEventListener("click", () => $("#new-form").classList.toggle("hidden"));
    $("#new-form").addEventListener("submit", async (e) => { e.preventDefault(); await API.post("/api/assignments", emptyToNull(formData(e.target))); route(); });
    bindRowActions("/api/assignments", items, (a) => `<h2>${esc(a.title)}</h2><div class="output">${esc(a.content || "—")}</div>`);
  },

  async materials() {
    const items = await API.get("/api/materials");
    view().innerHTML = `
      <div class="toolbar"><h2>${t("navMaterials")}</h2>
        <label class="btn primary" style="margin:0;color:#fff">⬆ ${t("upload")}<input type="file" id="file" class="hidden"></label></div>
      <p class="error" id="up-error"></p>
      <div class="card">${items.length ? items.map((m) => `
        <div class="list-item"><div class="ic green">⧉</div><div class="grow"><b>${esc(m.original_name)}</b>
          <div class="meta">${fmtSize(m.size_bytes)} · ${fmtDate(m.created_at)}</div></div>
          <button class="btn sm" data-dl="${m.id}">${t("download")}</button><button class="btn sm danger" data-del="${m.id}">${t("delete")}</button></div>`).join("") : `<p class="muted">${t("nothingYet")}</p>`}</div>`;
    $("#file").addEventListener("change", async (e) => {
      const fd = new FormData();
      fd.append("file", e.target.files[0]);
      try { await API.upload("/api/materials", fd); route(); } catch (err) { $("#up-error").textContent = err.message; }
    });
    view().querySelectorAll("[data-dl]").forEach((b) => b.addEventListener("click", () => {
      const m = items.find((x) => x.id == b.dataset.dl); API.download(m.id, m.original_name);
    }));
    bindRowActions("/api/materials", items);
  },
};

function bindRowActions(base, items, renderDetail) {
  view().querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", async () => {
    if (!confirm(t("confirmDelete"))) return;
    await API.del(`${base}/${b.dataset.del}`); route();
  }));
  if (renderDetail) view().querySelectorAll("[data-open]").forEach((b) => b.addEventListener("click", () => {
    showModal(renderDetail(items.find((x) => x.id == b.dataset.open)));
  }));
}

// ---------------- Router ----------------
let pollTimer = null;
function poll(fn, ms = 3000) { clearTimeout(pollTimer); pollTimer = setTimeout(fn, ms); }

async function route() {
  clearTimeout(pollTimer);
  document.querySelectorAll(".modal-bg").forEach((m) => m.remove());
  applyStaticTranslations();
  const [path, query] = (location.hash.replace(/^#\/?/, "") || "home").split("?");
  const [section, arg] = path.split("/");
  // Student page: works without login.
  if (section === "s" && arg) {
    $("#auth-screen").classList.add("hidden");
    $("#app").classList.add("hidden");
    $("#public-screen").classList.remove("hidden");
    return renderStudentPage(arg);
  }
  $("#public-screen").classList.add("hidden");
  if (!API.token) { renderAuth(); return; }
  if (!ME) {
    try { ME = await API.get("/api/auth/me"); } catch { renderAuth(); return; }
  }
  $("#auth-screen").classList.add("hidden");
  $("#app").classList.remove("hidden");
  $("#user-name").textContent = ME.full_name;
  $("#user-avatar").textContent = (ME.full_name || "?")[0].toUpperCase();
  const name = pages[section] ? section : "home";
  const navName = { assignment: "assignments" }[name] || name;
  document.querySelectorAll(".sb-nav a").forEach((a) => {
    a.classList.toggle("active", a.dataset.route === navName);
    a.title = a.textContent.trim(); // tooltip when the menu is collapsed
  });
  try { await pages[name](new URLSearchParams(query || ""), arg); }
  catch (err) { view().innerHTML = `<div class="card"><p class="error">${t("error")}: ${esc(err.message)}</p></div>`; }
}

document.querySelectorAll(".lang-switch button").forEach((b) => b.addEventListener("click", () => {
  setLang(b.dataset.lang);
  if (ME) API.patch("/api/auth/me", { language: LANG }).catch(() => {});
  if (API.token || /^#\/s\/./.test(location.hash)) route(); else renderAuth();
}));

// ---------------- Collapsible sidebar ----------------
const narrow = () => window.matchMedia("(max-width: 700px)").matches;
function setCollapsed(on, remember = true) {
  $("#app").classList.toggle("collapsed", on);
  const btn = $("#collapse-btn");
  btn.title = btn.ariaLabel = on ? "Expand menu" : "Collapse menu";
  if (remember && !narrow()) localStorageSet("sidebarCollapsed", on ? "1" : "0");
}
setCollapsed(narrow() || localStorageGet("sidebarCollapsed") === "1", false);
$("#collapse-btn").addEventListener("click", () => setCollapsed(!$("#app").classList.contains("collapsed")));
// On phones the open menu overlays the page, so close it after picking a section.
document.querySelectorAll(".sb-nav a").forEach((a) => a.addEventListener("click", () => { if (narrow()) setCollapsed(true, false); }));

window.addEventListener("hashchange", route);
setLang(LANG);
// Run after all scripts (checking.js adds more pages) have loaded.
window.addEventListener("DOMContentLoaded", route);
