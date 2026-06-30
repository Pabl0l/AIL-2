# AIL — Manual del Paradigma
## Parte 1: El Modelo

---

> Este manual define un paradigma de software diseñado exclusivamente para ser operado por inteligencia artificial. Nada aquí existe por convención. Todo existe por necesidad computacional.

---

## § 1. El Axioma Central

**Software no es texto. Software es significado.**

El texto fuente es una representación del significado, optimizada para lectura humana. No es el significado en sí. Cuando una IA lee código, convierte texto → AST → semántica. Ese paso intermedio es desperdicio puro.

Este paradigma elimina el paso intermedio. El software existe directamente en su representación semántica.

**El axioma:** Todo sistema de software es un grafo semántico tipado donde los nodos son unidades de significado y los edges son relaciones tipadas entre ellos.

Todo lo que sigue es consecuencia de este axioma.

---

## § 2. El Nodo Semántico

El nodo semántico es la unidad atómica del paradigma.

**Reemplaza:** archivo, clase, función, módulo, componente, servicio, procedimiento, interfaz, tipo, constante.

**Definición:** Un nodo es la unidad más pequeña de significado coherente que no puede subdividirse sin perder ese significado.

### Estructura de un nodo

```
NODO {
  id:        [hash de contenido]         — identidad inmutable
  tipo:      [uno de 7 tipos]            — categoría semántica
  firma:     [inputs + outputs + efectos] — contrato de comportamiento
  conducta:  [IR binario]                — solo nodos computation
  meta: {
    embedding:  [vector semántico]       — para búsqueda por significado
    dominio:    [referencia a ontología] — contexto de negocio
    partición:  [referencia a partición] — contexto de despliegue
    aliases:    [lista de nombres]       — opcionales, nunca identidad
  }
}
```

### Los 7 tipos de nodo

| Tipo | Reemplaza | Contiene |
|---|---|---|
| `computation` | función, método, handler, procedimiento | comportamiento ejecutable (IR binario) |
| `data` | struct, DTO, entity, schema, record | definición de campos tipados, sin métodos |
| `constraint` | comentario de regla, aserción, invariante, validación | regla de negocio verificable |
| `event` | domain event, excepción, mensaje, notificación | ocurrencia tipada con payload |
| `test` | unit test, integration test, spec | especificación de comportamiento esperado |
| `boundary` | endpoint, API pública, puerto, interfaz externa | punto de cruce entre interior y exterior |
| `ontology` | documentación, concepto DDD, término de negocio | definición de concepto del dominio |

### Por qué no clases, no archivos, no módulos

Clases, archivos y módulos agrupan conceptos según criterios que el humano eligió: "cosas relacionadas con Usuario", "código que pertenece a este archivo", "exports de este módulo". Esas agrupaciones son ortogonales entre sí y forzar una jerarquía única introduce falsedad.

Un nodo puede pertenecer simultáneamente al dominio `pagos`, la partición de despliegue `order-service`, el contexto `write-path`, y ser parte de la capa `infraestructura` — sin contradicción, porque cada pertenencia es un edge de tipo diferente. Ninguna jerarquía es "la correcta".

---

## § 3. El Edge Tipado

El edge es la unidad atómica de relación.

**Reemplaza:** import, herencia, composición, llamada implícita, dependencia de módulo, convención de carpeta.

**Definición:** Un edge es una relación dirigida y tipada entre dos nodos. Sin edge explícito, no existe relación.

### Propiedades de todo edge

- **Dirigido:** A → B tiene semántica diferente a B → A
- **Tipado:** el tipo del edge define qué significa la relación
- **Explícito:** no existen dependencias por proximidad, nombre, posición o convención

### El catálogo de edges

| Tipo de edge | Dirección | Significa |
|---|---|---|
| `depends-on` | A → B | A requiere B para ejecutar correctamente |
| `composed-of` | A → B | A contiene un campo cuyo tipo es B |
| `constrained-by` | A → B | B es una regla que A debe cumplir |
| `tests` | A → B | A verifica el comportamiento de B |
| `produces` | A → B | A emite eventos del tipo B |
| `consumes` | A → B | A procesa eventos del tipo B |
| `dispatches-to` | A → B | A puede resolverse en tiempo de ejecución como B |
| `boundary-exposes` | A → B | A (boundary) expone B al exterior |
| `derives-from` | A → B | A es una versión modificada de B |
| `belongs-to` | A → B | A pertenece al dominio, partición o contexto B |

### Lo que no existe

No existen edges implícitos. No existen dependencias por herencia de clase. No existen dependencias por posición en el árbol de carpetas. No existen dependencias por convención de nombre.

Si A usa B y no hay edge `depends-on` de A a B: A no puede usar B. Esta es una invariante del sistema, no una preferencia.

---

## § 4. El Grafo Semántico

El sistema completo en cualquier punto del tiempo es un grafo de propiedad etiquetado (labeled property graph).

### Propiedades estructurales

