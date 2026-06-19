# Diccionario de datos — `tickets.csv`

Este archivo describe las columnas del dataset de tickets de soporte que vas a
analizar. El archivo es una **exportación de un sistema real de atención al
cliente**, por lo que algunos valores pueden venir incompletos o en formatos
distintos. Aquí se describe el **formato esperado/ideal** de cada campo.

| Columna | Descripción | Formato esperado |
|---|---|---|
| `Ticket ID` | Identificador del ticket. | Entero. Debería ser único por ticket. |
| `Customer Name` | Nombre del cliente que reporta. | Texto. |
| `Customer Email` | Correo de contacto del cliente. | Email válido en minúsculas. |
| `Customer Age` | Edad del cliente. | Entero (rango razonable, p. ej. 18–90). |
| `Customer Gender` | Género reportado por el cliente. | `Male` / `Female` / `Other`. |
| `Product Purchased` | Producto asociado al ticket. | Texto. |
| `Date of Purchase` | Fecha de compra del producto. | Fecha (idealmente `YYYY-MM-DD`). |
| `Ticket Type` | Tipo / motivo del ticket. | Categoría (p. ej. *Technical issue*, *Billing inquiry*, *Refund request*, *Cancellation request*, *Product inquiry*). |
| `Ticket Subject` | Asunto corto del ticket. | Texto. |
| `Ticket Description` | Descripción del problema escrita por el cliente. | Texto libre. |
| `Ticket Status` | Estado actual del ticket. | `Open` / `Pending Customer Response` / `Closed`. |
| `Ticket Priority` | Prioridad asignada. | Categoría ordinal: `Low` < `Medium` < `High` < `Critical`. |
| `Ticket Channel` | Canal por el que entró el ticket. | `Email` / `Phone` / `Chat` / `Social media`. |
| `First Response Time` | Marca de tiempo de la primera respuesta. | Fecha y hora. Puede estar vacío si aún no hay respuesta. |
| `Time to Resolution` | Marca de tiempo de resolución. | Fecha y hora. Normalmente solo presente en tickets cerrados. |
| `Customer Satisfaction Rating` | Calificación de satisfacción del cliente. | Número del 1 al 5. Normalmente solo presente en tickets cerrados. |

## Notas

- El dataset contiene cientos de tickets; es una muestra representativa, no el
  histórico completo.
- Los campos de tiempo (`First Response Time`, `Time to Resolution`) y la
  calificación de satisfacción suelen estar vacíos cuando el ticket todavía no
  está cerrado. Eso es esperable.
- Trabaja los datos como lo harías con cualquier fuente de producción: revisa,
  valida y normaliza lo que haga falta antes de alimentarlos a tu solución.

> Dataset base: *Customer Support Ticket Dataset* (Kaggle, `suraj520`),
> adaptado para este ejercicio.
