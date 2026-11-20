// "Тапсырмалар" — AI checking of student work in 5 steps.
// Depends on helpers from app.js: $, esc, t, API, pages, view, fmtDate, fmtSize, showModal, poll, ME.

const ACCEPT = ".pdf,.docx,.pptx,.txt,.md,.jpg,.jpeg,.png,.webp,.gif,.bmp,.heic,.heif,image/*";
const fmtScore = (v) => (v === null || v === undefined ? "—" : Number(v).toString());

// ------------------------------------------------------------------ list
pages.assignments = async function () {
  const items = await API.get("/api/assignments");
  view().innerHTML = `
    <div class="toolbar"><h2>${t("navAssignments")}</h2><button class="btn primary" id="add">+ ${t("newAssignment")}</button></div>
    <form class="card hidden" id="new-form"><div class="form-grid">
      <div style="grid-column:1/-1"><label>${t("title")}</label><input name="title" required placeholder="${LANG === "ru" ? "Квадратные уравнения" : "Квадрат теңдеулер"}"></div>
      <div><label>${t("subject")}</label><input name="subject" value="${esc(ME.subject || "")}"></div>
      <div><label>${t("grade")}</label><input name="grade" placeholder="8"></div>
      <div><label>${t("kind")}</label><select name="kind"><option value="homework">${t("homework")}</option><option value="quiz">${t("quiz")}</option><option value="test">${t("test")}</option></select></div>
      <div><label>${t("maxScore")}</label><input name="max_score" type="number" value="10" min="1" max="100"></div>
      <div><label>${t("outputLang")}</label><select name="language"><option value="kk" ${LANG === "kk" ? "selected" : ""}>Қазақша</option><option value="ru" ${LANG === "ru" ? "selected" : ""}>Русский</option></select></div>
      <div><label>${t("dueDate")}</label><input name="due_date" type="datetime-local"></div>
      <div style="grid-column:1/-1"><label>${t("taskText")}</label><textarea name="content" placeholder="${esc(t("taskTextHint"))}"></textarea></div>
    </div><div class="actions"><button class="btn primary">${t("create")}</button></div><p class="error" id="new-err"></p></form>
    <div class="grid">${items.length ? items.map((a) => `
      <div class="card tool" data-go="#/assignment/${a.id}">
        <div class="ic pink">✎</div><b>${esc(a.title)}</b>
        <span class="muted">${esc(a.subject || "")}${a.grade ? " · " + esc(a.grade) : ""} · ${t(a.kind)}</span>
        <div class="chips"><span class="chip">${a.submission_count} ${t("submissionsShort")}</span><span class="chip">${a.checked_count} ${t("checkedShort")}</span>${a.analysis_status === "done" ? `<span class="chip ok">ЖИ ✓</span>` : ""}</div>
      </div>`).join("") : ""}</div>
    ${items.length ? "" : `
      <div class="card empty-state" id="empty-state">
        <div class="ic pink big">✎</div>
        <h3>${t("emptyTitle")}</h3>
        <p class="muted">${t("emptyText")}</p>
        <ol class="empty-steps">
          <li>${t("s1Title")}</li><li>${t("s2Title")}</li><li>${t("s3Title")}</li><li>${t("s4Title")}</li><li>${t("s5Title")}</li>
        </ol>
        <button class="btn primary" id="add-empty">+ ${t("newAssignment")}</button>
      </div>`}`;
  const openForm = () => {
    $("#new-form").classList.toggle("hidden");
    $("#empty-state")?.classList.toggle("hidden", !$("#new-form").classList.contains("hidden"));
    if (!$("#new-form").classList.contains("hidden")) $("#new-form [name=title]").focus();
  };
  $("#add").addEventListener("click", openForm);
  $("#add-empty")?.addEventListener("click", openForm);
  $("#new-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = emptyToNull(formData(e.target));
    d.max_score = Number(d.max_score || 10);
    try { const a = await API.post("/api/assignments", d); location.hash = `#/assignment/${a.id}`; }
    catch (err) { $("#new-err").textContent = err.message; }
  });
  view().querySelectorAll("[data-go]").forEach((el) => el.addEventListener("click", () => (location.hash = el.dataset.go)));
};

