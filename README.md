# ⚖️ Buscaopos · Seguimiento Diario y Dashboard de Oposiciones

Espacio único en GitHub para el seguimiento diario automático de convocatorias y procesos selectivos (A1 / A2 / C1) en **Gran Canaria y Canarias**, con investigación en el **BOP de Las Palmas**, **BOC** y los portales de `webs.md`.

## 🌐 Acceso al Dashboard
Una vez activado GitHub Pages (rama `main`, carpeta `/docs`), el panel estará disponible en:
- `https://ozonito.github.io/buscaopos/`

## 🏛️ Ordenación por Jerarquía de Administraciones
1. **Gobierno de Canarias** (Nivel 1)
2. **Cabildo de Gran Canaria** y organismos dependientes (Nivel 2)
3. **Ayuntamientos y Otros** (Nivel 3)

Cada organismo admite múltiples procesos selectivos de distintos cuerpos activos simultáneamente, y cada ficha concluye siempre con el apartado **«Situación actual del proceso selectivo»**.

## ⚙️ Configuración en GitHub (Secrets)
En **Settings → Secrets and variables → Actions** del repositorio:
- `GEMINI_API_KEY` *(recomendado)*: Clave de API de Google Gemini para que el bot lea los PDFs del BOP/BOC y actualice automáticamente las fichas y novedades.
- *(Opcional para el resumen semanal por correo)*: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_TO`.

## 🧠 Entrenamiento y corrección de fallos
1. Pulsa **«Reportar fallo / Entrenar»** en el dashboard para abrir un *GitHub Issue* pre-rellenado, o indícame el fallo directamente en el chat.
2. Las reglas aprendidas se guardan en `TRAINING_RULES.md` y `data/feedback_rules.json` para que el bot las aplique en cada ejecución diaria.
