#!/usr/bin/env python3
"""
Buscaopos Mobile Issue Processor
--------------------------------
Procesa automáticamente los GitHub Issues abiertos por el propietario del repo
desde el Dashboard (altas, bajas de procesos y reglas de entrenamiento),
actualiza fichas/, webs.md, TRAINING_RULES.md y regenera dashboard.json.
"""

import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import yaml

import track as t

ROOT_DIR = Path(__file__).resolve().parent.parent


def slugify(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", norm.lower()).strip("_")
    return slug[:60] or "nuevo_proceso"


def rebuild_dashboard() -> None:
    fichas = [
        t.parse_ficha(p)
        for p in sorted(t.FICHAS_DIR.glob("*.md"))
        if t.parse_ficha(p)["_raw_meta"].get("activo", True) is not False
    ]
    fichas.sort(key=lambda x: (x["nivel_prioridad"], x["organismo"], x["titulo"]))
    procesos_out = [
        {
            k: f[k]
            for k in [
                "id",
                "archivo",
                "titulo",
                "administracion",
                "nivel_prioridad",
                "organismo",
                "cuerpo",
                "grupo",
                "sistema",
                "estado",
                "url_portal",
                "ultimo_documento_url",
                "ultimo_documento_titulo",
                "ultimo_documento_fecha",
                "fecha_examen",
                "hora_llamamiento",
                "keywords",
                "ultima_revision",
                "descripcion",
                "historial",
                "situacion_actual",
            ]
        }
        for f in fichas
    ]
    for path in [t.DASHBOARD_FILE, t.ROOT_DIR / "docs" / "data" / "dashboard.json"]:
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
        else:
            d = {"novedades": [], "fuentes": [], "resumen": {}}
        d["procesos"] = procesos_out
        d["resumen"]["total_procesos"] = len(procesos_out)
        t.save_json(path, d)


def handle_baja(body: str, today_str: str) -> str:
    ids = re.findall(r"`([a-zA-Z0-9_\-]+)`", body)
    updated = []
    for fid in ids:
        p = t.FICHAS_DIR / f"{fid}.md"
        if not p.exists():
            continue
        ficha = t.parse_ficha(p)
        meta = ficha["_raw_meta"]
        meta["activo"] = False
        meta["ultima_revision"] = today_str
        yaml_str = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip()
        sections = ficha["_sections"]
        ordered = [k for k in sections if k not in ("_intro", "Situación actual del proceso selectivo")]
        ordered.append("Situación actual del proceso selectivo")
        parts = [f"---\n{yaml_str}\n---"]
        for k in ordered:
            if k in sections and sections[k].strip():
                parts.append(f"## {k}\n{sections[k].strip()}")
        p.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
        updated.append(fid)

    if updated:
        rebuild_dashboard()
        return f"Procesos desactivados (`activo: false`): {', '.join(updated)}. Las webs siguen activas en `webs.md`."
    return "No se encontró ninguna ficha coincidente para desactivar."


def handle_nuevo_proceso(title: str, body: str, today_str: str) -> str:
    def extract_field(label: str) -> str:
        m = re.search(rf"\*\*{re.escape(label)}\*\*:\s*(.+)", body)
        return m.group(1).strip().strip("`") if m else ""

    grupo = extract_field("Cuerpo / Grupo") or "A1"
    admin_raw = extract_field("Administración") or "Ayuntamientos y Otros (Nivel 3)"
    organismo = extract_field("Organismo convocante") or "Organismo público"
    proceso = extract_field("Proceso / Plaza") or re.sub(r"^\[Nuevo proceso\]\s*", "", title).strip()
    web = extract_field("Web de la administración")

    nivel = 3
    admin = "Ayuntamientos y Otros"
    if "Nivel 1" in admin_raw or "Gobierno de Canarias" in admin_raw:
        nivel, admin = 1, "Gobierno de Canarias"
    elif "Nivel 2" in admin_raw or "Cabildo" in admin_raw:
        nivel, admin = 2, "Cabildo de Gran Canaria"

    fid = slugify(f"{organismo}_{grupo}_{proceso}")
    ficha_path = t.FICHAS_DIR / f"{fid}.md"

    meta = {
        "id": fid,
        "titulo": f"{proceso} · {organismo}",
        "administracion": admin,
        "nivel_prioridad": nivel,
        "organismo": organismo,
        "cuerpo": proceso,
        "grupo": grupo,
        "sistema": "Proceso selectivo",
        "estado": "A la espera de nuevas publicaciones en la web oficial",
        "activo": True,
        "url_portal": web,
        "keywords": [organismo, proceso, grupo],
        "ultima_revision": today_str,
    }
    yaml_str = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip()
    content = (
        f"---\n{yaml_str}\n---\n\n"
        f"## Descripción del proceso\n"
        f"Proceso selectivo para {proceso} ({grupo}) convocado por {organismo}.\n\n"
        f"## Fuentes oficiales de seguimiento\n"
        f"- **Web oficial**: [{organismo}]({web})\n\n"
        f"## Historial de hitos y publicaciones\n"
        f"- **{today_str}**: Alta solicitada desde el dashboard.\n\n"
        f"## Situación actual del proceso selectivo\n"
        f"Proceso dado de alta y pendiente del próximo rastreo diario automático para analizar los documentos publicados.\n"
    )
    ficha_path.write_text(content, encoding="utf-8")

    # Add to webs.md if URL not already present
    if web and t.WEBS_FILE.exists():
        webs_txt = t.WEBS_FILE.read_text(encoding="utf-8")
        if web not in webs_txt:
            new_row = f"| **{organismo}** | {proceso} ({grupo}) | {web} | Diario | `{fid}` |\n"
            webs_txt = webs_txt.replace("\n---\n\n## 📝", f"\n{new_row}\n---\n\n## 📝")
            t.WEBS_FILE.write_text(webs_txt, encoding="utf-8")

    rebuild_dashboard()
    return f"Alta completada: creada ficha `fichas/{fid}.md` y añadida la fuente a `webs.md`."


def handle_training_rule(title: str, body: str, today_str: str) -> str:
    clean_title = re.sub(r"^\[Entrenamiento\]\s*", "", title).strip()
    summary_lines = [ln.strip() for ln in body.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    summary = " ".join(summary_lines)[:350]
    entry = f"- **{today_str} · {clean_title}**: {summary}\n"
    if t.RULES_MD_FILE.exists():
        txt = t.RULES_MD_FILE.read_text(encoding="utf-8")
        t.RULES_MD_FILE.write_text(txt.rstrip() + "\n" + entry, encoding="utf-8")
    return "Regla añadida a `TRAINING_RULES.md` para futuras ejecuciones."


def main() -> None:
    title = os.environ.get("ISSUE_TITLE", "").strip()
    body = os.environ.get("ISSUE_BODY", "").strip()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if title.startswith("[Baja"):
        msg = handle_baja(body, today_str)
    elif title.startswith("[Nuevo proceso]"):
        msg = handle_nuevo_proceso(title, body, today_str)
    else:
        msg = handle_training_rule(title, body, today_str)

    print(msg)
    summary_file = os.environ.get("RESULT_FILE")
    if summary_file:
        Path(summary_file).write_text(msg, encoding="utf-8")


if __name__ == "__main__":
    main()
