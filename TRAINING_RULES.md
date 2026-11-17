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
*(Añade aquí o mediante GitHub Issues cualquier fallo detectado para que el bot lo tenga en cuenta en futuras ejecuciones).*
