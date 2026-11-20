// Photo picker: "Select photos" tile + thumbnails with remove buttons + camera capture.
// Usage: const picker = createPhotoPicker(element, { max: 10 }); picker.getFiles(); picker.clear();

const PP_ACCEPT = ".pdf,.docx,.pptx,.txt,.md,.jpg,.jpeg,.png,.webp,.gif,.bmp,.heic,.heif,image/*";
const PP_CAMERA_SVG = `<svg viewBox="0 0 24 24" width="30" height="30" fill="currentColor" aria-hidden="true"><path d="M9 3 7.2 5H4a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-3.2L15 3H9Zm3 5a5 5 0 1 1 0 10 5 5 0 0 1 0-10Zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"/></svg>`;
const PP_PHONE_SVG = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="2"/><path d="M11 18h2"/></svg>`;

function createPhotoPicker(root, { max = 10 } = {}) {
  let items = []; // { file, url }
  const isTouch = window.matchMedia("(pointer: coarse)").matches;

  root.innerHTML = `
    <div class="pp">
      <button type="button" class="pp-cam-link">${PP_PHONE_SVG}<span>${t("ppCamera")}</span></button>
      <div class="pp-label"></div>
      <div class="pp-grid">
        <label class="pp-tile pp-add">
          ${PP_CAMERA_SVG}<b>${t("ppSelect")}</b><small>${t("ppDrop")}</small>
          <input type="file" multiple accept="${PP_ACCEPT}" class="hidden pp-input">
        </label>
      </div>
      <input type="file" accept="image/*" capture="environment" class="hidden pp-capture">
      <p class="error pp-err"></p>
    </div>`;
  const grid = root.querySelector(".pp-grid");
  const addTile = root.querySelector(".pp-add");
  const label = root.querySelector(".pp-label");
  const err = root.querySelector(".pp-err");

  function add(files) {
    err.textContent = "";
    for (const f of files) {
      if (items.length >= max) { err.textContent = t("ppMax", { n: max }); break; }
      items.push({ file: f, url: f.type.startsWith("image/") && !/hei[cf]$/i.test(f.name) ? URL.createObjectURL(f) : null });
    }
    render();
  }

  function render() {
    grid.querySelectorAll(".pp-thumb").forEach((el) => el.remove());
    items.forEach((it, i) => {
      const tile = document.createElement("div");
      tile.className = "pp-tile pp-thumb";
      tile.innerHTML = `${it.url ? `<img src="${it.url}" alt="">` : `<div class="pp-doc">📄<span>${esc(it.file.name)}</span></div>`}
        <span class="pp-num">${i + 1}</span>
        <button type="button" class="pp-x" aria-label="${t("delete")}" title="${t("delete")}">×</button>`;
      tile.querySelector(".pp-x").addEventListener("click", (e) => {
        e.stopPropagation();
        if (it.url) URL.revokeObjectURL(it.url);
        items.splice(i, 1);
        render();
      });
      if (it.url) tile.addEventListener("click", () => showModal(`<img src="${it.url}" class="pp-big" alt="">`));
      grid.appendChild(tile);
    });
    label.textContent = items.length ? `${t("ppMyImages")} (${t("ppUnsent", { n: items.length })})` : "";
    addTile.classList.toggle("hidden", items.length >= max);
  }

  // file chooser
  root.querySelector(".pp-input").addEventListener("change", (e) => { add(e.target.files); e.target.value = ""; });
  root.querySelector(".pp-capture").addEventListener("change", (e) => { add(e.target.files); e.target.value = ""; });

  // drag & drop
  ["dragenter", "dragover"].forEach((ev) => grid.addEventListener(ev, (e) => { e.preventDefault(); grid.classList.add("pp-drag"); }));
  ["dragleave", "drop"].forEach((ev) => grid.addEventListener(ev, (e) => { e.preventDefault(); grid.classList.remove("pp-drag"); }));
  grid.addEventListener("drop", (e) => add(e.dataTransfer.files));

  // camera: phone -> native camera; computer -> webcam window
  root.querySelector(".pp-cam-link").addEventListener("click", () => {
    if (isTouch || !navigator.mediaDevices?.getUserMedia) root.querySelector(".pp-capture").click();
    else openWebcam();
  });

  async function openWebcam() {
    let stream;
    err.textContent = "";
    label.dataset.prev = label.textContent;
    label.textContent = t("ppOpening");
    try {
      // Some browsers never answer when camera access is blocked: give up after 15 s.
      stream = await Promise.race([
        navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment", width: { ideal: 1920 } } }),
        new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 15000)),
      ]);
    } catch {
      err.textContent = t("ppNoCamera");
      return;
    } finally {
      label.textContent = label.dataset.prev;
    }
    const bg = document.createElement("div");
    bg.className = "modal-bg";
    bg.innerHTML = `<div class="modal pp-cam">
      <video autoplay playsinline muted></video>
      <div class="actions"><button type="button" class="btn primary pp-shot">📸 ${t("ppTake")}</button><button type="button" class="btn pp-close">${t("close")}</button><span class="muted pp-taken"></span></div>
    </div>`;
    document.body.appendChild(bg);
    const video = bg.querySelector("video");
    video.srcObject = stream;
    let taken = 0;
    const close = () => { stream.getTracks().forEach((tr) => tr.stop()); bg.remove(); };
    bg.querySelector(".pp-close").addEventListener("click", close);
    bg.addEventListener("click", (e) => { if (e.target === bg) close(); });
    bg.querySelector(".pp-shot").addEventListener("click", () => {
      const c = document.createElement("canvas");
      c.width = video.videoWidth; c.height = video.videoHeight;
      c.getContext("2d").drawImage(video, 0, 0);
      c.toBlob((blob) => {
        add([new File([blob], `camera-${Date.now()}.jpg`, { type: "image/jpeg" })]);
        taken += 1;
        bg.querySelector(".pp-taken").textContent = `✓ ${taken}`;
        if (items.length >= max) close();
      }, "image/jpeg", 0.9);
    });
  }

  render();
  return {
    getFiles: () => items.map((it) => it.file),
    clear: () => { items.forEach((it) => it.url && URL.revokeObjectURL(it.url)); items = []; render(); },
  };
}
