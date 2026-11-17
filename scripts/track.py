#!/usr/bin/env python3
"""
Buscaopos Daily Tracker & AI Investigator
-----------------------------------------
1. Lee las fuentes configuradas en webs.md.
2. Lee las fichas activas en fichas/*.md y las reglas en TRAINING_RULES.md + data/feedback_rules.json.
3. Rastrea las webs y descarga/investiga documentos (HTML y PDF) del BOP de Las Palmas y del BOC.
4. Detecta cambios y coincidencias por palabras clave y, si GEMINI_API_KEY está configurada,
   usa IA para analizar las novedades, descartar falsos positivos según TRAINING_RULES.md
   y actualizar el historial y la 'Situación actual del proceso selectivo' de cada ficha.
5. Genera data/dashboard.json ordenado por prioridad de Administración Pública:
   1. Gobierno de Canarias -> 2. Cabildo de Gran Canaria -> 3. Ayuntamientos y Otros.
"""

import hashlib
import io
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
import urllib3
import yaml
from bs4 import BeautifulSoup
from pypdf import PdfReader

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT_DIR = Path(__file__).resolve().parent.parent
WEBS_FILE = ROOT_DIR / "webs.md"
FICHAS_DIR = ROOT_DIR / "fichas"
DATA_DIR = ROOT_DIR / "data"
RULES_MD_FILE = ROOT_DIR / "TRAINING_RULES.md"
RULES_JSON_FILE = DATA_DIR / "feedback_rules.json"
STATE_FILE = DATA_DIR / "scrape_state.json"
DASHBOARD_FILE = DATA_DIR / "dashboard.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

TIMEOUT = 25


def load_json(path: Path, default: Any) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_webs_md() -> list[dict[str, Any]]:
    """Extrae la tabla de fuentes activas desde webs.md."""
    if not WEBS_FILE.exists():
        return []
    lines = WEBS_FILE.read_text(encoding="utf-8").splitlines()
    sources = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        name_raw, scope, url_raw, freq = parts[0], parts[1], parts[2], parts[3]
        ficha = parts[4] if len(parts) > 4 else "—"
        if name_raw.startswith("Organismo") or name_raw.startswith(":---") or set(name_raw) <= {"-", ":"}:
            continue
        name = re.sub(r"\*\*(.*?)\*\*", r"\1", name_raw).strip()
        # Extract URL from markdown link or <url>
        m = re.search(r"https?://[^\s\)\]>]+", url_raw)
        if not m:
            continue
        url = m.group(0).rstrip(".,;")
        sources.append(
            {
                "nombre": name,
                "ambito": scope,
                "url": url,
                "frecuencia": freq,
                "ficha": ficha.strip("` "),
            }
        )
    return sources


def parse_ficha(path: Path) -> dict[str, Any]:
    """Lee una ficha Markdown con frontmatter YAML y extrae sus secciones."""
    text = path.read_text(encoding="utf-8")
    meta: dict[str, Any] = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()

    sections: dict[str, str] = {}
    current_heading = "_intro"
    buffer: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            sections[current_heading] = "\n".join(buffer).strip()
            current_heading = line[3:].strip()
            buffer = []
        else:
            buffer.append(line)
    sections[current_heading] = "\n".join(buffer).strip()

    def clean_md_text(s: str) -> str:
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
        return s.strip()

    situacion_actual = clean_md_text(sections.get("Situación actual del proceso selectivo", ""))
    historial_raw = sections.get("Historial de hitos y publicaciones", "")
    historial = [
        clean_md_text(ln.lstrip("- ").strip())
        for ln in historial_raw.splitlines()
        if ln.strip().startswith("-")
    ]

    return {
        "id": meta.get("id", path.stem),
        "archivo": f"fichas/{path.name}",
        "titulo": meta.get("titulo", path.stem),
        "administracion": meta.get("administracion", "Ayuntamientos y Otros"),
        "nivel_prioridad": int(meta.get("nivel_prioridad", 3)),
        "organismo": meta.get("organismo", meta.get("administracion", "")),
        "cuerpo": meta.get("cuerpo", ""),
        "grupo": meta.get("grupo", "A1/A2/C1"),
        "sistema": meta.get("sistema", ""),
        "estado": meta.get("estado", "A la espera de publicación de novedades"),
        "url_portal": meta.get("url_portal", ""),
        "ultimo_documento_url": meta.get("ultimo_documento_url", ""),
        "ultimo_documento_titulo": meta.get("ultimo_documento_titulo", ""),
        "ultimo_documento_fecha": str(meta.get("ultimo_documento_fecha", "")),
        "fecha_examen": str(meta.get("fecha_examen", "")),
        "hora_llamamiento": str(meta.get("hora_llamamiento", "")),
        "keywords": meta.get("keywords", []),
        "ultima_revision": str(meta.get("ultima_revision", "")),
        "descripcion": sections.get("Descripción del proceso", ""),
        "fuentes_texto": sections.get("Fuentes oficiales de seguimiento", ""),
        "historial": historial,
        "situacion_actual": situacion_actual,
        "_raw_meta": meta,
        "_sections": sections,
    }


