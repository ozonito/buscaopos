const REPO_URL = "https://github.com/ozonito/buscaopos";

const ADMIN_LEVELS = {
  1: { label: "1. Gobierno de Canarias", icon: "🏛️" },
  2: { label: "2. Cabildo de Gran Canaria", icon: "🏝️" },
  3: { label: "3. Ayuntamientos y Otros", icon: "🏢" },
};

let dashboardData = null;

function initTheme() {
  const saved = localStorage.getItem("buscaopos_theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
  document.getElementById("theme-toggle").addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("buscaopos_theme", next);
  });
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

  // Group strictly by priority level 1 -> 2 -> 3
  const grouped = { 1: [], 2: [], 3: [] };
  filtered.forEach((p) => {
    const lvl = grouped[p.nivel_prioridad] ? p.nivel_prioridad : 3;
    grouped[lvl].push(p);
  });

  let html = "";
  [1, 2, 3].forEach((lvl) => {
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
  return `
    <article class="process-card">
      <div>
        <div class="card-meta">
          <span class="badge">${escapeHtml(p.grupo)} · ${escapeHtml(p.sistema || "Proceso")}</span>
          <span class="badge badge-muted">${escapeHtml(p.estado)}</span>
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
        <button class="btn btn-outline" data-open-modal="${escapeHtml(p.id)}">📄 Ver ficha e historial</button>
        <a class="btn btn-outline" href="${escapeHtml(p.url_portal)}" target="_blank" rel="noopener">🔗 Portal</a>
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

  const histHtml = (p.historial || []).length
    ? `<ul>${p.historial.map((h) => `<li>${escapeHtml(h)}</li>`).join("")}</ul>`
    : `<p class="muted">Sin hitos registrados todavía.</p>`;

  // El último apartado debe ser siempre la situación actual del proceso selectivo
  document.getElementById("modal-body").innerHTML = `
    <div>
      <h4>Descripción</h4>
      <p>${escapeHtml(p.descripcion || "—")}</p>
    </div>
    <div>
      <h4>Historial de hitos y publicaciones</h4>
      ${histHtml}
    </div>
    <div class="situacion-box">
      <h4>Situación actual del proceso selectivo</h4>
      <p>${escapeHtml(p.situacion_actual || "Pendiente de actualización.")}</p>
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

async function init() {
  initTheme();
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
  } catch (err) {
    document.getElementById("procesos-container").innerHTML =
      `<div class="panel"><p class="muted">Error cargando data/dashboard.json: ${escapeHtml(err.message)}</p></div>`;
  }
}

init();
