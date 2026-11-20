// «Қатысу» — class journal + face recognition on one class photo (runs locally on the server).
// 1) Enroll: with parental consent, add 2–3 face photos per student.
// 2) Lesson: take one class photo → faces are matched to enrolled students → write result into the journal.
// Depends on app.js / checking.js helpers: $, esc, t, API, pages, view, showModal, poll, infoTip.

Object.assign(I18N.kk, {
  navAttendance: "Қатысу",
  rcNew: "Жаңа сабақ",
  rcTitle: "Сынып / сабақ",
  rcTitlePh: "Мысалы: 8А · Алгебра",
  rcUsePrev: "Бұрынғы тізімді алу",
  rcUsePrevNone: "— жаңа тізім —",
  rcDate: "Күні",
  rcRoster: "Оқушылар тізімі (әр жолға бір оқушы)",
  rcRosterPh: "Әлиев Әли\nБекова Айдана\nДәулетов Дамир",
  rcRosterCount: "{n} оқушы",
  rcCreate: "Журналды ашу",
  rcEmptyRoster: "Тізімге кемінде бір оқушы жазыңыз",
  rcEmptyTitle: "Әзірге журнал жоқ",
  rcEmptyText: "Сабақ ашып, сынып тізімін енгізіңіз. Оқушылардың беттерін бір рет тіркесеңіз, кейін бір сынып фотосымен кім бар, кім жоқ екені бірден анықталады.",
  rcBack: "← Қатысу",
  rcOnList: "Тізімде",
  rcRecognized: "Танылды",
  rcUnknownFaces: "Танылмаған бет",
  rcEnrolled: "Беті тіркелген",
  rcNoPhoto: "Сынып фотосын түсіріңіз — жүйе беті тіркелген оқушыларды таниды.",
  rcBusy: "Беттер танылып жатыр...",
  rcNoEnrolled: "Әлі ешбір оқушының беті тіркелмеген. Төмендегі «Беттерді тіркеу» бөлімінде фото қосыңыз.",
  rcResult: "Танылды: {r} оқушы.",
  rcNotSeen: "Фотода жоқ: {names}",
  rcApply: "✓ Нәтижені журналға жазу",
  rcApplied: "Журнал жаңартылды",
  rcNotEnrolledNote: "Беті тіркелмегендер ({n}) журналда өзгертілмеді — оларды өзіңіз белгілеңіз.",
  rcPhotoCard: "Сынып фотосы",
  rcPhotoTip: "Тақтаның алдынан, бүкіл сыныпқа қарап түсіріңіз: әр оқушының беті көрінуі керек. Үлкен сынып болса 2 фото жүктеңіз. Фото тек осы компьютерде өңделеді.",
  rcShoot: "📷 Түсіру",
  rcUpload: "🖼 Файлдан жүктеу",
  rcMaxPhotos: "Ең көбі 3 фото",
  rcFacesFound: "{n} бет",
  rcRecount: "Қайта тану",
  rcClickFace: "Бетті бассаңыз, кім екенін өзіңіз көрсете аласыз.",
  rcWhoIsThis: "Бұл кім?",
  rcNotStudent: "— оқушы емес / белгісіз —",
  rcLearn: "Бұл бетті оқушының үлгісіне қосу (келесіде жақсырақ танылады)",
  rcJournal: "Журнал",
  rcAllPresent: "Барлығы келді",
  rcEditRoster: "Тізімді өзгерту",
  rcSave: "Сақтау",
  rcPresent: "Келді", rcLate: "Кешікті", rcAbsent: "Келмеді",
  rcSeen: "фотода бар",
  rcEnroll: "Беттерді тіркеу",
  rcEnrollTip: "Әр оқушыдан 2–3 фото: бет тура қарап тұрсын, жарық жақсы болсын. Толық фото сақталмайды — тек 128 саннан тұратын бет үлгісі мен кішкентай сурет. Деректер тек осы компьютерде.",
  rcConsent: "Ата-ана келісімі бар",
  rcConsentWarn: "Биометриялық деректерді (бет суретін) тек ата-ананың жазбаша келісімімен сақтауға болады. Келісімді алып тастасаңыз, бұл оқушының бет деректері өшіріледі.",
  rcConsentOffConfirm: "Келісімді алып тастасаңыз, бұл оқушының бет деректері толық өшіріледі. Жалғастырасыз ба?",
  rcAddFace: "+ Фото",
  rcNeedConsent: "Алдымен келісімді белгілеңіз",
  rcWipeAll: "Барлық бет деректерін өшіру",
  rcWipeConfirm: "Барлық оқушылардың бет деректері мен келісім белгілері толық өшіріледі. Қайтару мүмкін емес. Жалғастырасыз ба?",
  rcModelsMissing: "Бетті тану модельдері табылмады (backend/models/face).",
  err_no_face: "Фотодан бет табылмады. Бет анық көрінетін фото жүктеңіз.",
  err_many_faces: "Фотода бір ғана оқушы болуы керек.",
  err_no_consent: "Алдымен ата-ана келісімін белгілеңіз.",
  err_too_many_samples: "Бір оқушыға ең көбі 5 фото.",
  err_models_missing: "Бетті тану модельдері табылмады.",
});
Object.assign(I18N.ru, {
  navAttendance: "Посещаемость",
  rcNew: "Новый урок",
  rcTitle: "Класс / урок",
  rcTitlePh: "Например: 8А · Алгебра",
  rcUsePrev: "Взять прошлый список",
  rcUsePrevNone: "— новый список —",
  rcDate: "Дата",
  rcRoster: "Список учеников (по одному в строке)",
  rcRosterPh: "Алиев Али\nБекова Айдана\nДаулетов Дамир",
  rcRosterCount: "{n} учеников",
  rcCreate: "Открыть журнал",
  rcEmptyRoster: "Впишите в список хотя бы одного ученика",
  rcEmptyTitle: "Пока нет журналов",
  rcEmptyText: "Откройте урок и введите список класса. Один раз зарегистрируйте лица учеников — потом по одному фото класса сразу видно, кто есть, а кого нет.",
  rcBack: "← Посещаемость",
  rcOnList: "В списке",
  rcRecognized: "Узнаны",
  rcUnknownFaces: "Неузнанные лица",
  rcEnrolled: "Лицо зарегистрировано",
  rcNoPhoto: "Сфотографируйте класс — система узнает учеников с зарегистрированным лицом.",
  rcBusy: "Распознаю лица...",
  rcNoEnrolled: "Ещё ни у кого не зарегистрировано лицо. Добавьте фото в разделе «Регистрация лиц» ниже.",
  rcResult: "Узнано учеников: {r}.",
  rcNotSeen: "Нет на фото: {names}",
  rcApply: "✓ Записать результат в журнал",
  rcApplied: "Журнал обновлён",
  rcNotEnrolledNote: "Ученики без зарегистрированного лица ({n}) в журнале не изменены — отметьте их сами.",
  rcPhotoCard: "Фото класса",
  rcPhotoTip: "Снимайте от доски, лицом к классу: лицо каждого ученика должно быть видно. Для большого класса — 2 фото. Фото обрабатывается только на этом компьютере.",
  rcShoot: "📷 Снять",
  rcUpload: "🖼 Загрузить файл",
  rcMaxPhotos: "Не больше 3 фото",
  rcFacesFound: "{n} лиц",
  rcRecount: "Распознать заново",
  rcClickFace: "Нажмите на лицо, чтобы указать, кто это.",
  rcWhoIsThis: "Кто это?",
  rcNotStudent: "— не ученик / неизвестно —",
  rcLearn: "Добавить это лицо в образец ученика (в следующий раз узнает лучше)",
  rcJournal: "Журнал",
  rcAllPresent: "Все пришли",
  rcEditRoster: "Изменить список",
  rcSave: "Сохранить",
  rcPresent: "Пришёл", rcLate: "Опоздал", rcAbsent: "Нет",
  rcSeen: "есть на фото",
  rcEnroll: "Регистрация лиц",
  rcEnrollTip: "2–3 фото на ученика: лицо прямо, хороший свет. Полное фото не хранится — только образец лица из 128 чисел и маленькая картинка. Данные только на этом компьютере.",
  rcConsent: "Есть согласие родителей",
  rcConsentWarn: "Биометрические данные (фото лица) можно хранить только с письменного согласия родителей. Если снять согласие, данные лица ученика удаляются.",
  rcConsentOffConfirm: "Если снять согласие, данные лица этого ученика будут полностью удалены. Продолжить?",
  rcAddFace: "+ Фото",
  rcNeedConsent: "Сначала отметьте согласие",
  rcWipeAll: "Удалить все данные лиц",
  rcWipeConfirm: "Будут полностью удалены данные лиц и отметки согласия всех учеников. Восстановить нельзя. Продолжить?",
  rcModelsMissing: "Модели распознавания лиц не найдены (backend/models/face).",
  err_no_face: "На фото не найдено лицо. Загрузите фото, где лицо хорошо видно.",
  err_many_faces: "На фото должен быть только один ученик.",
  err_no_consent: "Сначала отметьте согласие родителей.",
  err_too_many_samples: "Не больше 5 фото на ученика.",
  err_models_missing: "Модели распознавания лиц не найдены.",
});

