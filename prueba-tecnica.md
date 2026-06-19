# Prueba Técnica — AI Support Ticket Analyzer

¡Hola! Gracias por tu interés en sumarte al equipo. Esta prueba está pensada
para que muestres cómo **razonas un problema, decides qué tecnología usar y
entregas algo funcional**. No buscamos perfección ni un producto pulido: nos
interesa tu criterio, tu autonomía y tu forma de trabajar.

Tienes total libertad de stack. Usa las herramientas con las que seas más
productivo.

---

## El caso

Una empresa recibe a diario tickets de soporte de sus clientes. Hoy el equipo
los revisa de forma manual: leer, clasificar y priorizar toma mucho tiempo.

Tu misión es construir un **analizador de tickets con IA** que reciba esos
tickets, los procese automáticamente y permita entenderlos de un vistazo a
través de un dashboard.

Te entregamos los datos en `dataset/tickets.csv` (revisa también
`dataset/diccionario-de-datos.md`).

> **Sobre los datos:** provienen de una exportación real de un sistema de
> soporte. Como suele pasar en producción, no son perfectos: puede haber
> valores faltantes, formatos distintos o inconsistencias. Forma parte del
> ejercicio decidir qué hacer con eso.

---

## Qué debes construir

### 1. Backend / API
Un servicio que exponga, como mínimo:

- Cargar / ingerir los tickets desde el archivo de datos.
- Listar los tickets ya analizados (con los campos enriquecidos por IA).
- Devolver un resumen con métricas agregadas.
- Un endpoint `/ask` que permita **hacer preguntas en lenguaje natural** sobre
  los tickets (ej.: *"¿cuáles son los problemas más críticos esta semana?"*,
  *"¿qué producto genera más quejas?"*).

### 2. IA aplicada al producto
Para cada ticket, usando un modelo de lenguaje, genera al menos:

- **Categoría** sugerida.
- **Prioridad** sugerida.
- **Resumen** corto del problema.
- **Sentimiento / urgencia** del cliente.
- **Equipo responsable** sugerido (ej.: Soporte Técnico, Facturación, etc.).

El endpoint `/ask` debe apoyarse en el contenido de los tickets y en una
**base de conocimiento simple** (ver punto 3).

### 3. Base de conocimiento
Crea una base de conocimiento sencilla que la IA pueda consultar para responder
mejor (por ejemplo: políticas de soporte, SLAs, guía de a qué equipo va cada
tipo de problema). El formato es libre: markdown, JSON, SQLite, una pequeña
base vectorial, lo que prefieras. Lo importante es que `/ask` la **utilice**.

### 4. Dashboard
Una interfaz visual que muestre los resultados. Como mínimo:

- Tabla de tickets con sus campos enriquecidos.
- Filtros básicos (por categoría, prioridad, estado, etc.).
- KPIs principales (total de tickets, prioridad alta/crítica, categorías
  más frecuentes, clientes/productos más afectados…).
- Al menos una visualización gráfica (barras, pastel, línea, etc.).

### 5. Deploy local
Debemos poder **clonar tu repositorio, levantarlo y probarlo** siguiendo tu
README. Docker / Docker Compose es un plus, pero no obligatorio: si prefieres
comandos directos (`pip install`, `npm install`, etc.), perfecto, siempre que
estén claros y funcionen.

---

## Sobre el modelo de IA

- Puedes usar el proveedor que quieras: OpenAI, Anthropic, Gemini, modelos
  locales (Ollama), etc.
- **No es obligatorio que gastes en una API de pago.** Si no quieres usar una
  key real, está perfectamente bien implementar un **modo "mock"** (respuestas
  simuladas) siempre que la arquitectura permita conectar un LLM real
  fácilmente. Déjalo documentado.
- Si usas API keys, **no las subas al repositorio.** Usa variables de entorno y
  documenta cuáles se necesitan.

---

## Entregables

1. **Repositorio Git** con todo el código.
2. **`README.md`** que incluya:
   - Cómo instalar.
   - Cómo correr el proyecto.
   - Cómo probarlo (qué endpoints llamar, cómo abrir el dashboard).
   - Endpoints principales.
   - Variables de entorno necesarias.
   - Decisiones técnicas (por qué elegiste tu stack y tu enfoque).
   - Limitaciones conocidas y qué mejorarías con más tiempo.
3. **Resumen breve de cómo usaste IA durante el desarrollo** (puede ir en el
   README o en un archivo aparte). Cuéntanos:
   - Qué herramientas usaste (ChatGPT, Claude, Cursor, OpenCode, Codex, etc.).
   - Para qué las usaste y qué validaste manualmente.
   - Si usaste configuraciones de agentes, prompts reutilizables o archivos
     como `AGENTS.md`, inclúyelos o descríbelos.

> Valoramos especialmente que uses IA **como herramienta de construcción**, no
> solo dentro del producto. Cuéntanos cómo te apoyaste en ella para entregar
> mejor y más rápido.

---

## Cómo lo vamos a revisar

A grandes rasgos nos fijaremos en:

- Que entiendas bien el problema y tomes decisiones razonables.
- Que la solución **funcione** y se pueda ejecutar siguiendo tu README.
- Tu criterio técnico al elegir y combinar tecnologías.
- Cómo trabajaste los datos (los datos no vienen limpios a propósito).
- Cómo aplicaste IA, tanto en el producto como en tu flujo de trabajo.
- Orden y claridad del código y la documentación.
- Manejo básico de errores.
- Simplicidad: preferimos algo simple y completo a algo complejo a medias.

No esperamos que implementes absolutamente todo a la perfección. Si tienes que
priorizar, hazlo y explícanos por qué en el README.

---

## Tiempo y entrega

- **Tiempo sugerido:** 1 día.
- **Entrega:** enlace al repositorio Git (público o con acceso). No hace falta
  video ni presentación.

Cualquier supuesto que necesites tomar, tómalo y déjalo documentado. ¡Éxitos!
