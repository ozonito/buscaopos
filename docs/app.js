const REPO_URL = "https://github.com/ozonito/buscaopos";

const ADMIN_LEVELS = {
  1: { label: "1. Gobierno de Canarias", icon: "🏛️" },
  2: { label: "2. Cabildo de Gran Canaria", icon: "🏝️" },
  3: { label: "3. ULPGC", icon: "🎓" },
  4: { label: "4. Ayuntamientos y Otros", icon: "🏢" },
};

let dashboardData = null;

function initTheme() {
  document.documentElement.setAttribute("data-theme", "dark");
  localStorage.setItem("buscaopos_theme", "dark");
}

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function buildReportIssueUrl(proceso) {
  const title = encodeURIComponent(`[Entrenamiento] Ajuste en: ${proceso.titulo}`);
  const body = encodeURIComponent(
    `### Proceso afectado\n- **ID**: \`${proceso.id}\`\n- **Organismo**: ${proceso.organismo}\n- **URL**: ${proceso.url_portal}\n\n### Fallo detectado o regla a entrenar\nDescribe qué ha fallado o qué debe tener en cuenta Buscaopos a partir de ahora:\n`
  );
  return `${REPO_URL}/issues/new?labels=training-feedback&title=${title}&body=${body}`;
}

function renderStats(data) {
  document.getElementById("last-updated").textContent =
    `Actualizado: ${data.fecha_legible || "—"}`;
  document.getElementById("stat-procesos").textContent = data.resumen.total_procesos;
  document.getElementById("stat-fuentes").textContent =
    `${data.resumen.fuentes_ok}/${data.resumen.total_fuentes} OK`;
  document.getElementById("stat-novedades").textContent = data.resumen.novedades_recientes;
  document.getElementById("stat-ia").textContent = data.ia_activa ? "Activa" : "Modo reglas";
}

