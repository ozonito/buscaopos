# 🌐 WEBS DE SEGUIMIENTO DE OPOSICIONES

Este archivo contiene el listado de páginas web y boletines oficiales que el bot de Buscaopos monitorea diariamente en búsqueda de nuevas convocatorias de oposiciones de técnico (A1 / A2 / C1) y actualizaciones de los procesos activos.

---

## 🏛️ Fuentes de Monitoreo Activas

| Organismo / Fuente | Ámbito / Tipo | Dirección URL | Frecuencia de Actualización | Ficha |
|:---|:---|:---|:---|:---|
| **Boletín Oficial de Canarias (BOC)** | Boletín Autonómico | https://www.gobiernodecanarias.org/boc/ | Diario (Lunes a Viernes) | — |
| **AFT · Administración Tributaria y Financiera** | Funcionario TL (acceso libre) | https://www.gobiernodecanarias.org/administracionespublicas/funcionpublica/acceso/convocatorias-en-curso/2026/Acceso_libre/ficha/ADMINISTRACION-TRIBUTARIA-Y-FINANCIERA-Turno-Libre/ | Periódico | `gobcan_aft_a1_2026` |
| **Boletín Oficial de la Provincia (BOP)** | Boletín Provincial | https://www.boplaspalmas.net/nbop2/index.php | Lunes, Miércoles y Viernes | — |
| **Cabildo de Gran Canaria** | Portal de Empleo Público | https://cabildo.grancanaria.com/ciu/empleo-publico | Periódico | `cabildo_gc_procesos_vigilados` |
| **Cabildo de Gran Canaria (Tablón)** | Tablón de Anuncios (Sede) | https://sede.grancanaria.com/tablon-de-anuncios | Diario | `cabildo_gc_procesos_vigilados` |
| **Autoridad Única del Transporte de Gran Canaria** | Técnico/a de Gestión Administrativa y Digital | https://ferrocarrilesgrancanaria.sedelectronica.es/info.0 | Periódico | `autgc_tecnico_gestion_administrativa` |
| **Ayuntamiento de Las Palmas de Gran Canaria** | Convocatorias en Curso | https://www.laspalmasgc.es/es/ayuntamiento/empleo-publico/convocatorias-en-curso/ | Periódico | — |
| **Ayuntamiento de San Bartolomé de Tirajana** | Portal de Empleo Público | https://www.maspalomas.com/oposicionesyempleo | Periódico | — |
| **Ayuntamiento de Teror** | Funcionario TL | https://teror.sedelectronica.es/board/9753e838-f59b-11de-b600-00237da12c6a/ | Periódico | — |
| **Ayuntamiento de Santa Lucía** | Funcionario | https://www.santaluciagc.com/empleo_publico/convocatorias-para-cubrir-plazas-en-propiedad/ | Periódico | — |
| **Turismo LPA (Ayto)** | Laboral Fijo | https://turismolpa.com/recursos-humanos/ | Periódico | — |
| **ULPGC (Funcionario TL)** | Funcionario TL | https://www.ulpgc.es/spersonal-pas/convocatoriasdepromocioni | Periódico | `ulpgc_a1_escala_tecnica` |
| **ULPGC (Pers. Laboral Fijo)** | Pers. Laboral Fijo | https://www.ulpgc.es/spersonal-pas/personallaboralfijo | Periódico | — |
| **Audiencia de Cuentas de Canarias** | Convocatorias en Curso | https://acuentascanarias.org/empleo-publico/ | Periódico | — |
| **Puertos de Las Palmas** | Convocatorias en Curso | https://www.palmasport.es/es/informacion-publica/ofertas-de-empleo/ | Periódico | — |
| **Valora Gestión Tributaria** | Portal de Empleo Público | https://www.valoragt.com/empleo | Periódico | — |
| **AEAT (Agencia Tributaria)** | Estatal | https://sede.agenciatributaria.gob.es/Sede/trabajar-agencia-tributaria.html | Periódico | — |
| **Boletín Estatal (PAG)** | Boletín Nacional / Recopilatorio | https://administracion.gob.es/pag_Home/empleoPublico/boletin.html | Semanal (Miércoles) | — |

---

## 📝 Instrucciones para Añadir Nuevos Organismos
Si deseas ampliar la vigilancia a otros portales de empleo público (ayuntamientos de la isla, consorcios, organismos autónomos), añade una fila en la tabla de arriba siguiendo el mismo formato. El scraper diario lee dinámicamente este archivo en cada ejecución.