def update_ficha_file(
    ficha_path: Path,
    new_estado: str | None,
    new_hito: str | None,
    new_situacion: str | None,
    today_str: str,
    ultimo_doc_url: str | None = None,
    ultimo_doc_titulo: str | None = None,
    ultimo_doc_fecha: str | None = None,
    fecha_examen: str | None = None,
    hora_llamamiento: str | None = None,
) -> None:
    """Actualiza una ficha .md manteniendo siempre 'Situación actual del proceso selectivo' al final."""
    ficha = parse_ficha(ficha_path)
    meta = ficha["_raw_meta"]
    meta["ultima_revision"] = today_str
    if new_estado:
        meta["estado"] = new_estado
    if ultimo_doc_url:
        meta["ultimo_documento_url"] = ultimo_doc_url
    if ultimo_doc_titulo:
        meta["ultimo_documento_titulo"] = ultimo_doc_titulo
    if ultimo_doc_fecha:
        meta["ultimo_documento_fecha"] = ultimo_doc_fecha
    if fecha_examen:
        meta["fecha_examen"] = fecha_examen
    if hora_llamamiento:
        meta["hora_llamamiento"] = hora_llamamiento

    sections = ficha["_sections"]
    if new_hito:
        hist = sections.get("Historial de hitos y publicaciones", "").strip()
        entry = f"- **{today_str}**: {new_hito}"
        if new_hito not in hist:
            sections["Historial de hitos y publicaciones"] = (
                f"{entry}\n{hist}" if hist else entry
            )
    if new_situacion:
        sections["Situación actual del proceso selectivo"] = new_situacion.strip()

    # Reassemble markdown keeping 'Situación actual del proceso selectivo' strictly last
    ordered_keys = [
        "Descripción del proceso",
        "Fuentes oficiales de seguimiento",
        "Historial de hitos y publicaciones",
    ]
    for k in sections:
        if k not in ordered_keys and k not in ("_intro", "Situación actual del proceso selectivo"):
            ordered_keys.append(k)
    ordered_keys.append("Situación actual del proceso selectivo")

    yaml_str = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip()
    parts = [f"---\n{yaml_str}\n---"]
    for k in ordered_keys:
        if k in sections and sections[k].strip():
            parts.append(f"## {k}\n{sections[k].strip()}")

    ficha_path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")