function renderProcesos() {
  const container = document.getElementById("procesos-container");
  const search = document.getElementById("search-input").value.trim().toLowerCase();
  const adminFilter = document.getElementById("filter-admin").value;
  const grupoFilter = document.getElementById("filter-grupo").value;

  const filtered = (dashboardData.procesos || []).filter((p) => {
    if (adminFilter !== "all" && String(p.nivel_prioridad) !== adminFilter) return false;
    if (grupoFilter !== "all" && !String(p.grupo).toUpperCase().includes(grupoFilter)) return false;
    if (search) {
      const hay = `${p.titulo} ${p.organismo} ${p.cuerpo} ${p.grupo} ${p.situacion_actual}`.toLowerCase();
      if (!hay.includes(search)) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `<div class="panel"><p class="muted">No hay procesos que coincidan con los filtros actuales.</p></div>`;
    return;
  }

  // Group strictly by priority level 1 -> 2 -> 3 -> 4
  const grouped = { 1: [], 2: [], 3: [], 4: [] };
  filtered.forEach((p) => {
    const lvl = grouped[p.nivel_prioridad] ? p.nivel_prioridad : 4;
    grouped[lvl].push(p);
  });

  let html = "";
  [1, 2, 3, 4].forEach((lvl) => {
    const items = grouped[lvl];
    if (!items.length) return;
    const meta = ADMIN_LEVELS[lvl];
    html += `
      <section class="admin-section">
        <div class="admin-group-header">
          <h2>${meta.icon} ${meta.label}</h2>
          <span class="badge badge-muted">${items.length} proceso(s)</span>
        </div>
        <div class="cards-grid">
          ${items.map((p) => renderCard(p)).join("")}
        </div>
      </section>
    `;
  });

  container.innerHTML = html;

  container.querySelectorAll("[data-open-modal]").forEach((btn) => {
    btn.addEventListener("click", () => openModal(btn.getAttribute("data-open-modal")));
  });
}

function renderCard(p) {
  const docLink = p.ultimo_documento_url
    ? `<a class="btn btn-outline" href="${escapeHtml(p.ultimo_documento_url)}" target="_blank" rel="noopener" title="${escapeHtml(p.ultimo_documento_titulo || "Último documento publicado")}">📎 Último doc</a>`
    : "";
  const examBadge = p.fecha_examen
    ? `<span class="badge badge-ok">📅 Examen: ${escapeHtml(p.fecha_examen)}${p.hora_llamamiento ? " · " + escapeHtml(p.hora_llamamiento) : ""}</span>`
    : "";

  return `
    <article class="process-card">
      <div>
        <div class="card-meta">
          <span class="badge">${escapeHtml(p.grupo)} · ${escapeHtml(p.sistema || "Proceso")}</span>
          <span class="badge badge-muted">${escapeHtml(p.estado)}</span>
          ${examBadge}
        </div>
        <h3 class="card-title">${escapeHtml(p.titulo)}</h3>
        <p class="card-org">${escapeHtml(p.organismo)}</p>
        <p class="card-cuerpo">${escapeHtml(p.cuerpo)}</p>
      </div>

      <div class="situacion-box">
        <h4>Situación actual del proceso selectivo</h4>
        <p>${escapeHtml(p.situacion_actual || "Sin información registrada todavía.")}</p>
      </div>

      <div class="card-actions">
        <button class="btn btn-outline" data-open-modal="${escapeHtml(p.id)}">📄 Ficha e historial</button>
        ${docLink}
        <a class="btn btn-outline" href="${escapeHtml(p.url_portal)}" target="_blank" rel="noopener">🔗 Web del proceso</a>
      </div>
    </article>
  `;
}

function openModal(id) {
  const p = (dashboardData.procesos || []).find((x) => x.id === id);
  if (!p) return;

  const modal = document.getElementById("process-modal");
  document.getElementById("modal-admin-badge").textContent =
    `${ADMIN_LEVELS[p.nivel_prioridad]?.label || p.administracion} · ${p.grupo}`;
  document.getElementById("modal-title").textContent = p.titulo;
  document.getElementById("modal-subtitle").textContent = `${p.organismo} — ${p.cuerpo}`;
  document.getElementById("modal-portal-link").href = p.url_portal || "#";
  document.getElementById("modal-report-link").href = buildReportIssueUrl(p);

  const modalDocLink = document.getElementById("modal-doc-link");
  if (p.ultimo_documento_url) {
    modalDocLink.href = p.ultimo_documento_url;
    modalDocLink.textContent = "📎 Último documento";
    modalDocLink.title = p.ultimo_documento_titulo || "Último documento publicado";
    modalDocLink.style.display = "inline-flex";
  } else {
    modalDocLink.style.display = "none";
  }

  const histHtml = (p.historial || []).length
    ? `<ul>${p.historial.map((h) => `<li>${escapeHtml(h)}</li>`).join("")}</ul>`
    : `<p class="muted">Sin hitos registrados todavía.</p>`;

  const examHtml = p.fecha_examen
    ? `<div><h4>Fecha estimada / convocada de examen</h4><p><strong>${escapeHtml(p.fecha_examen)}</strong>${p.hora_llamamiento ? ` · Llamamiento: <strong>${escapeHtml(p.hora_llamamiento)}</strong>` : ""}</p></div>`
    : "";

  // El último apartado debe ser siempre la situación actual del proceso selectivo
  document.getElementById("modal-body").innerHTML = `
    <div>
      <h4>Descripción</h4>
      <p>${escapeHtml(p.descripcion || "—")}</p>
    </div>
    ${examHtml}
    <div>
      <h4>Historial de hitos y publicaciones (ordenado por fecha)</h4>
      ${histHtml}
    </div>
    <div class="situacion-box">
      <h4>Situación actual del proceso selectivo</h4>
      <p class="situacion-headline">${escapeHtml(p.estado || "Pendiente de actualización")}</p>
      <p class="situacion-detail">${escapeHtml(p.situacion_actual || "Pendiente de actualización.")}</p>
    </div>
  `;

  modal.showModal();
}

function renderNovedades(novedades) {
  const el = document.getElementById("novedades-list");
  if (!novedades || !novedades.length) {
    el.innerHTML = `<p class="muted">No se han registrado novedades recientes todavía. El bot comprobará BOP Las Palmas, BOC y los portales en la próxima ejecución diaria.</p>`;
    return;
  }
  el.innerHTML = novedades
    .slice(0, 15)
    .map(
      (n) => `
      <div class="novedad-item">
        <div class="card-meta">
          <strong>${escapeHtml(n.fuente)}</strong>
          <span class="badge badge-muted">${escapeHtml(n.fecha)}</span>
        </div>
        <p style="margin:0.35rem 0;">
          <a href="${escapeHtml(n.url)}" target="_blank" rel="noopener">${escapeHtml(n.titulo)}</a>
        </p>
        <p class="muted" style="margin:0;">${escapeHtml(n.resumen)}</p>
      </div>
    `
    )
    .join("");
}

function renderFuentes(fuentes) {
  const tbody = document.getElementById("fuentes-tbody");
  tbody.innerHTML = (fuentes || [])
    .map((f) => {
      const ok = f.estado_rastreo === "ok";
      const badgeClass = ok ? "badge-ok" : "badge-err";
      const statusText = ok ? `OK (${f.http_status})` : `Error (${f.http_status || "timeout"})`;
      return `
        <tr>
          <td><strong>${escapeHtml(f.nombre)}</strong></td>
          <td>${escapeHtml(f.ambito)}</td>
          <td>${escapeHtml(f.frecuencia)}</td>
          <td><span class="badge ${badgeClass}">${statusText}</span></td>
          <td><a href="${escapeHtml(f.url)}" target="_blank" rel="noopener">Abrir</a></td>
        </tr>
      `;
    })
    .join("");
}

function getIncursoMap() {
  try {
    return JSON.parse(localStorage.getItem("buscaopos_incurso") || "{}");
  } catch {
    return {};
  }
}

function setIncursoState(id, isActive) {
  const map = getIncursoMap();
  map[id] = isActive;
  localStorage.setItem("buscaopos_incurso", JSON.stringify(map));
}

function updateSyncBajasBtn(procesos) {
  const btn = document.getElementById("sync-incurso-btn");
  if (!btn) return;
  const map = getIncursoMap();
  const desactivados = (procesos || []).filter((p) => map[p.id] === false);
  if (!desactivados.length) {
    btn.style.display = "none";
    return;
  }
  const title = encodeURIComponent(`[Baja de procesos] Desactivar ${desactivados.length} proceso(s)`);
  const listTxt = desactivados
    .map((p) => `- \`${p.id}\` — ${p.titulo} (${p.organismo})`)
    .join("\n");
  const body = encodeURIComponent(
    `### Procesos en los que ya no estoy incurso (\`activo: false\`)\n${listTxt}\n\n*(Mantener las webs correspondientes activas en \`webs.md\` para futuras convocatorias).*`
  );
  btn.href = `${REPO_URL}/issues/new?labels=training-feedback&title=${title}&body=${body}`;
  btn.textContent = `📤 Sincronizar bajas (${desactivados.length})`;
  btn.style.display = "inline-flex";
}

function renderResumenProcesos(procesos) {
  const tbody = document.getElementById("resumen-procesos-tbody");
  if (!tbody) return;
  if (!procesos || !procesos.length) {
    tbody.innerHTML = `<tr><td colspan="4" class="muted">No hay procesos activos registrados.</td></tr>`;
    return;
  }
  const map = getIncursoMap();
  tbody.innerHTML = procesos
    .map((p) => {
      const checked = map[p.id] !== false;
      return `
      <tr class="${checked ? "" : "row-inactive"}" data-row-id="${escapeHtml(p.id)}">
        <td><strong>${escapeHtml(p.administracion)}</strong><br><span class="muted">${escapeHtml(p.organismo)}</span></td>
        <td>${escapeHtml(p.titulo)} <span class="badge badge-muted">${escapeHtml(p.grupo)}</span></td>
        <td>${escapeHtml(p.estado)}</td>
        <td>
          <div class="switch-wrap">
            <label class="switch" title="Activar o desactivar seguimiento si estás incurso">
              <input type="checkbox" data-incurso-toggle="${escapeHtml(p.id)}" ${checked ? "checked" : ""} />
              <span class="slider"></span>
            </label>
            <span class="muted" data-incurso-label="${escapeHtml(p.id)}">${checked ? "Incurso" : "Baja"}</span>
          </div>
        </td>
      </tr>
    `;
    })
    .join("");

  tbody.querySelectorAll("[data-incurso-toggle]").forEach((input) => {
    input.addEventListener("change", () => {
      const id = input.getAttribute("data-incurso-toggle");
      const active = input.checked;
      setIncursoState(id, active);
      const row = tbody.querySelector(`[data-row-id="${id}"]`);
      const lbl = tbody.querySelector(`[data-incurso-label="${id}"]`);
      if (row) row.classList.toggle("row-inactive", !active);
      if (lbl) lbl.textContent = active ? "Incurso" : "Baja";
      updateSyncBajasBtn(procesos);
    });
  });

  updateSyncBajasBtn(procesos);
}

function initNewProcessModal() {
  const modal = document.getElementById("new-process-modal");
  const openBtn = document.getElementById("open-new-process-btn");
  const closeBtn = document.getElementById("new-process-close");
  const cancelBtn = document.getElementById("new-process-cancel");
  const form = document.getElementById("new-process-form");
  if (!modal || !openBtn || !form) return;

  openBtn.addEventListener("click", () => modal.showModal());
  closeBtn?.addEventListener("click", () => modal.close());
  cancelBtn?.addEventListener("click", () => modal.close());

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const cuerpo = document.getElementById("np-cuerpo").value;
    const [nivel, admin] = document.getElementById("np-admin").value.split("|");
    const organismo = document.getElementById("np-organismo").value.trim();
    const titulo = document.getElementById("np-titulo").value.trim();
    const web = document.getElementById("np-web").value.trim();

    const issueTitle = encodeURIComponent(`[Nuevo proceso] [${cuerpo}] ${titulo} (${organismo})`);
    const issueBody = encodeURIComponent(
      `### Alta de nuevo proceso selectivo\n` +
      `- **Cuerpo / Grupo**: \`${cuerpo}\`\n` +
      `- **Administración**: ${admin} (Nivel ${nivel})\n` +
      `- **Organismo convocante**: ${organismo}\n` +
      `- **Proceso / Plaza**: ${titulo}\n` +
      `- **Web de la administración**: ${web}\n\n` +
      `Por favor, añade esta fuente a \`webs.md\` y crea su ficha en \`fichas/\`.`
    );
    window.open(
      `${REPO_URL}/issues/new?labels=training-feedback&title=${issueTitle}&body=${issueBody}`,
      "_blank",
      "noopener"
    );
    form.reset();
    modal.close();
  });
}

async function init() {
  initTheme();
  initNewProcessModal();
  document.getElementById("modal-close").addEventListener("click", () => {
    document.getElementById("process-modal").close();
  });

  ["search-input", "filter-admin", "filter-grupo"].forEach((id) => {
    document.getElementById(id).addEventListener("input", renderProcesos);
    document.getElementById(id).addEventListener("change", renderProcesos);
  });

  try {
    const resp = await fetch("data/dashboard.json", { cache: "no-store" });
    dashboardData = await resp.json();
    renderStats(dashboardData);
    renderProcesos();
    renderNovedades(dashboardData.novedades);
    renderFuentes(dashboardData.fuentes);
    renderResumenProcesos(dashboardData.procesos);
  } catch (err) {
    document.getElementById("procesos-container").innerHTML =
      `<div class="panel"><p class="muted">Error cargando data/dashboard.json: ${escapeHtml(err.message)}</p></div>`;
  }
}

init();
