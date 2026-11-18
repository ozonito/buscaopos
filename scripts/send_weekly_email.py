#!/usr/bin/env python3
"""
Buscaopos Weekly Email Digest
-----------------------------
Envía un correo semanal en HTML con el resumen de novedades y la situación actual
de los procesos selectivos, enlazando al Dashboard de GitHub Pages.
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
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_port = int((os.environ.get("SMTP_PORT") or "587").strip())
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()
    email_to = os.environ.get("EMAIL_TO", "").strip()
    dashboard_url = os.environ.get(
        "DASHBOARD_URL", "https://ozonito.github.io/buscaopos/"
    ).strip()

    if not all([smtp_host, smtp_user, smtp_pass, email_to]):
        print("[INFO] Credenciales SMTP no configuradas. Se omite el envío semanal.")
        return

    data = json.loads(DASHBOARD_FILE.read_text(encoding="utf-8"))
    procesos = data.get("procesos", [])
    novedades = data.get("novedades", [])[:10]

    nov_html = "".join(
        f"<li><strong>[{n.get('fecha','')}] {n.get('fuente','')}</strong>: "
        f"<a href='{n.get('url','#')}'>{n.get('titulo','')}</a> — {n.get('resumen','')}</li>"
        for n in novedades
    ) or "<li>Sin novedades destacadas esta semana.</li>"

    proc_html = "".join(
        f"<tr>"
        f"<td style='padding:8px;border:1px solid #ddd;'><strong>{p['administracion']}</strong><br><small>{p['organismo']}</small></td>"
        f"<td style='padding:8px;border:1px solid #ddd;'>{p['titulo']}<br><small>{p['cuerpo']} ({p['grupo']})</small></td>"
        f"<td style='padding:8px;border:1px solid #ddd;'><strong>{p['estado']}</strong><br>{p['situacion_actual']}</td>"
        f"</tr>"
        for p in procesos
    )

    html = f"""
    <html><body style="font-family:sans-serif;color:#1e293b;max-width:760px;margin:auto;">
      <h2>📋 Resumen Semanal Buscaopos</h2>
      <p>Última actualización: <strong>{data.get('fecha_legible','')}</strong> ·
         <a href="{dashboard_url}">Abrir Dashboard Completo en GitHub Pages</a></p>
      <h3>🔔 Novedades recientes</h3>
      <ul>{nov_html}</ul>
      <h3>🏛️ Situación actual de tus procesos (por prioridad)</h3>
      <table style="border-collapse:collapse;width:100%;font-size:14px;">
        <thead>
          <tr style="background:#f1f5f9;">
            <th style="padding:8px;border:1px solid #ddd;text-align:left;">Administración</th>
            <th style="padding:8px;border:1px solid #ddd;text-align:left;">Proceso / Cuerpo</th>
            <th style="padding:8px;border:1px solid #ddd;text-align:left;">Situación actual</th>
          </tr>
        </thead>
        <tbody>{proc_html}</tbody>
      </table>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Buscaopos · Resumen semanal ({data.get('fecha_legible', '')})"
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [email_to], msg.as_string())
    print(f"[OK] Resumen semanal enviado a {email_to}")


if __name__ == "__main__":
    main()