**Sin jerarquía impuesta.** Un nodo puede relacionarse con N otros nodos por N tipos de edge distintos, sin necesidad de un padre único. La pertenencia múltiple es natural, no un caso especial.

**Content-addressed.** La identidad de todo nodo es función de su contenido. Cambiar el contenido produce un nuevo nodo con nueva identidad. El nodo original no desaparece — persiste hasta que ningún edge lo referencie.

**Inmutable.** Los nodos no se modifican in-place. Se crean versiones nuevas. El grafo crece, nunca muta retroactivamente.

**Versionado.** El grafo completo tiene snapshots: estados consistentes e inmutables. El historial del sistema es una cadena de snapshots. Cualquier estado anterior es restaurable.

**Consultable.** Cualquier pregunta sobre el sistema es una consulta de grafo: ¿qué reglas aplican a este nodo? ¿qué nodos dependen de este? ¿qué cambió entre versión A y B? ¿qué nodos implementan esta firma? Todo es consulta, nada es grep sobre texto.

### Tabla de correspondencia: paradigma actual → grafo semántico

| Concepto actual | Equivalente en el grafo |
|---|---|
| Estructura de carpetas | edges `belongs-to` + etiquetas de partición |
| Módulos / paquetes | particiones del grafo (subgrafos con nodos boundary) |
| Interfaces / contratos | constraints de tipo en edges `depends-on` |
| Herencia de clase | edges `dispatches-to` + nodos con firmas compatibles |
| Inyección de dependencias | edges `depends-on` explícitos + composición de grafo |
| Patrones de diseño (Factory, Strategy, etc.) | propiedades estructurales del grafo |
| Base de código completa | el grafo en su snapshot actual |
| Repositorio Git | cadena de snapshots del grafo con deltas semánticos |
| Documentación de API | generada automáticamente desde nodos boundary |
| Reglas de negocio | nodos constraint con edges constrained-by |
| Pruebas | nodos test con edges tests |
| Errores | nodos event subtipo error |

---

## § 5. Particiones y Boundaries

Un sistema real tiene múltiples contextos: dominios de negocio, unidades de despliegue, contextos de ejecución. Las **particiones** modelan esto sin imponer jerarquía.

### Qué es una partición

Una partición es un subgrafo etiquetado. Sus nodos tienen edges `belongs-to` a un nodo de partición. No es un concepto de archivo ni de carpeta — es una propiedad del nodo.

Un nodo puede pertenecer a múltiples particiones simultáneamente:
- Partición de dominio: `dominio:inventario`
- Partición de despliegue: `servicio:inventory-service`
- Partición de ejecución: `path:write-path`

### Nodos boundary

Un nodo `boundary` es el único punto por donde el tráfico entre particiones puede fluir. Si A (en partición P1) necesita usar B (en partición P2), A depende del nodo `boundary` de P2 que expone B — no de B directamente.

La violación de esta regla (edge `depends-on` que cruza partición sin pasar por boundary) es un error de compilación del grafo.

### Qué reemplaza

| Actual | En particiones |
|---|---|
| Bounded Context (DDD) | partición de dominio |
| Microservicio | partición de despliegue con boundary nodes |
| Módulo con exports privados | partición con boundary nodes para lo público |
| Capa (domain / application / infrastructure) | partición de arquitectura |

La diferencia clave: en el paradigma actual, los límites son convenciones de carpeta que nadie puede verificar automáticamente. En este paradigma, los límites son edges y particiones que el compilador del grafo verifica en cada snapshot.

---

## § 6. El Ciclo de Vida de un Nodo

### Nacimiento

Un nodo existe desde el momento en que es creado y agregado al grafo con sus edges requeridos. Requiere:
- Tipo válido
- Firma completa
- Al menos un edge de contexto (`belongs-to` a alguna partición u ontología)
- Para nodos `computation`: conducta IR válida

### Existencia

Un nodo existe mientras al menos un edge activo lo referencie, o mientras sea parte del snapshot actual.

### Modificación

Los nodos no se modifican. Se crea un nuevo nodo que `derives-from` el anterior. El nuevo nodo tiene una nueva ID. Los nodos que dependían del anterior deben declarar explícitamente si adoptan la nueva versión o mantienen la anterior.

### Eliminación

Un nodo se elimina cuando ningún edge del snapshot actual lo referencia. La eliminación es siempre consecuencia de actualizar los edges que lo apuntaban, no un acto directo sobre el nodo.

---

## Resumen del Modelo

El modelo completo tiene exactamente cuatro primitivas:

1. **Nodo** — unidad atómica de significado
2. **Edge** — unidad atómica de relación
3. **Grafo** — el sistema completo como conjunto de nodos y edges
4. **Snapshot** — estado consistente del grafo en un punto del tiempo

Todo lo demás — arquitecturas, patrones, principios, convenciones — es consecuencia de estas cuatro primitivas operando bajo las reglas del paradigma.