// ------------------------------------------------------------------ detail (5 steps)
// Tap on ⓘ toggles it (hover already shows it on a computer). One handler for every page.
document.addEventListener("click", (e) => {
  const tip = e.target.closest(".info");
  document.querySelectorAll(".info.open").forEach((x) => { if (x !== tip) x.classList.remove("open"); });
  if (tip) tip.classList.toggle("open");
});

// ⓘ icon: the text shows on hover / tap (keeps cards short).
function infoTip(id, html) {
  return `<span class="info" tabindex="0" role="button" aria-label="Info" id="${id}">
    <span class="info-i">i</span><span class="info-pop">${html}</span></span>`;
}

function stepCard(n, role, roleClass, title, desc, bodyId) {
  return `<section class="card step hidden" id="step${n}">
    <div class="step-head">
      <span class="step-badge ${roleClass}">${t("step", { n })} · ${role}</span>
    </div>
    <div class="step-title"><h3>${title}</h3>${infoTip(`info${n}`, `<p>${desc}</p><div class="info-extra"></div>`)}</div>
    <div id="${bodyId}"></div></section>`;
}

// Extra text inside a step's ⓘ (e.g. "ЖИ әлі қосылмаған"); warn = highlight the icon.
function setStepInfo(n, html, warn = false) {
  const el = document.getElementById(`info${n}`);
  if (!el) return;
  el.querySelector(".info-extra").innerHTML = html || "";
  el.classList.toggle("warn", !!warn);
}

