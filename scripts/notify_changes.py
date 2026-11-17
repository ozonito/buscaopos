#!/usr/bin/env python3
"""
Buscaopos Immediate Change Notifier
-----------------------------------
Envía un aviso inmediato por correo electrónico si en la ejecución de hoy
se ha detectado alguna modificación en cualquiera de las convocatorias.
Requiere los secrets: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_TO.
"""

import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = ROOT_DIR / "data" / "dashboard.json"


def main() -> None:
    if not DASHBOARD_FILE.exists():
        print("[INFO] No existe data/dashboard.json. Se omite el aviso.")
        return

    data = json.loads(DASHBOARD_FILE.read_text(encoding="utf-8"))
    today_str = data.get("fecha_legible", "")
    novedades_hoy = [
        n for n in data.get("novedades", []) if n.get("fecha") == today_str
    ]
    fuentes_con_cambios = [
        f for f in data.get("fuentes", []) if f.get("cambio_detectado")
    ]

    if not novedades_hoy and not fuentes_con_cambios:
        print("[INFO] Sin modificaciones hoy en las convocatorias. No se envía aviso.")
        return

    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()
    email_to = os.environ.get("EMAIL_TO", "").strip()
    dashboard_url = os.environ.get(
        "DASHBOARD_URL", "https://ozonito.github.io/buscaopos/"
    ).strip()

    if not all([smtp_host, smtp_user, smtp_pass, email_to]):
        print(
            f"[INFO] Detectadas {len(novedades_hoy)} novedades y {len(fuentes_con_cambios)} fuentes con cambios hoy, "
            "pero faltan secrets SMTP para enviar el aviso por correo."
        )
        return

    nov_html = "".join(
        f"<li><strong>{n.get('fuente', '')}</strong>: "
        f"<a href='{n.get('url', '#')}'>{n.get('titulo', '')}</a> — {n.get('resumen', '')}</li>"
        for n in novedades_hoy
    )
    src_html = "".join(
        f"<li><strong>{f.get('nombre', '')}</strong>: <a href='{f.get('url', '#')}'>{f.get('url', '')}</a></li>"
        for f in fuentes_con_cambios
    )

    html = f"""
    <html><body style="font-family:sans-serif;color:#1e293b;max-width:760px;margin:auto;">
      <h2>🔔 Aviso Buscaopos · Modificación detectada ({today_str})</h2>
      <p>Se han detectado cambios en tus convocatorias vigiladas.
         <a href="{dashboard_url}">Abrir Dashboard en GitHub Pages</a></p>
      {"<h3>📄 Novedades analizadas</h3><ul>" + nov_html + "</ul>" if nov_html else ""}
      {"<h3>🌐 Portales con cambios</h3><ul>" + src_html + "</ul>" if src_html else ""}
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔔 Buscaopos · Modificación en convocatorias ({today_str})"
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [email_to], msg.as_string())
    print(f"[OK] Aviso inmediato enviado a {email_to}")


if __name__ == "__main__":
    main()