const RC_STATUSES = [["present", "✓", "rcPresent"], ["late", "⏰", "rcLate"], ["absent", "✕", "rcAbsent"]];
const rcPad = (n) => String(n).padStart(2, "0");
const rcToday = () => { const d = new Date(); return `${d.getFullYear()}-${rcPad(d.getMonth() + 1)}-${rcPad(d.getDate())}`; };
const rcDate = (d) => { const x = new Date(d); return `${rcPad(x.getDate())}.${rcPad(x.getMonth() + 1)}.${x.getFullYear()}`; };
const rcErr = (m) => (I18N[LANG]?.["err_" + m] || I18N.kk["err_" + m] ? t("err_" + m) : m);
const shortName = (n) => { const p = n.split(/\s+/); return p.length > 1 ? `${p[1]} ${p[0][0]}.` : n; };

// ------------------------------------------------------------------ list + create
pages.attendance = async function (_params, id) {
  if (id) return rcDetail(id);
  const [items, prev] = await Promise.all([API.get("/api/rollcall"), API.get("/api/rollcall/rosters")]);
  view().innerHTML = `
   <div class="apple-page">
    <div class="page-head"><h2>${t("navAttendance")}</h2><button class="btn primary" id="rc-add">+ ${t("rcNew")}</button></div>
    <form class="card hidden" id="rc-form" novalidate>
      ${prev.length ? `<label>${t("rcUsePrev")}</label><select id="rc-prev"><option value="">${t("rcUsePrevNone")}</option>
        ${prev.map((p, i) => `<option value="${i}">${esc(p.title)} · ${t("rcRosterCount", { n: p.roster.length })}</option>`).join("")}</select>` : ""}
      <div class="form-grid">
        <div><label>${t("rcTitle")}</label><input name="title" required maxlength="200" placeholder="${esc(t("rcTitlePh"))}"></div>
        <div><label>${t("rcDate")}</label><input name="lesson_date" type="date" required value="${rcToday()}"></div>
      </div>
      <label>${t("rcRoster")} · <span id="rc-count">${t("rcRosterCount", { n: 0 })}</span></label>
      <textarea name="roster" rows="9" placeholder="${esc(t("rcRosterPh"))}"></textarea>
      <div class="actions"><button class="btn primary">${t("rcCreate")}</button></div>
      <p class="error" id="rc-err"></p>
    </form>
    ${items.length ? `<div class="grid">${items.map((s) => `
      <div class="card tool" data-go="#/attendance/${s.id}">
        <div class="ic teal">✓</div><b>${esc(s.title)}</b><span class="muted">${rcDate(s.lesson_date)}</span>
        <div class="chips"><span class="chip ok">${t("rcPresent")}: ${s.present}/${s.total}</span>
          ${s.absent ? `<span class="chip miss-chip">${t("rcAbsent")}: ${s.absent}</span>` : ""}
          ${s.faces_total !== null ? `<span class="chip ai-chip">📷 ${t("rcRecognized")}: ${s.recognized.length}</span>` : ""}</div>
      </div>`).join("")}</div>` : `
      <div class="card empty-state" id="rc-empty">
        <div class="ic teal big">✓</div><h3>${t("rcEmptyTitle")}</h3><p class="muted">${t("rcEmptyText")}</p>
        <button class="btn primary" id="rc-add-empty">+ ${t("rcNew")}</button>
      </div>`}
   </div>`;

  const form = $("#rc-form");
  const names = () => form.roster.value.split("\n").map((x) => x.trim()).filter(Boolean);
  const recount = () => { $("#rc-count").textContent = t("rcRosterCount", { n: names().length }); };
  const toggle = () => {
    form.classList.toggle("hidden");
    $("#rc-empty")?.classList.toggle("hidden", !form.classList.contains("hidden"));
    if (!form.classList.contains("hidden")) form.title.focus();
  };
  $("#rc-add").addEventListener("click", toggle);
  $("#rc-add-empty")?.addEventListener("click", toggle);
  form.roster.addEventListener("input", recount);
  $("#rc-prev")?.addEventListener("change", (e) => {
    const p = prev[Number(e.target.value)];
    if (!p) return;
    form.title.value = p.title; form.roster.value = p.roster.join("\n"); recount();
  });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!form.title.value.trim()) { form.title.focus(); return; }
    if (!names().length) { $("#rc-err").textContent = t("rcEmptyRoster"); return; }
    try {
      const s = await API.post("/api/rollcall", { title: form.title.value.trim(), lesson_date: `${form.lesson_date.value}T00:00`, roster: names() });
      location.hash = `#/attendance/${s.id}`;
    } catch (err) { $("#rc-err").textContent = err.message === "empty_roster" ? t("rcEmptyRoster") : err.message; }
  });
  view().querySelectorAll("[data-go]").forEach((el) => el.addEventListener("click", () => (location.hash = el.dataset.go)));
};