pages.assignment = async function (_params, id) {
  let wf = await API.get(`/api/assignments/${id}/workflow`);
  const a = wf.assignment;
  const link = `${location.origin}/#/s/${a.share_code}`;

  const stepRoles = [t("roleTeacher"), t("roleAI"), t("roleStudent"), t("roleAICheck"), t("roleTeacher")];
  view().innerHTML = `
   <div class="apple-page">
    <a href="#/assignments" class="back-link">${t("backToList")}</a>
    <div class="page-head"><div><h2>${esc(a.title)}</h2>
      <span class="muted">${[a.subject && esc(a.subject), a.grade && esc(a.grade), t(a.kind), `${t("maxScore")}: ${a.max_score}`].filter(Boolean).join(" · ")}</span></div>
      <button class="btn danger sm" id="del-assignment">${t("delete")}</button></div>
    <nav class="stepper" role="tablist">
      ${[1, 2, 3, 4, 5].map((n) => `
        <button class="stepper-item" role="tab" data-step="${n}" type="button">
          <span class="stepper-dot">${n}</span>
          <span class="stepper-text"><b>${t("step", { n })}</b><small>${stepRoles[n - 1]}</small></span>
        </button>`).join("")}
    </nav>
    <div class="steps">
      ${stepCard(1, t("roleTeacher"), "blue-badge", t("s1Title"), t("s1Desc"), "s1")}
      ${stepCard(2, t("roleAI"), "blue-badge", t("s2Title"), t("s2Desc"), "s2")}
      ${stepCard(3, t("roleStudent"), "blue-badge", t("s3Title"), t("s3Desc"), "s3")}
      ${stepCard(4, t("roleAICheck"), "green-badge", t("s4Title"), t("s4Desc"), "s4")}
      ${stepCard(5, t("roleTeacher"), "green-badge", t("s5Title"), t("s5Desc"), "s5")}
    </div>
   </div>`;

  // ---- stepper: one step visible at a time (remembered per assignment)
  const stepKey = `assignmentStep-${id}`;
  function showStep(n) {
    n = Math.min(5, Math.max(1, Number(n) || 1));
    for (let i = 1; i <= 5; i++) $(`#step${i}`).classList.toggle("hidden", i !== n);
    document.querySelectorAll(".stepper-item").forEach((b) => {
      const on = Number(b.dataset.step) === n;
      b.classList.toggle("active", on);
      b.setAttribute("aria-selected", on);
    });
    localStorageSet(stepKey, String(n));
  }
  function updateStepper() {
    const subs = wf.submissions;
    const done = {
      1: wf.sources.length > 0 || !!(a.content || "").trim(),
      2: wf.analysis_status === "done",
      3: subs.length > 0,
      4: subs.some((s) => s.status === "checked" || s.status === "no_ai"),
      5: subs.length > 0 && subs.every((s) => s.finalized),
    };
    document.querySelectorAll(".stepper-item").forEach((b) => b.classList.toggle("done", !!done[b.dataset.step]));
  }
  document.querySelectorAll(".stepper-item").forEach((b) => b.addEventListener("click", () => showStep(b.dataset.step)));
  showStep(localStorageGet(stepKey) || 1);

  $("#del-assignment").addEventListener("click", async () => {
    if (!confirm(t("confirmDelete"))) return;
    await API.del(`/api/assignments/${id}`); location.hash = "#/assignments";
  });

  // ---- step 1: material
  function renderS1() {
    $("#s1").innerHTML = `
      ${a.content ? `<label>${t("taskText")}</label><div class="output small">${esc(a.content)}</div>` : ""}
      <label>${t("navMaterials")}</label>
      ${wf.sources.length ? wf.sources.map((m) => `<div class="list-item"><span class="file-ic">📄</span><div class="grow">${esc(m.original_name)}<div class="meta">${fmtSize(m.size_bytes)}</div></div><button class="btn sm danger" data-rm="${m.id}">✕</button></div>`).join("") : `<p class="muted">${t("noFiles")}</p>`}
      <div class="actions"><label class="btn">⬆ ${t("addFiles")}<input type="file" id="src-file" class="hidden" multiple accept="${ACCEPT}"></label></div>
      <p class="error" id="s1-err"></p>`;
    $("#src-file").addEventListener("change", async (e) => {
      $("#s1-err").textContent = "";
      for (const f of e.target.files) {
        const fd = new FormData(); fd.append("file", f);
        try { await API.upload(`/api/assignments/${id}/sources`, fd); } catch (err) { $("#s1-err").textContent = `${f.name}: ${err.message}`; }
      }
      await refresh(true);
    });
    $("#s1").querySelectorAll("[data-rm]").forEach((b) => b.addEventListener("click", async () => {
      await API.del(`/api/assignments/${id}/sources/${b.dataset.rm}`); await refresh(true);
    }));
  }

  // ---- step 2: AI analysis
  function anSection(icon, title, body) {
    return body ? `<section class="an-sec"><h4><span class="an-ic">${icon}</span>${title}</h4>${body}</section>` : "";
  }
  function chipList(arr) {
    return arr && arr.length ? `<div class="an-chips">${arr.map((x) => `<span class="an-chip">${esc(x)}</span>`).join("")}</div>` : "";
  }
  function renderAnalysis(an) {
    const total = an.rubric.reduce((s, r) => s + Number(r.points || 0), 0);
    return `
      <div class="an-result">
        ${anSection("📘", t("summary"), `<p class="an-summary">${esc(an.summary)}</p>`)}
        ${anSection("∑", t("formulas"), an.formulas?.length ? `<div class="an-formulas">${an.formulas.map((f) => `<code class="an-formula">${esc(f)}</code>`).join("")}</div>` : "")}
        ${anSection("✓", t("expectedAnswers"), an.expected_answers?.length ? `<ol class="an-answers">${an.expected_answers.map((x) => `<li>${esc(x)}</li>`).join("")}</ol>` : "")}
        ${anSection("★", t("rubric"), `<div class="an-rubric">
            ${an.rubric.map((r) => `<div class="an-crit"><div class="grow"><b>${esc(r.criterion)}</b>${r.description ? `<p>${esc(r.description)}</p>` : ""}</div><span class="an-pts">${fmtScore(r.points)}</span></div>`).join("")}
            <div class="an-crit an-total"><div class="grow"><b>${t("totalPoints")}</b></div><span class="an-pts">${fmtScore(Math.round(total * 10) / 10)}</span></div>
          </div>`)}
        <div class="an-two">
          ${anSection("◆", t("keyConcepts"), chipList(an.key_concepts))}
          ${anSection("Aa", t("terms"), chipList(an.terms))}
        </div>
      </div>`;
  }
  function renderS2() {
    const an = wf.analysis;
    const st = wf.analysis_status;
    const hasInput = wf.sources.length || (a.content || "").trim();
    if (!wf.ai_enabled) {
      setStepInfo(2, `<div class="info-warn">⚠ <b>${t("noAiTitle")}</b><p>${t("noAiText")}</p></div>`, true);
    } else {
      setStepInfo(2, hasInput ? "" : `<div class="info-warn"><p>${t("needStep1")}</p></div>`, !hasInput);
    }
    const running = st === "running";
    const providerChip = wf.ai_enabled
      ? `<span class="chip ai-chip">✦ ${esc(wf.ai_provider === "gemini" ? "Gemini" : "Claude")} · ${esc(wf.ai_model || "")}</span>`
      : `<span class="chip warn-chip">⚠ ${t("noAiTitle")}</span>`;
    let html = `
      <div class="an-toolbar">
        <button class="btn primary" id="analyze" ${running || !hasInput || !wf.ai_enabled ? "disabled" : ""}>
          ${running ? `<span class="spinner"></span>${t("analyzingShort")}` : `✦ ${an ? t("reanalyze") : t("analyze")}`}
        </button>
        ${providerChip}
      </div>
      ${!hasInput && wf.ai_enabled ? `<p class="muted small-text">${t("needStep1")}</p>` : ""}`;
    if (running) {
      html += `<div class="an-loading"><span class="spinner big"></span><div><b>${t("analyzing")}</b>
        <div class="skeleton"></div><div class="skeleton short"></div></div></div>`;
    }
    if (st === "error") html += `<div class="an-error">⚠ ${t("error")}: ${esc(wf.analysis_error)}</div>`;
    if (an && !running) html += renderAnalysis(an);
    $("#s2").innerHTML = html;
    $("#analyze").addEventListener("click", async (e) => {
      e.currentTarget.disabled = true;
      e.currentTarget.innerHTML = `<span class="spinner"></span>${t("analyzingShort")}`;
      try { await API.post(`/api/assignments/${id}/analyze`); } catch (err) { alert(err.message); }
      await refresh(true);
    });
  }

  // ---- step 3: student uploads (link + teacher upload)
  function renderS3() {
    $("#s3").innerHTML = `
      <label>${t("shareLink")}</label>
      <div class="link-row"><input readonly value="${esc(link)}" id="share-link"><button class="btn" id="copy-link">${t("copy")}</button><a class="btn" href="${esc(link)}" target="_blank">↗</a></div>
      <form id="teacher-upload" class="sub-form">
        <b>${t("uploadForStudent")}</b>
        <label>${t("studentName")}</label><input name="student_name" required>
        <label>${t("photosOrFiles")}</label>
        <div id="tu-picker"></div>
        <div class="actions"><button class="btn primary" id="tu-btn">${t("send")}</button></div>
        <p class="error" id="s3-err"></p>
      </form>`;
    $("#copy-link").addEventListener("click", async (e) => {
      try { await navigator.clipboard.writeText(link); } catch { $("#share-link").select(); document.execCommand("copy"); }
      e.target.textContent = t("copied"); setTimeout(() => (e.target.textContent = t("copy")), 1500);
    });
    const picker = createPhotoPicker($("#tu-picker"));
    $("#teacher-upload").addEventListener("submit", async (e) => {
      e.preventDefault();
      const files = picker.getFiles();
      if (!files.length) { $("#s3-err").textContent = t("needFiles"); return; }
      const btn = $("#tu-btn"); btn.disabled = true; $("#s3-err").textContent = "";
      const fd = new FormData();
      fd.append("student_name", e.target.student_name.value);
      files.forEach((f) => fd.append("files", f, f.name));
      try { await API.upload(`/api/assignments/${id}/submissions`, fd); e.target.reset(); picker.clear(); await refresh(true); }
      catch (err) { $("#s3-err").textContent = err.message; }
      btn.disabled = false;
    });
  }

  // ---- step 4: AI checks
  function statusChip(s) {
    return `<span class="status st-${s.status}">${t("st_" + s.status)}</span>`;
  }
  function renderS4() {
    const subs = wf.submissions;
    setStepInfo(4, !wf.ai_enabled ? `<div class="info-warn">⚠ <b>${t("noAiTitle")}</b><p>${t("noAiManual")}</p></div>`
      : wf.analysis_status !== "done" ? `<div class="info-warn"><p>${t("waitAnalysis")}</p></div>` : "", !wf.ai_enabled || wf.analysis_status !== "done");
    let html = subs.length ? subs.map((s) => `
      <div class="list-item"><div class="avatar sm">${esc(s.student_name[0] || "?").toUpperCase()}</div>
        <div class="grow"><b>${esc(s.student_name)}</b><div class="meta">${fmtDate(s.created_at)} · ${s.file_count} 📎${s.error ? ` · <span class="error">${esc(s.error)}</span>` : ""}</div></div>
        <div class="row-actions">
          ${s.status === "checked" ? `<b class="score">${fmtScore(s.ai_score)}/${a.max_score}</b>` : ""}
          ${statusChip(s)}
          <button class="btn sm" data-detail="${s.id}">${t("details")}</button>
          ${wf.ai_enabled && wf.analysis_status === "done" && ["error", "checked", "no_ai"].includes(s.status) ? `<button class="btn sm" data-regrade="${s.id}" title="${t("regrade")}">↻</button>` : ""}
          <button class="btn sm danger icon-only" data-del-sub="${s.id}" aria-label="${t("delete")}">✕</button>
        </div>
      </div>`).join("") : `<p class="muted">${t("noSubmissions")}</p>`;
    $("#s4").innerHTML = html;
    $("#s4").querySelectorAll("[data-detail]").forEach((b) => b.addEventListener("click", () => openSubmission(b.dataset.detail)));
    $("#s4").querySelectorAll("[data-regrade]").forEach((b) => b.addEventListener("click", async () => { await API.post(`/api/submissions/${b.dataset.regrade}/regrade`); await refresh(true); }));
    $("#s4").querySelectorAll("[data-del-sub]").forEach((b) => b.addEventListener("click", async () => {
      if (!confirm(t("confirmDelete"))) return;
      await API.del(`/api/submissions/${b.dataset.delSub}`); await refresh(true);
    }));
  }

  // ---- step 5: results table
  function renderS5() {
    // Everything except work the AI is still about to check.
    const subs = wf.submissions.filter((s) => !(wf.ai_enabled && (s.status === "pending" || s.status === "checking")) || s.teacher_score !== null);
    if (!subs.length) { $("#s5").innerHTML = `<p class="muted">${t("noSubmissions")}</p>`; return; }
    $("#s5").innerHTML = `
      <div class="tbl-wrap"><table class="tbl results"><thead><tr>
        <th>${t("student")}</th><th class="num">${t("aiScore")}</th><th class="num">${t("teacherScore")}</th><th class="num">${t("finalScore")}</th><th></th>
      </tr></thead><tbody>
      ${subs.map((s) => `<tr data-row="${s.id}" class="${s.finalized ? "final" : ""}">
        <td><a href="#" data-detail="${s.id}">${esc(s.student_name)}</a></td>
        <td class="num">${s.ai_score === null ? "—" : `${fmtScore(s.ai_score)}/${a.max_score}`}</td>
        <td class="num"><input type="number" step="0.5" min="0" max="${a.max_score}" class="score-input" value="${s.teacher_score ?? ""}" placeholder="${s.ai_score ?? ""}" ${s.finalized ? "disabled" : ""}></td>
        <td class="num"><b>${fmtScore(s.final_score)}</b></td>
        <td class="right"><div class="cell-actions">${s.finalized
          ? `<span class="status st-checked">${t("approved")}</span><button class="btn sm" data-unfinal="${s.id}">${t("unapprove")}</button>`
          : `<button class="btn sm primary" data-final="${s.id}">${t("approve")}</button>`}</div></td>
      </tr>`).join("")}
      </tbody></table></div>
      <div class="actions"><button class="btn" id="approve-all">${t("approveAll")}</button><button class="btn" id="csv">⬇ ${t("exportCsv")}</button></div>
      <p class="error" id="s5-err"></p>`;
    const saveRow = async (sid, finalized) => {
      const row = $(`[data-row="${sid}"]`);
      const v = row.querySelector(".score-input").value;
      const sub = subs.find((x) => x.id == sid);
      if (finalized && v === "" && (sub.ai_score === null || sub.ai_score === undefined)) {
        $("#s5-err").textContent = `${sub.student_name}: ${t("enterScore")}`; row.querySelector(".score-input").focus(); return;
      }
      try { await API.patch(`/api/submissions/${sid}/grade`, { teacher_score: v === "" ? null : Number(v), finalized }); }
      catch (err) { $("#s5-err").textContent = err.message; return; }
      await refresh(true);
    };
    $("#s5").querySelectorAll("[data-final]").forEach((b) => b.addEventListener("click", () => saveRow(b.dataset.final, true)));
    $("#s5").querySelectorAll("[data-unfinal]").forEach((b) => b.addEventListener("click", () => saveRow(b.dataset.unfinal, false)));
    $("#s5").querySelectorAll("[data-detail]").forEach((b) => b.addEventListener("click", (e) => { e.preventDefault(); openSubmission(b.dataset.detail); }));
    $("#approve-all").addEventListener("click", async () => {
      for (const s of subs.filter((x) => !x.finalized)) {
        const v = $(`[data-row="${s.id}"] .score-input`).value;
        if (v === "" && (s.ai_score === null || s.ai_score === undefined)) continue; // nothing to approve yet
        await API.patch(`/api/submissions/${s.id}/grade`, { teacher_score: v === "" ? null : Number(v), finalized: true }).catch(() => {});
      }
      await refresh(true);
    });
    $("#csv").addEventListener("click", () => {
      const rows = [[t("student"), t("aiScore"), t("teacherScore"), t("finalScore"), t("approve")]]
        .concat(subs.map((s) => [s.student_name, s.ai_score ?? "", s.teacher_score ?? "", s.final_score ?? "", s.finalized ? "✓" : ""]));
      const csv = "﻿" + rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
      const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
      Object.assign(document.createElement("a"), { href: url, download: `${a.title}.csv` }).click();
      URL.revokeObjectURL(url);
    });
  }

  // ---- submission detail modal (step 4 result + teacher comment)
  async function openSubmission(sid) {
    const s = await API.get(`/api/submissions/${sid}`);
    const r = s.ai_result;
    const aspect = (label, x) => x ? `<div class="aspect a-${x.status}"><div><b>${label}</b><span>${t("a_" + x.status)}</span></div><p>${esc(x.comment)}</p></div>` : "";
    const imgs = s.files.filter((f) => (f.content_type || "").startsWith("image/"));
    const others = s.files.filter((f) => !(f.content_type || "").startsWith("image/"));
    showModal(`
      <h2>${esc(s.student_name)}${s.final_score !== null ? ` — ${fmtScore(s.final_score)}/${s.max_score}` : ""}</h2>
      ${r ? `<p class="muted">${t("confidence")}: <b class="conf-${r.confidence}">${t("c_" + r.confidence)}</b></p>` : ""}
      <div class="thumbs">${imgs.map((f) => `<a data-img="${f.id}" target="_blank"><img alt="${esc(f.original_name)}"></a>`).join("")}
        ${others.map((f) => `<a class="btn sm" data-file="${f.id}" data-name="${esc(f.original_name)}">📄 ${esc(f.original_name)}</a>`).join("")}</div>
      ${r ? `
        <div class="aspects">${aspect(t("formulaUsage"), r.formula_usage)}${aspect(t("solutionPath"), r.solution_path)}${aspect(t("calculations"), r.calculations)}${aspect(t("finalAnswer"), r.final_answer)}</div>
        <div class="an-block"><b>${t("rubric")}</b><table class="tbl"><thead><tr><th>${t("criterion")}</th><th class="num">${t("points")}</th><th>${t("comment")}</th></tr></thead><tbody>
          ${r.criteria.map((c) => `<tr><td>${esc(c.criterion)}</td><td class="num">${fmtScore(c.points)}/${fmtScore(c.max_points)}</td><td>${esc(c.comment)}</td></tr>`).join("")}
        </tbody></table></div>
        <div class="an-block"><b>${t("mistakes")}</b>${r.mistakes.length ? `<table class="tbl"><thead><tr><th>${t("where")}</th><th>${t("whatWrong")}</th><th>${t("howCorrect")}</th></tr></thead><tbody>
          ${r.mistakes.map((m) => `<tr><td>${esc(m.where)}</td><td>${esc(m.what)}</td><td>${esc(m.correct)}</td></tr>`).join("")}</tbody></table>` : `<p class="muted">${t("noMistakes")}</p>`}</div>
        <div class="an-block"><b>${t("feedback")}</b><p>${esc(r.feedback_for_student)}</p></div>
        ${r.note_for_teacher ? `<div class="an-block"><b>${t("noteForTeacher")}</b><p>${esc(r.note_for_teacher)}</p></div>` : ""}
        <details class="an-block"><summary><b>${t("recognized")}</b></summary><div class="output small">${esc(r.recognized_text)}</div></details>` : ""}
      <div class="an-block"><b>${t("comment")}</b><textarea id="t-comment">${esc(s.teacher_comment || "")}</textarea>
        <div class="actions"><button class="btn primary" id="save-comment">${t("saveToLibrary")}</button></div></div>`);
    for (const el of document.querySelectorAll(".modal [data-img]")) {
      API.blobUrl(`/api/submissions/${sid}/files/${el.dataset.img}`).then((u) => { el.href = u; el.querySelector("img").src = u; }).catch(() => {});
    }
    document.querySelectorAll(".modal [data-file]").forEach((el) => el.addEventListener("click", async () => {
      const u = await API.blobUrl(`/api/submissions/${sid}/files/${el.dataset.file}`);
      Object.assign(document.createElement("a"), { href: u, download: el.dataset.name }).click();
    }));
    $("#save-comment").addEventListener("click", async (e) => {
      await API.patch(`/api/submissions/${sid}/grade`, { teacher_score: s.teacher_score, teacher_comment: $("#t-comment").value, finalized: s.finalized });
      e.target.textContent = t("saved");
    });
  }

  // ---- refresh + polling while AI is working
  let lastSig = "";
  async function refresh(force = false) {
    if (!location.hash.startsWith(`#/assignment/${id}`)) return;
    wf = await API.get(`/api/assignments/${id}/workflow`);
    const sig = JSON.stringify([wf.sources, wf.analysis_status, wf.submissions]);
    if (sig !== lastSig || force === true) {
      const editing = document.activeElement && $("#s5").contains(document.activeElement);
      renderS1(); renderS2(); renderS4();
      if (!editing) renderS5();
      updateStepper();
      lastSig = sig;
    }
    const busy = wf.analysis_status === "running" || wf.submissions.some((s) => s.status === "pending" || s.status === "checking");
    if (busy) poll(() => refresh("poll"));
  }
  renderS3();
  await refresh(true);
};