def fetch_url(url: str) -> tuple[int, str, bytes]:
    """Descarga una URL devolviendo (status_code, content_type, content_bytes)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False, allow_redirects=True)
        ctype = resp.headers.get("Content-Type", "").lower()
        return resp.status_code, ctype, resp.content
    except Exception as exc:
        return 0, f"error: {exc}", b""


def extract_text_from_html(html_bytes: bytes, base_url: str) -> tuple[str, list[dict[str, str]]]:
    """Extrae texto limpio y enlaces relevantes (especialmente PDFs y resoluciones)."""
    soup = BeautifulSoup(html_bytes, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        label = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        full_url = urljoin(base_url, href)
        links.append({"text": label[:180], "url": full_url})
    return text, links


def extract_text_from_pdf(pdf_bytes: bytes, max_pages: int = 12) -> str:
    """Extrae texto de un PDF usando pypdf."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        chunks = []
        for page in reader.pages[:max_pages]:
            txt = page.extract_text() or ""
            if txt.strip():
                chunks.append(txt)
        return re.sub(r"\s+", " ", "\n".join(chunks))
    except Exception:
        return ""


def investigate_bulletin(
    name: str,
    url: str,
    links: list[dict[str, str]],
    rules: dict[str, Any],
    fichas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Investiga enlaces recientes dentro del BOP de Las Palmas o BOC,
    descargando hasta 5 documentos/PDFs que coincidan con palabras clave.
    """
    findings = []
    all_keywords = set(k.lower() for k in rules.get("include_keywords", []))
    for f in fichas:
        for kw in f.get("keywords", []):
            all_keywords.add(kw.lower())
    exclude_kw = [k.lower() for k in rules.get("exclude_keywords", [])]

    candidate_links = []
    for lk in links:
        txt_low = lk["text"].lower()
        url_low = lk["url"].lower()
        if any(ex in txt_low for ex in exclude_kw):
            continue
        is_pdf = ".pdf" in url_low
        is_relevant_text = any(kw in txt_low for kw in all_keywords)
        is_bulletin_doc = any(
            token in url_low for token in ["boc-", "/boc/", "bop", "sumario", "ver_pdf", "anuncio"]
        )
        if is_relevant_text or (is_pdf and is_bulletin_doc):
            candidate_links.append(lk)

    # Deduplicate and limit to avoid long runs
    seen_urls = set()
    checked = 0
    for lk in candidate_links:
        if lk["url"] in seen_urls or checked >= 5:
            continue
        seen_urls.add(lk["url"])
        checked += 1
        status, ctype, content = fetch_url(lk["url"])
        if status != 200 or not content:
            continue
        doc_text = ""
        if "pdf" in ctype or lk["url"].lower().endswith(".pdf"):
            doc_text = extract_text_from_pdf(content)
        elif "html" in ctype:
            doc_text, _ = extract_text_from_html(content, lk["url"])

        if doc_text:
            doc_low = doc_text.lower()
            matched = [kw for kw in all_keywords if kw in doc_low]
            if matched:
                findings.append(
                    {
                        "fuente": name,
                        "titulo": lk["text"] or lk["url"],
                        "url": lk["url"],
                        "keywords_detectadas": matched[:8],
                        "extracto": doc_text[:1200],
                    }
                )
    return findings


def analyze_with_gemini(
    api_key: str,
    fichas: list[dict[str, Any]],
    changed_sources: list[dict[str, Any]],
    bulletin_findings: list[dict[str, Any]],
    training_rules_md: str,
    today_str: str,
) -> dict[str, Any] | None:
    """Envía las novedades detectadas a Gemini para análisis estructurado."""
    if not api_key or (not changed_sources and not bulletin_findings):
        return None

    fichas_summary = [
        {
            "id": f["id"],
            "titulo": f["titulo"],
            "organismo": f["organismo"],
            "cuerpo": f["cuerpo"],
            "grupo": f["grupo"],
            "estado": f["estado"],
            "solo_lista_reserva": bool(f["_raw_meta"].get("solo_lista_reserva", False)),
            "situacion_actual": f["situacion_actual"],
        }
        for f in fichas
    ]

    prompt = f"""Eres el asistente experto de Buscaopos (fecha de hoy: {today_str}).
Tu tarea es analizar EN PROFUNDIDAD las novedades y documentos publicados hoy en los portales web, en el BOP de Las Palmas y en el BOC de Canarias.

REGLAS OBLIGATORIAS:
1. Si una ficha tiene "solo_lista_reserva": true, NO generes novedades ni actualizaciones salvo que se publique explícitamente la LISTA DE RESERVA.
1. El campo "nuevo_estado" NO puede referirse nunca a la tarea del bot (PROHIBIDO usar "En seguimiento", "Vigilado", "Rastreando", etc.). Debe reflejar la FASE ADMINISTRATIVA REAL de la convocatoria, por ejemplo:
   - "A la espera del término del plazo de presentación de instancias"
   - "Publicada relación provisional de admitidos/excluidos; a la espera de lista definitiva"
   - "Publicada relación definitiva de admitidos; a la espera de fecha de examen"
   - "Convocado primer/segundo/tercer ejercicio (fecha y llamamiento publicados)"
   - "A la espera de las calificaciones provisionales"
   - "A la espera de las calificaciones definitivas"
   - "En fase de concurso / valoración de méritos"
   - "Pendiente de nombramiento"
2. Analiza en profundidad cada documento publicado, ordena los hitos por fecha y haz especial referencia al ÚLTIMO documento publicado en "nueva_situacion_actual", devolviendo su URL directa en "ultimo_documento_url".
3. Si en algún documento se estima o convoca una fecha de examen, extrae "fecha_examen" (YYYY-MM-DD) y "hora_llamamiento" (ej. "09:30").

REGLAS DE ENTRENAMIENTO DEL USUARIO:
{training_rules_md[:3000]}

PROCESOS SELECTIVOS ACTIVOS ACTUALMENTE:
{json.dumps(fichas_summary, ensure_ascii=False, indent=2)}

CAMBIOS DETECTADOS EN PORTALES WEB:
{json.dumps(changed_sources, ensure_ascii=False, indent=2)[:6000]}

DOCUMENTOS INVESTIGADOS EN BOP / BOC:
{json.dumps(bulletin_findings, ensure_ascii=False, indent=2)[:8000]}

Devuelve EXCLUSIVAMENTE un JSON válido (sin markdown ```json) con esta estructura:
{{
  "novedades": [
    {{
      "fecha": "{today_str}",
      "fuente": "Nombre de la web o boletín",
      "titulo": "Resumen corto de la novedad",
      "url": "URL directa del documento",
      "ficha_id": "id de la ficha relacionada o null si es nueva convocatoria",
      "relevancia": "alta|media|baja",
      "resumen": "Explicación detallada del documento publicado y qué implica para el proceso"
    }}
  ],
  "actualizaciones_fichas": [
    {{
      "ficha_id": "id de la ficha a actualizar",
      "nuevo_estado": "Fase administrativa real del proceso (nunca 'En seguimiento')",
      "nuevo_hito": "Texto corto del hito con enlace o referencia al documento",
      "nueva_situacion_actual": "Párrafo claro haciendo especial referencia al último documento publicado y a qué fase se espera ahora",
      "ultimo_documento_url": "URL directa del último documento publicado",
      "ultimo_documento_titulo": "Título del último documento",
      "ultimo_documento_fecha": "YYYY-MM-DD",
      "fecha_examen": "YYYY-MM-DD o null",
      "hora_llamamiento": "HH:MM o null"
    }}
  ]
}}
Si no hay novedades relevantes tras aplicar las reglas de entrenamiento, devuelve {{"novedades": [], "actualizaciones_fichas": []}}.
"""

    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={api_key}"
    )
    try:
        resp = requests.post(
            endpoint,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=45,
        )
        if resp.status_code != 200:
            print(f"[WARN] Gemini API returned {resp.status_code}: {resp.text[:200]}")
            return None
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.DOTALL).strip()
        return json.loads(raw_text)
    except Exception as exc:
        print(f"[WARN] Error calling/parsing Gemini: {exc}")
        return None


def main() -> None:
    now_utc = datetime.now(timezone.utc)
    today_str = now_utc.strftime("%Y-%m-%d")
    now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    rules_json = load_json(RULES_JSON_FILE, {})
    training_rules_md = (
        RULES_MD_FILE.read_text(encoding="utf-8") if RULES_MD_FILE.exists() else ""
    )
    prev_state = load_json(STATE_FILE, {"hashes": {}, "novedades": [], "last_checked": {}})
    prev_hashes: dict[str, str] = prev_state.get("hashes", {})
    prev_last_checked: dict[str, str] = prev_state.get("last_checked", {})

    sources = parse_webs_md()
    ficha_files = sorted(FICHAS_DIR.glob("*.md"))
    fichas = [parse_ficha(p) for p in ficha_files]
    ficha_by_id = {f["id"]: f for f in fichas}

    source_statuses = []
    changed_sources = []
    bulletin_findings = []
    new_hashes = dict(prev_hashes)
    new_last_checked = dict(prev_last_checked)

    for src in sources:
        url = src["url"]
        linked_ficha = ficha_by_id.get(src["ficha"])
        is_monthly = "mensual" in src["frecuencia"].lower() or (
            linked_ficha and bool(linked_ficha["_raw_meta"].get("solo_lista_reserva", False))
        )
        last_chk_str = prev_last_checked.get(url, "")
        if is_monthly and last_chk_str:
            try:
                days_since = (now_utc.date() - datetime.strptime(last_chk_str, "%Y-%m-%d").date()).days
                if days_since < 30:
                    source_statuses.append(
                        {
                            "nombre": src["nombre"],
                            "ambito": src["ambito"],
                            "url": url,
                            "frecuencia": "Mensual (Lista de reserva)" if (linked_ficha and linked_ficha["_raw_meta"].get("solo_lista_reserva")) else src["frecuencia"],
                            "ficha": src["ficha"],
                            "http_status": 200,
                            "estado_rastreo": "ok",
                            "cambio_detectado": False,
                            "ultima_comprobacion": f"{last_chk_str} (próxima en {30 - days_since}d)",
                        }
                    )
                    continue
            except ValueError:
                pass

        new_last_checked[url] = today_str
        status, ctype, content = fetch_url(url)
        ok = 200 <= status < 400 and len(content) > 0
        text_sample = ""
        changed = False

        if ok and "html" in ctype:
            clean_text, links = extract_text_from_html(content, url)
            content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()[:16]
            old_hash = prev_hashes.get(url)
            if old_hash and old_hash != content_hash:
                changed = True
            new_hashes[url] = content_hash
            text_sample = clean_text[:2000]

            if changed:
                changed_sources.append(
                    {
                        "nombre": src["nombre"],
                        "url": url,
                        "extracto": text_sample,
                        "enlaces_destacados": links[:12],
                    }
                )

            # Deep investigation for BOP Las Palmas and BOC
            if "boplaspalmas.net" in url or "gobiernodecanarias.org/boc" in url:
                found = investigate_bulletin(src["nombre"], url, links, rules_json, fichas)
                bulletin_findings.extend(found)
        elif ok:
            content_hash = hashlib.sha256(content).hexdigest()[:16]
            if prev_hashes.get(url) and prev_hashes.get(url) != content_hash:
                changed = True
            new_hashes[url] = content_hash

        source_statuses.append(
            {
                "nombre": src["nombre"],
                "ambito": src["ambito"],
                "url": url,
                "frecuencia": src["frecuencia"],
                "ficha": src["ficha"],
                "http_status": status,
                "estado_rastreo": "ok" if ok else "error",
                "cambio_detectado": changed,
                "ultima_comprobacion": now_iso,
            }
        )

    # AI analysis if GEMINI_API_KEY is present
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    ai_result = analyze_with_gemini(
        gemini_key, fichas, changed_sources, bulletin_findings, training_rules_md, today_str
    )

    new_novedades = list(prev_state.get("novedades", []))
    if ai_result:
        for nov in ai_result.get("novedades", []):
            new_novedades.insert(0, nov)
        for upd in ai_result.get("actualizaciones_fichas", []):
            fid = upd.get("ficha_id")
            target_path = FICHAS_DIR / f"{fid}.md"
            if target_path.exists():
                update_ficha_file(
                    target_path,
                    upd.get("nuevo_estado"),
                    upd.get("nuevo_hito"),
                    upd.get("nueva_situacion_actual"),
                    today_str,
                )
    else:
        # Deterministic fallback novedades when changes/bulletin matches are detected without AI
        for bf in bulletin_findings:
            new_novedades.insert(
                0,
                {
                    "fecha": today_str,
                    "fuente": bf["fuente"],
                    "titulo": f"Coincidencia en boletín: {bf['titulo'][:100]}",
                    "url": bf["url"],
                    "ficha_id": None,
                    "relevancia": "media",
                    "resumen": f"Palabras clave detectadas: {', '.join(bf['keywords_detectadas'])}.",
                },
            )

    # Keep latest 50 novedades deduplicated by (fecha, url, titulo)
    dedup_nov = []
    seen_nov = set()
    for n in new_novedades:
        key = (n.get("fecha", ""), n.get("url", ""), n.get("titulo", ""))
        if key not in seen_nov:
            seen_nov.add(key)
            dedup_nov.append(n)
    dedup_nov = dedup_nov[:50]

    # Reload fichas after potential AI updates and sort strictly by Administration Priority
    fichas_final = [
        parse_ficha(p)
        for p in sorted(FICHAS_DIR.glob("*.md"))
        if parse_ficha(p)["_raw_meta"].get("activo", True) is not False
    ]
    fichas_final.sort(key=lambda x: (x["nivel_prioridad"], x["organismo"], x["titulo"]))

    # Remove internal fields before serializing
    procesos_out = []
    for f in fichas_final:
        procesos_out.append(
            {
                "id": f["id"],
                "archivo": f["archivo"],
                "titulo": f["titulo"],
                "administracion": f["administracion"],
                "nivel_prioridad": f["nivel_prioridad"],
                "organismo": f["organismo"],
                "cuerpo": f["cuerpo"],
                "grupo": f["grupo"],
                "sistema": f["sistema"],
                "estado": f["estado"],
                "url_portal": f["url_portal"],
                "ultimo_documento_url": f["ultimo_documento_url"],
                "ultimo_documento_titulo": f["ultimo_documento_titulo"],
                "ultimo_documento_fecha": f["ultimo_documento_fecha"],
                "fecha_examen": f["fecha_examen"],
                "hora_llamamiento": f["hora_llamamiento"],
                "keywords": f["keywords"],
                "ultima_revision": f["ultima_revision"],
                "descripcion": f["descripcion"],
                "historial": f["historial"],
                "situacion_actual": f["situacion_actual"],
            }
        )

    dashboard_payload = {
        "ultima_actualizacion": now_iso,
        "fecha_legible": today_str,
        "ia_activa": bool(gemini_key),
        "resumen": {
            "total_procesos": len(procesos_out),
            "total_fuentes": len(source_statuses),
            "fuentes_ok": sum(1 for s in source_statuses if s["estado_rastreo"] == "ok"),
            "novedades_recientes": len(dedup_nov),
        },
        "procesos": procesos_out,
        "novedades": dedup_nov,
        "fuentes": source_statuses,
        "reglas_entrenamiento_url": "TRAINING_RULES.md",
    }

    save_json(
        STATE_FILE,
        {"hashes": new_hashes, "novedades": dedup_nov, "last_checked": new_last_checked},
    )
    save_json(DASHBOARD_FILE, dashboard_payload)
    # Also copy dashboard.json to docs/data/dashboard.json so GitHub Pages serves it cleanly
    save_json(ROOT_DIR / "docs" / "data" / "dashboard.json", dashboard_payload)
    print(f"[OK] Dashboard actualizado: {len(procesos_out)} procesos, {len(source_statuses)} fuentes.")


if __name__ == "__main__":
    main()