// ------------------------------------------------------------------ one lesson
async function rcDetail(id) {
  let s = await API.get(`/api/rollcall/${id}`);
  const urls = {}; // blob URLs for photos / face thumbnails (they need the login token)
  const blob = async (key, path) => (urls[key] = urls[key] || await API.blobUrl(path));
  let appliedNote = "";

  view().innerHTML = `
   <div class="apple-page">
    <a href="#/attendance" class="back-link">${t("rcBack")}</a>
    <div class="page-head"><div><h2>${esc(s.title)}</h2><span class="muted">${rcDate(s.lesson_date)}</span></div>
      <button class="btn danger sm" id="rc-del">${t("delete")}</button></div>
    ${s.models_ready ? "" : `<div class="rc-verdict rc-warn">⚠ ${t("rcModelsMissing")}</div>`}
    <div class="rc-compare" id="rc-compare"></div>
    <section class="card">
      <div class="step-title"><h3>${t("rcPhotoCard")}</h3>${infoTip("rc-tip", `<p>${t("rcPhotoTip")}</p>`)}</div>
      <div class="rc-upload" id="rc-upload">
        <label class="btn primary">${t("rcShoot")}<input type="file" accept="image/*" capture="environment" class="hidden" id="rc-shoot"></label>
        <label class="btn">${t("rcUpload")}<input type="file" accept="image/*,.heic,.heif" class="hidden" id="rc-file"></label>
      </div>
      <p class="error" id="rc-photo-err"></p>
      <div id="rc-photos"></div>
    </section>
    <section class="card">
      <div class="att-table-head"><h3>${t("rcJournal")}</h3>
        <div class="att-head-actions">
          <button class="btn sm" id="rc-all">✓ ${t("rcAllPresent")}</button>
          <button class="btn sm" id="rc-edit">${t("rcEditRoster")}</button>
          <button class="btn sm" id="rc-csv">⬇ ${t("exportCsv")}</button>
        </div></div>
      <div class="rc-edit hidden" id="rc-edit-box">
        <textarea rows="8" id="rc-edit-text"></textarea>
        <div class="actions"><button class="btn primary sm" id="rc-edit-save">${t("rcSave")}</button></div>
      </div>
      <div id="rc-list"></div>
      <p class="error" id="rc-list-err"></p>
    </section>
    <section class="card">
      <div class="att-table-head"><div class="step-title" style="margin:0"><h3>${t("rcEnroll")}</h3>${infoTip("rc-enroll-tip", `<p>${t("rcEnrollTip")}</p><div class="info-warn"><p>${t("rcConsentWarn")}</p></div>`)}</div>
        <span class="chip" id="rc-enrolled-chip"></span></div>
      <div id="rc-enroll"></div>
      <p class="error" id="rc-enroll-err"></p>
      <div class="rc-danger"><button class="btn sm danger" id="rc-wipe">${t("rcWipeAll")}</button></div>
    </section>
   </div>`;

  $("#rc-del").addEventListener("click", async () => {
    if (!confirm(t("confirmDelete"))) return;
    await API.del(`/api/rollcall/${id}`); location.hash = "#/attendance";
  });

  // ---- class photo upload
  async function uploadClass(file) {
    if (!file) return;
    $("#rc-photo-err").textContent = ""; appliedNote = "";
    const fd = new FormData(); fd.append("file", file, file.name || "class.jpg");
    try { await API.upload(`/api/rollcall/${id}/photos`, fd); }
    catch (err) { $("#rc-photo-err").textContent = err.message === "too_many_photos" ? t("rcMaxPhotos") : err.message; }
    await refresh(true);
  }
  ["#rc-shoot", "#rc-file"].forEach((sel) => $(sel).addEventListener("change", (e) => { uploadClass(e.target.files[0]); e.target.value = ""; }));

  // ---- journal actions
  async function setMarks(marks) {
    try { s = await API.put(`/api/rollcall/${id}/marks`, { marks }); } catch (err) { $("#rc-list-err").textContent = err.message; }
    renderAll();
  }
  $("#rc-all").addEventListener("click", () => setMarks(Object.fromEntries(s.roster.map((r) => [r.name, "present"]))));
  $("#rc-edit").addEventListener("click", () => {
    $("#rc-edit-box").classList.toggle("hidden");
    $("#rc-edit-text").value = s.roster.map((r) => r.name).join("\n");
  });
  $("#rc-edit-save").addEventListener("click", async () => {
    const roster = $("#rc-edit-text").value.split("\n").map((x) => x.trim()).filter(Boolean);
    if (!roster.length) { $("#rc-list-err").textContent = t("rcEmptyRoster"); return; }
    try { s = await API.put(`/api/rollcall/${id}`, { title: s.title, lesson_date: s.lesson_date, roster }); $("#rc-edit-box").classList.add("hidden"); }
    catch (err) { $("#rc-list-err").textContent = err.message; }
    renderAll();
  });
  $("#rc-csv").addEventListener("click", () => {
    const label = Object.fromEntries(RC_STATUSES.map(([k, , key]) => [k, t(key)]));
    const rows = [["№", t("student"), t("rcJournal")], ...s.roster.map((r, i) => [i + 1, r.name, label[r.status]])];
    const csv = "﻿" + rows.map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    Object.assign(document.createElement("a"), { href: url, download: `${s.title} ${rcDate(s.lesson_date)}.csv` }).click();
    URL.revokeObjectURL(url);
  });
  $("#rc-wipe").addEventListener("click", async () => {
    if (!confirm(t("rcWipeConfirm"))) return;
    await API.del("/api/rollcall/faces/all");
    Object.keys(urls).filter((k) => k.startsWith("f")).forEach((k) => delete urls[k]);
    await refresh(true);
  });

  // ---- top: comparison
  function renderCompare() {
    const enrolledSet = new Set(s.roster.filter((r) => r.consent && r.samples.length).map((r) => r.name));
    const seen = new Set(s.recognized);
    const notSeen = [...enrolledSet].filter((n) => !seen.has(n));
    let kind = "none", text = t("rcNoPhoto"), action = "";
    if (s.busy) { kind = "busy"; text = t("rcBusy"); }
    else if (!s.enrolled) { kind = "warn"; text = t("rcNoEnrolled"); }
    else if (s.faces_total !== null) {
      kind = notSeen.length || s.unknown_faces ? "warn" : "ok";
      text = t("rcResult", { r: s.recognized.length }) + (notSeen.length ? " " + t("rcNotSeen", { names: notSeen.map(shortName).join(", ") }) : "");
      action = `<button class="btn primary sm" id="rc-apply">${t("rcApply")}</button>`;
    }
    $("#rc-compare").innerHTML = `
      <div class="rc-nums rc-nums-4">
        <div class="att-big total"><b>${s.total}</b><span>${t("rcOnList")}</span></div>
        <div class="att-big came"><b>${s.busy ? '<span class="spinner big"></span>' : s.faces_total === null ? "—" : s.recognized.length}</b><span>${t("rcRecognized")}</span></div>
        <div class="att-big ${s.unknown_faces ? "miss" : ""}"><b>${s.faces_total === null ? "—" : s.unknown_faces}</b><span>${t("rcUnknownFaces")}</span></div>
        <div class="att-big"><b>${s.enrolled}<small>/${s.total}</small></b><span>${t("rcEnrolled")}</span></div>
      </div>
      <div class="rc-verdict rc-${kind}">${kind === "ok" ? "✓" : kind === "warn" ? "⚠" : kind === "busy" ? '<span class="spinner"></span>' : "ⓘ"}
        <span class="grow">${esc(text)}</span>${action}</div>
      ${appliedNote ? `<div class="rc-applied">${esc(appliedNote)}</div>` : ""}`;
    $("#rc-apply")?.addEventListener("click", async () => {
      try {
        const res = await API.post(`/api/rollcall/${id}/apply`);
        s = res;
        appliedNote = `✓ ${t("rcApplied")}.` + (res.not_enrolled.length ? " " + t("rcNotEnrolledNote", { n: res.not_enrolled.length }) : "");
      } catch (err) { appliedNote = err.message; }
      renderAll();
    });
  }

  // ---- class photos with named boxes
  function renderPhotos() {
    $("#rc-upload").querySelectorAll("label.btn").forEach((l) => l.classList.toggle("hidden", s.photo_list.length >= 3));
    $("#rc-photos").innerHTML = s.photo_list.map((p) => `
      <div class="rc-photo-card">
        <div class="rc-photo" data-photo="${p.id}">
          <img alt="">
          ${p.ai_status === "done" ? p.faces.map((f, i) => `
            <button type="button" class="rc-box lv-${f.level}" data-face="${i}" style="top:${f.box[0] / 10}%;left:${f.box[1] / 10}%;height:${(f.box[2] - f.box[0]) / 10}%;width:${(f.box[3] - f.box[1]) / 10}%"
              title="${esc(f.name || "?")}${f.score ? ` · ${Math.round(f.score * 100)}%` : ""}"><i>${esc(f.name ? shortName(f.name) : "?")}</i></button>`).join("") : ""}
          ${["pending", "checking"].includes(p.ai_status) ? `<div class="rc-photo-busy"><span class="spinner big"></span>${t("rcBusy")}</div>` : ""}
        </div>
        <div class="rc-photo-info">
          ${p.ai_status === "done" ? `<span class="chip ai-chip">📷 ${t("rcFacesFound", { n: p.ai_count })}</span><span class="muted small-text">${t("rcClickFace")}</span>` : ""}
          ${p.ai_status === "error" ? `<span class="chip warn-chip">${esc(rcErr(p.ai_note || ""))}</span>` : ""}
          <div class="cell-actions">
            ${!["pending", "checking"].includes(p.ai_status) ? `<button class="btn sm" data-recount="${p.id}">↻ ${t("rcRecount")}</button>` : ""}
            <button class="btn sm danger icon-only" data-del-photo="${p.id}" aria-label="${t("delete")}">✕</button>
          </div>
        </div>
      </div>`).join("");
    $("#rc-photos").querySelectorAll("[data-photo]").forEach(async (el) => {
      const pid = el.dataset.photo;
      try { el.querySelector("img").src = await blob(`p${pid}`, `/api/rollcall/photos/${pid}`); } catch {}
      el.querySelectorAll("[data-face]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); whoIsThis(pid, Number(b.dataset.face)); }));
    });
    $("#rc-photos").querySelectorAll("[data-recount]").forEach((b) => b.addEventListener("click", async () => {
      await API.post(`/api/rollcall/photos/${b.dataset.recount}/recount`); await refresh(true);
    }));
    $("#rc-photos").querySelectorAll("[data-del-photo]").forEach((b) => b.addEventListener("click", async () => {
      if (!confirm(t("confirmDelete"))) return;
      await API.del(`/api/rollcall/photos/${b.dataset.delPhoto}`); await refresh(true);
    }));
  }

  // Teacher points out who a face is (or that it's nobody on the list).
  function whoIsThis(pid, index) {
    const p = s.photo_list.find((x) => String(x.id) === String(pid));
    const f = p.faces[index];
    const taken = new Set(p.faces.filter((x, i) => i !== index && x.name).map((x) => x.name));
    const opts = s.roster.map((r) => `<option value="${esc(r.name)}" ${f.name === r.name ? "selected" : ""}>${esc(r.name)}${taken.has(r.name) ? " ✓" : ""}</option>`).join("");
    showModal(`<h3>${t("rcWhoIsThis")}</h3>
      <div class="rc-who"><canvas id="rc-who-face" width="160" height="160"></canvas>
        <div class="grow"><select id="rc-who-sel"><option value="">${t("rcNotStudent")}</option>${opts}</select>
          <label class="switch-row"><input type="checkbox" id="rc-who-learn" checked> <span>${t("rcLearn")}</span></label>
          <div class="actions"><button class="btn primary" id="rc-who-save">${t("rcSave")}</button></div>
          <p class="error" id="rc-who-err"></p></div></div>`);
    // show the face crop
    const img = new Image();
    img.onload = () => {
      const c = $("#rc-who-face"); if (!c) return;
      const [y0, x0, y1, x1] = f.box.map((v, i) => (v / 1000) * (i % 2 ? img.naturalWidth : img.naturalHeight));
      const side = Math.max(x1 - x0, y1 - y0) * 1.6, cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
      c.getContext("2d").drawImage(img, cx - side / 2, cy - side / 2, side, side, 0, 0, 160, 160);
    };
    img.src = urls[`p${pid}`];
    $("#rc-who-save").addEventListener("click", async () => {
      const name = $("#rc-who-sel").value || null;
      try {
        await API.post(`/api/rollcall/photos/${pid}/faces/${index}`, { student_name: name, learn: $("#rc-who-learn").checked });
        document.querySelector(".modal-bg")?.remove();
        await refresh(true);
      } catch (err) { $("#rc-who-err").textContent = rcErr(err.message); }
    });
  }

  // ---- journal
  function renderList() {
    const seen = new Set(s.recognized);
    $("#rc-list").innerHTML = s.roster.map((r, i) => `
      <div class="rc-row rc-${r.status}">
        <span class="rc-num">${i + 1}</span>
        <b class="grow">${esc(r.name)}${seen.has(r.name) ? ` <span class="chip mini ai-chip">📷 ${t("rcSeen")}</span>` : ""}</b>
        <div class="rc-seg" role="group" aria-label="${esc(r.name)}">
          ${RC_STATUSES.map(([k, ic, key]) => `<button type="button" class="${r.status === k ? `on ${k}` : ""}" data-name="${esc(r.name)}" data-st="${k}" title="${t(key)}">${ic}<span>${t(key)}</span></button>`).join("")}
        </div>
      </div>`).join("");
    $("#rc-list").querySelectorAll("[data-st]").forEach((b) => b.addEventListener("click", () => {
      if (!b.classList.contains("on")) setMarks({ [b.dataset.name]: b.dataset.st });
    }));
  }

  // ---- enrollment (consent first, then 2–3 face photos)
  function renderEnroll() {
    $("#rc-enrolled-chip").textContent = `${s.enrolled}/${s.total}`;
    $("#rc-enroll").innerHTML = s.roster.map((r) => `
      <div class="rc-enroll-row ${r.consent ? "" : "no-consent"}">
        <b class="grow">${esc(r.name)}</b>
        <label class="switch-row rc-consent"><input type="checkbox" data-consent="${esc(r.name)}" ${r.consent ? "checked" : ""}> <span>${t("rcConsent")}</span></label>
        <div class="rc-thumbs">
          ${r.samples.map((sid) => `<span class="rc-thumb"><img data-thumb="${sid}" alt=""><button type="button" data-del-sample="${sid}" aria-label="${t("delete")}">×</button></span>`).join("")}
          ${r.consent && r.samples.length < 5 ? `
            <label class="rc-add-face" title="${t("rcAddFace")}">${t("rcAddFace")}<input type="file" accept="image/*" capture="environment" class="hidden" data-add="${esc(r.name)}"></label>` : ""}
        </div>
      </div>`).join("");
    $("#rc-enroll").querySelectorAll("[data-thumb]").forEach(async (im) => {
      try { im.src = await blob(`f${im.dataset.thumb}`, `/api/rollcall/faces/samples/${im.dataset.thumb}`); } catch {}
    });
    $("#rc-enroll").querySelectorAll("[data-consent]").forEach((cb) => cb.addEventListener("change", async () => {
      const name = cb.dataset.consent;
      const row = s.roster.find((x) => x.name === name);
      if (!cb.checked && row.samples.length && !confirm(t("rcConsentOffConfirm"))) { cb.checked = true; return; }
      await API.put("/api/rollcall/faces/consent", { student_name: name, consent: cb.checked });
      await refresh(true);
    }));
    $("#rc-enroll").querySelectorAll("[data-add]").forEach((inp) => inp.addEventListener("change", async (e) => {
      const file = e.target.files[0]; e.target.value = "";
      if (!file) return;
      $("#rc-enroll-err").textContent = "";
      const fd = new FormData(); fd.append("student_name", inp.dataset.add); fd.append("file", file, file.name || "face.jpg");
      try { await API.upload("/api/rollcall/faces/samples", fd); }
      catch (err) { $("#rc-enroll-err").textContent = `${inp.dataset.add}: ${rcErr(err.message)}`; }
      await refresh(true);
    }));
    $("#rc-enroll").querySelectorAll("[data-del-sample]").forEach((b) => b.addEventListener("click", async () => {
      await API.del(`/api/rollcall/faces/samples/${b.dataset.delSample}`); await refresh(true);
    }));
  }

  function renderAll() { renderCompare(); renderPhotos(); renderList(); renderEnroll(); }

  let lastSig = "";
  async function refresh(force = false) {
    if (location.hash !== `#/attendance/${id}`) return;
    s = await API.get(`/api/rollcall/${id}`);
    const sig = JSON.stringify(s.photo_list);
    if (force || sig !== lastSig) { renderAll(); lastSig = sig; }
    if (s.busy) poll(() => refresh(), 2000);
  }
  await refresh(true);
}