// ------------------------------------------------------------------ student page (no login)
async function renderStudentPage(code) {
  const box = $("#public-view");
  let a;
  try { a = await API.get(`/api/public/a/${encodeURIComponent(code)}`); }
  catch { box.innerHTML = `<div class="auth-card"><p class="error">${t("stuNotFound")}</p></div>`; return; }
  box.innerHTML = `
    <div class="auth-card wide">
      <div class="brand"><img class="logo-img" src="/static/img/logo-mark.png" alt="Komek Teacher"><div><b>Komek Teacher</b><small>${t("stuTitle")}</small></div></div>
      <h2>${esc(a.title)}</h2>
      <p class="muted">${[a.subject && esc(a.subject), a.grade && esc(a.grade), `${t("stuTeacher")}: ${esc(a.teacher)}`, a.due_date && `${t("dueDate")}: ${fmtDate(a.due_date)}`].filter(Boolean).join(" · ")}</p>
      ${a.content ? `<div class="output small">${esc(a.content)}</div>` : ""}
      <form id="stu-form">
        <label>${t("studentName")}</label><input name="student_name" required maxlength="120">
        <label>${t("photosOrFiles")}</label>
        <p class="muted small-text">${t("stuHint")}</p>
        <div id="stu-picker"></div>
        <button class="btn primary wide" id="stu-btn">${t("send")}</button>
        <p class="error" id="stu-err"></p>
      </form>
    </div>`;
  const picker = createPhotoPicker($("#stu-picker"));
  $("#stu-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const files = picker.getFiles();
    if (!files.length) { $("#stu-err").textContent = t("needFiles"); return; }
    const btn = $("#stu-btn"); btn.disabled = true; btn.textContent = "..."; $("#stu-err").textContent = "";
    const fd = new FormData();
    fd.append("student_name", e.target.student_name.value);
    files.forEach((f) => fd.append("files", f, f.name));
    try {
      await API.upload(`/api/public/a/${encodeURIComponent(code)}/submit`, fd);
      $("#stu-form").innerHTML = `<p class="success">✓ ${t("stuDone")}</p><button class="btn wide" id="again">${t("stuAgain")}</button>`;
      $("#again").addEventListener("click", () => renderStudentPage(code));
    } catch (err) {
      $("#stu-err").textContent = err.message; btn.disabled = false; btn.textContent = t("send");
    }
  });
}
