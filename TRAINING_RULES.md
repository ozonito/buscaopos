# 🧠 Reglas de Entrenamiento y Corrección de Fallos (Buscaopos)

Este documento recoge las instrucciones, correcciones de fallos y criterios de filtrado que vas indicando para entrenar al bot de Buscaopos.
El script diario (`scripts/track.py`) inyecta estas reglas en el análisis con IA y aplica las reglas estructuradas de `data/feedback_rules.json` en cada ejecución.

## 📌 Criterios Generales de Priorización y Ordenación
1. **Jerarquía de Administraciones Públicas** (de mayor a menor importancia):
   - **Nivel 1 — Gobierno de Canarias** (y organismos autonómicos principales).
   - **Nivel 2 — Cabildo de Gran Canaria** (y sus organismos/consorcios dependientes como AUTGC o Valora Gestión Tributaria).
   - **Nivel 3 — Ayuntamientos y Otros** (Ayuntamientos de Gran Canaria, ULPGC, Puertos de Las Palmas, Audiencia de Cuentas, AEAT, etc.).
2. **Múltiples procesos por organismo**: Un mismo organismo puede tener varios procesos selectivos de distintos cuerpos/grupos activos simultáneamente. Cada proceso debe mantenerse separado en su propia ficha sin mezclar estados ni fechas.
3. **Grupos de interés**: Priorizar cuerpos técnicos **A1, A2 y C1** (especialmente gestión administrativa, jurídica, económica, tributaria, técnica y digital).

## 🚫 Falsos Positivos / Exclusiones Aprendidas
- Ignorar convocatorias exclusivamente de personal laboral temporal de oficios, peones, operarios o bolsas de empleo ajenas a grupos A1/A2/C1, salvo que pertenezcan a un proceso ya vigilado.
- En el BOP de Las Palmas y el BOC, distinguir claramente entre **bases/convocatoria**, **lista provisional/definitiva de admitidos y excluidos**, **nombramiento de tribunal**, **fecha de examen**, **calificaciones** y **nombramiento**.

## 📝 Historial de Correcciones del Usuario
- **2026-11-17 · Estado real de la convocatoria**: El campo `estado` NO puede referirse a la tarea del bot (nunca usar `"En seguimiento"`, `"Vigilado"` o similar). Debe expresar la fase administrativa real: ej. *"A la espera del término del plazo de presentación de instancias"*, *"Publicada relación de admitidos; a la espera de fecha de examen"*, *"A la espera de calificaciones provisionales"*, etc.
- **2026-11-17 · Análisis documental ordenado y enlace rápido**: Analizar en profundidad todos los documentos publicados en cada convocatoria, ordenados cronológicamente por fecha, haciendo especial referencia al último documento y enlazándolo directamente (`ultimo_documento_url`) para acceso rápido en el dashboard.
- **2026-11-17 · Avisos inmediatos**: Enviar un aviso por correo electrónico cada vez que se produzca una modificación en cualquiera de las convocatorias.
- **2026-11-17 · Google Calendar para exámenes**: Si se estima o convoca una fecha de examen, crear una tarea/evento de día completo en Google Calendar con al menos dos semanas de antelación que dure las dos semanas previas al examen para verlo todos los días, incluyendo en el título la hora del llamamiento.
- **2026-11-17 · Tema oscuro siempre**: El dashboard web debe mostrarse siempre en tema oscuro.
- **2026-11-17 · Frecuencia mensual en lista de reserva**: Si un proceso está suspendido y solo queda a la espera de la lista de reserva (`solo_lista_reserva: true`), reducir su comprobación web a una frecuencia **mensual** (cada 30 días).

